import os
from pathlib import Path
import json
import moviepy.editor as mp
import numpy as np
from datetime import datetime
import pandas as pd
import difflib
from moviepy.video.io.VideoFileClip import VideoFileClip
from .thumbnail_generation import get_champions_list_from_wiki
from src.riot_api import get_game_metadata_by_matchid
from src.paths import STREAMS_PATH, INTRO_VIDEO_PATH, OUTRO_VIDEO_PATH, EDITED_VIDEOS_INFO_PATH, THUMBNAIL_IMAGES_PATH

def create_highlights_video(streamer, add_intro_video="True", add_outro_video="True", sound_correction=True):

    streams = STREAMS_PATH / streamer
    for stream in os.listdir(streams):
        video_info_json_path = streams / stream / (stream + ".json")
        stream_video_path = streams / stream / (stream + ".mp4")
        if (stream_video_path.exists()) & (video_info_json_path.exists()):
            print(f"Start of Higlight videos creation for {streamer}-{stream}")
            with open(video_info_json_path.as_posix()) as file:
                stream_info = json.load(file)

            for game, stream_game_data in stream_info.items():

                edited_game_video_path = Path(f"{stream_video_path.parent}/{stream_video_path.stem}_{game}_edited{stream_video_path.suffix}")
                if (not edited_game_video_path.exists()):
                    streamer_summoner_name = stream_game_data["summoner_name"]

                    with open(stream_game_data["json_file"], encoding="utf-8") as file:
                        game_data = json.load(file)

                    match_id = game_data["metadata"]["matchId"]
                    streamer_id = get_streamer_id(game_data, streamer_summoner_name)
                    game_score = compute_game_score(match_id, streamer_id)

                    if game_score >= 0.5:
                        interesting_events = get_game_highlights(game_data, streamer_id)
                        game_video_path = Path(f"{stream_video_path.parent}/{stream_video_path.stem}_{game}{stream_video_path.suffix}")
                        raw_game_video = get_raw_game_video(stream_video_path, game_video_path, game, stream_game_data)
                        game_video_path = game_video_path.as_posix()
                        time_intervals = get_time_intervals(interesting_events, game_video_path, raw_game_video, sound_correction)
                        create_video(time_intervals, game_video_path, raw_game_video, add_intro_video, add_outro_video)
                        create_videos_info(game_video_path, streamer, streamer_id, match_id, game_score)
                        print(f"Created highlight video for game {game}")
                    else:
                        print(f"{game} has not enough highlights to create video")

                else:
                    print(f"{game} highlights video was already created")

            print(f"End of Higlight videos creation for {streamer}-{stream}")


def get_raw_game_video(stream_video_path, game_video_path, game, data):
    if game_video_path.exists():
        raw_game_video = mp.VideoFileClip(game_video_path.as_posix())
    else:
        if data["duration"] > 14*60:
            start_time = data["start"] - 60
            end_time = data["end"] + 60
            video = mp.VideoFileClip(stream_video_path.as_posix())
            raw_game_video = video.subclip(start_time, end_time)
        else:
            print(f"Raw {game} video duration not long enough (<14 mins) to create video")

    return raw_game_video

def create_videos_info(game_video_path, streamer, streamer_id, match_id, score):

    try:
        edited_videos_info = pd.read_excel(EDITED_VIDEOS_INFO_PATH)
    except:
        edited_videos_info = pd.DataFrame(columns=["video_path", "duration", "streamer", "played_champion", "played_position",
         "date", "score", "title", "description", "thumbnail_path", "published"])

    lol_positions = {"TOP": "TOP", "JUNGLE": "JUNGLE", "MIDDLE": "MID", "BOTTOM": "ADC", "UTILITY": "SUPPORT"}
    champ_list = get_champions_list_from_wiki()

    game_metadata = get_game_metadata_by_matchid(match_id)
    streamer_stats = game_metadata["info"]["participants"][streamer_id-1]
    for i, player_stats in enumerate(game_metadata["info"]["participants"]):
        if i != streamer_id-1:
            if player_stats["teamPosition"] == streamer_stats["teamPosition"]:
                enemy_champion = difflib.get_close_matches(player_stats["championName"], champ_list)[0]

    stream_date = datetime.fromtimestamp(game_metadata["info"]["gameCreation"]/1000)
    position = lol_positions[streamer_stats["teamPosition"]]
    champion_name = streamer_stats["championName"]
    if champion_name == "MonkeyKing":
        champion_name = "Wukong"
    champion_name = difflib.get_close_matches(champion_name, champ_list)[0]
    title = champion_name + " " + position + " vs " + enemy_champion + " ft." + \
            streamer + " | Stream Highlights [" + stream_date.strftime("%d/%m/%Y") + "]"

    description = "League of Legends gameplay highlights from {} stream on {}. \n \n \n \n \n #LeagueOfLegends #{} #{}"\
        .format(streamer, stream_date.strftime("%d/%m/%Y"), streamer, streamer_stats["championName"])

    game_metadata = get_game_metadata_by_matchid(match_id)
    stream_date = datetime.fromtimestamp(game_metadata["info"]["gameCreation"] / 1000)
    edited_game_video_path = game_video_path[:-4] + "_edited.mp4"
    video = mp.VideoFileClip(edited_game_video_path)
    duration = video.duration / 60
    thumbnail_image_path = THUMBNAIL_IMAGES_PATH.as_posix() + "/{}_{}_{}.png".format(streamer, title.split(" ft.")[0],
                                                                          stream_date.strftime("%d-%m-%Y"))

    video_info = {"video_path": edited_game_video_path, "duration": duration, "streamer": streamer,
                  "played_champion": champion_name, "played_position": position, "date":stream_date, "score": score, "title": title,
                  "description": description, "thumbnail_path": thumbnail_image_path, "published": False}

    edited_videos_info = edited_videos_info.append(video_info, ignore_index=True)
    edited_videos_info.to_excel(EDITED_VIDEOS_INFO_PATH, index=False)


def compute_game_score(match_id, streamer_id):
    game_metadata = get_game_metadata_by_matchid(match_id)
    streamer_stats = game_metadata["info"]["participants"][streamer_id-1]
    score = 0
    if (game_metadata["info"]["gameDuration"] < 12*60) or (streamer_stats["teamPosition"] == "JUNGLE"):
        return score
    if streamer_stats["win"]:
        score += 0.20
    score += streamer_stats["kills"]*0.025 + streamer_stats["assists"]*0.01 + streamer_stats["doubleKills"]*0.01 + \
             streamer_stats["tripleKills"]*0.0625 + streamer_stats["quadraKills"]*0.125 + streamer_stats["pentaKills"]*0.25

    return score

def get_streamer_id(game_data, streamer_summoner_name):
    streamer_id = game_data["metadata"]["participants"].index(streamer_summoner_name) + 1
    return streamer_id

def get_game_highlights(game_data, streamer_id):
    interesting_event_types = ["PAUSE_END", "CHAMPION_KILL", "CHAMPION_SPECIAL_KILL", "TURRET_PLATE_DESTROYED",
                               "BUILDING_KILL", "ELITE_MONSTER_KILL", "DRAGON_SOUL_GIVEN", "GAME_END"]
    interesting_events = []
    for time_frame in game_data["info"]["frames"]:
        for event in time_frame["events"]:
            if event["type"] in interesting_event_types:
                interesting_events.append(event)
    interesting_events_for_highlights = []
    for event in interesting_events:

        event_timestamp = int(event["timestamp"] / 1000 + 60)

        if event["type"] == "PAUSE_END":
            interesting_events_for_highlights.append(["GAME_START", event_timestamp])
        if event["type"] == "CHAMPION_KILL":
            if event["killerId"] == streamer_id:
                interesting_events_for_highlights.append(["KILL", event_timestamp])
            if event["victimId"] == streamer_id:
                interesting_events_for_highlights.append(["DEATH", event_timestamp])
            try:
                if streamer_id in event["assistingParticipantIds"]:
                    interesting_events_for_highlights.append(["ASSIST", event_timestamp])
            except:
                pass
        if event["type"] == "CHAMPION_SPECIAL_KILL":
            if event["killerId"] == streamer_id:
                interesting_events_for_highlights.append(["SPECIAL_KILL", event_timestamp])

        if event["type"] == "BUILDING_KILL":
            if event["killerId"] == streamer_id:
                if event["buildingType"] == 'INHIBITOR_BUILDING':
                    event_name = "BUILDING_" + "INHIBITOR_" + event["laneType"]
                    interesting_events_for_highlights.append([event_name, event_timestamp])
                if event["buildingType"] == 'TOWER_BUILDING':
                    event_name = "BUILDING_" + event["towerType"] + "_" + event["laneType"]
                    interesting_events_for_highlights.append([event_name, event_timestamp])

            try:
                if streamer_id in event["assistingParticipantIds"]:
                    if event["buildingType"] == 'INHIBITOR_BUILDING':
                        event_name = "BUILDING_" + "INHIBITOR_" + event["laneType"]
                        interesting_events_for_highlights.append([event_name, event_timestamp])
                    if event["buildingType"] == 'TOWER_BUILDING':
                        event_name = "BUILDING_" + event["towerType"] + "_" + event["laneType"]
                        interesting_events_for_highlights.append([event_name, event_timestamp])
            except:
                pass

        if event["type"] == "ELITE_MONSTER_KILL":
            if event["killerId"] == streamer_id:
                interesting_events_for_highlights.append([event["monsterType"], event_timestamp])

            try:
                if streamer_id in event["assistingParticipantIds"]:
                    interesting_events_for_highlights.append([event["monsterType"], event_timestamp])
            except:
                pass

        if event["type"] == "GAME_END":
            interesting_events_for_highlights.append(["GAME_END", event_timestamp])

    return interesting_events_for_highlights

def get_time_intervals(interesting_events, game_video_path, raw_game_video, sound_correction=True):

    time_intervals = []
    for event, timestamp in interesting_events:
        if event == "GAME_START":
            interval = [timestamp - 5, timestamp + 10]
            time_intervals.append(interval)
        if event in ["KILL", "DEATH", "ASSIST"]:
            interval = [timestamp - 20, timestamp + 10]
            time_intervals.append(interval)
        if "BUILDING" in event:
            interval = [timestamp - 15, timestamp + 10]
            time_intervals.append(interval)
        if event == "ELITE_MONSTER_KILL":
            interval = [timestamp - 20, timestamp + 10]
            time_intervals.append(interval)
        if event == "GAME_END":
            interval = [timestamp - 20, timestamp + 25]
            time_intervals.append(interval)
    merged_time_intervals = []
    prevList = time_intervals[0]
    for lists in time_intervals[1:]:
        if lists[0] <= prevList[1] + 1:
            prevList = [prevList[0], lists[1]]
        else:
            merged_time_intervals.append(prevList)
            prevList = lists
    merged_time_intervals.append(prevList)

    if sound_correction:
        merged_time_intervals_sound_correction = []
        for start_seconds, end_seconds in merged_time_intervals:
            # crop a video clip and add it to list
            c = raw_game_video.subclip(start_seconds, end_seconds)

            audio_array = c.audio.to_soundarray()
            mono_audio_array = np.mean(audio_array, axis=1)

            sound_end = mono_audio_array[-44100:].max()
            sound_start = mono_audio_array[:44100].max()
            while (sound_end > 0.04) & (end_seconds < raw_game_video.duration-1):
                end_seconds += 1
                c = raw_game_video.subclip(start_seconds, end_seconds)
                audio_array = c.audio.to_soundarray()
                mono_audio_array = np.mean(audio_array, axis=1)
                sound_end = mono_audio_array[-44100:].max()
            while (sound_start > 0.04) & (start_seconds > 1):
                start_seconds -= 1
                c = raw_game_video.subclip(start_seconds, end_seconds)
                audio_array = c.audio.to_soundarray()
                mono_audio_array = np.mean(audio_array, axis=1)
                sound_start = mono_audio_array[:44100].max()

            merged_time_intervals_sound_correction.append([start_seconds, end_seconds])

        final_merged_time_intervals = []
        prevList = merged_time_intervals_sound_correction[0]
        for lists in merged_time_intervals_sound_correction[1:]:
            if lists[0] <= prevList[1] + 1:
                prevList = [prevList[0], lists[1]]
            else:
                final_merged_time_intervals.append(prevList)
                prevList = lists
        final_merged_time_intervals.append(prevList)

        return final_merged_time_intervals
    else:
        return merged_time_intervals

def create_video(time_intervals, game_video_path, raw_game_video, add_intro_video, add_outro_video):
    
    clips = []  # list of all video fragments
    if (INTRO_VIDEO_PATH.exists()) & (add_intro_video=="True"):
        intro_video = mp.VideoFileClip(INTRO_VIDEO_PATH.as_posix())
        clips.append(intro_video)
    for start_seconds, end_seconds in time_intervals:
        # crop a video clip and add it to list
        c = raw_game_video.subclip(start_seconds, end_seconds)
        c = c.crossfadein(1)
        clips.append(c)
    if (OUTRO_VIDEO_PATH.exists()) & ((add_outro_video=="True")):
        outro_video = mp.VideoFileClip(OUTRO_VIDEO_PATH.as_posix())
        clips.append(outro_video)

    final_clip = mp.concatenate_videoclips(clips)
    edited_game_video_path = game_video_path[:-4] + "_edited.mp4"
    final_clip.write_videofile(edited_game_video_path)
    final_clip.close()

