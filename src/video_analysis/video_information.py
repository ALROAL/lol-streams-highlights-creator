import numpy as np
import textdistance
import cv2
import json
import matplotlib.pyplot as plt
from src.riot_api.utils import *
import pytesseract as tes
import os
import datetime
import re
from src.paths import JSON_PATH, STREAMS_PATH, STREAMERS_SUMMONERS_NAMES_JSON_PATH, TAB_TEMPLATE, STREAMER_SUMMONER_NAME_INDICATOR_TEMPLATE

def extract_streamer_videos_information(streamer, region, prev_days):

    streams = STREAMS_PATH / streamer
    try:
        streams.exists()
    except:
        print(f"No video stream found for {streamer}")
    for stream in os.listdir(streams):
        stream_times_json_path = streams / stream / ("stream_times" + ".json")
        video_info_json_path = streams / stream / (stream + ".json")
        stream_video_path = streams / stream / (stream + ".mp4")
        if (stream_video_path.exists()) & (not video_info_json_path.exists()):
            file_path_list = [(streams / stream / file).as_posix() for file in os.listdir(streams / stream)]
            print(f"Start of stream {streamer}-{stream} information extraction")
            start_information_extraction = datetime.datetime.now().timestamp()

            template = cv2.imread(str(TAB_TEMPLATE))
            template = cv2.resize(template, (1144, 393))
            video_info = {}

            vidcap = cv2.VideoCapture(stream_video_path.as_posix())

            n_game = 1
            skip_frames = 0

            game_images_path_dict = {int(im_path.split("_")[-5]): im_path for im_path in file_path_list if re.match(".*game_[0-9]*_frame_[0-9]*_score_[0-9.]*.png", im_path)}
            game_images_frame_dict = {int(im_path.split("_")[-5]): int(im_path.split("_")[-3]) for im_path in file_path_list if re.match(".*game_[0-9]*_frame_[0-9]*_score_[0-9.]*.png", im_path)}

            with open(stream_times_json_path, "r", encoding='utf-8') as file:
                stream_times = json.load(file)
            
            waiting_time = datetime.datetime.now().timestamp()
            for stream_time in stream_times:
                
                if stream_time[0] == 0:
                    vidcap.set(cv2.CAP_PROP_POS_FRAMES, (10*60)*vidcap.get(cv2.CAP_PROP_FPS))
                else:
                    vidcap.set(cv2.CAP_PROP_POS_FRAMES, int(stream_time[0]*vidcap.get(cv2.CAP_PROP_FPS)))
                success, image = vidcap.read()
                while success:
                    try:
                        image = cv2.imread(game_images_path_dict[n_game])
                        current_frame = game_images_frame_dict[n_game]
                        vidcap.set(cv2.CAP_PROP_POS_FRAMES, int(current_frame))
                        skip_frames = 100
                    except:
                        pass

                    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                    if max_val > 0.4:
                        if skip_frames == 0:
                            time_seconds = get_game_time(image)
                            if time_seconds < 7:
                                current_frame = vidcap.get(cv2.CAP_PROP_POS_FRAMES)
                                vidcap.set(cv2.CAP_PROP_POS_FRAMES, int(current_frame + (8-time_seconds)*vidcap.get(cv2.CAP_PROP_FPS)))

                        skip_frames += 1
                        if skip_frames >= 15:
                            skip_frames = 0
                            current_frame = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
                            print(f"Found frame {current_frame} with score {round(max_val, 3)} for game {n_game}")

                            image_filename = str(streams / stream / f"game_{n_game}_frame_{current_frame}_score_{round(max_val, 3)}.png")
                            cv2.imwrite(image_filename, image)

                            image_tab_cut = image[max_loc[1]:max_loc[1] + template.shape[0],
                                            max_loc[0]:max_loc[0] + template.shape[1], :]

                            game_start_seconds = get_game_start_seconds(image, vidcap)
                            if game_start_seconds < 0:
                                print("Game start not shown in video")
                            summoner_names_from_image, streamer_summoner_name = get_summoner_names_from_image(image_tab_cut)

                            try:
                                with open(STREAMERS_SUMMONERS_NAMES_JSON_PATH, "r", encoding='utf-8') as file:
                                    streamers_summoner_names = json.load(file)
                                if streamer not in streamers_summoner_names.keys():
                                    print(f"Found new streamer ({streamer}) with summnoner name ({streamer_summoner_name})")
                                    streamers_summoner_names[streamer] = [streamer_summoner_name]
                                else:
                                    for streamer_known_summoner_name in streamers_summoner_names[streamer]:
                                        score = textdistance.hamming.normalized_similarity(streamer_summoner_name, streamer_known_summoner_name)
                                        if score > 0.9:
                                            streamer_summoner_name = streamer_known_summoner_name
                                            break
                                    if streamer_summoner_name not in streamers_summoner_names[streamer]:
                                        streamers_summoner_names[streamer] += [streamer_summoner_name]
                                        print(f"Found new summnoner name ({streamer_summoner_name}) for streamer ({streamer})")
                                
                                with open(STREAMERS_SUMMONERS_NAMES_JSON_PATH, 'w', encoding='utf-8') as f:
                                    json.dump(streamers_summoner_names, f, ensure_ascii=False, indent=4)
                            except:
                                
                                streamers_summoner_names = {streamer: [streamer_summoner_name]}
                                with open(STREAMERS_SUMMONERS_NAMES_JSON_PATH, 'w', encoding='utf-8') as f:
                                    json.dump(streamers_summoner_names, f, ensure_ascii=False, indent=4)
                                print(f"Creation of JSON file to store streamers and their corresponding summoner names")
                                print(f"Found new summnoner name ({streamer_summoner_name}) for streamer ({streamer})")


                            extract_games_json_by_username(streamer_summoner_name, region, prev_days)

                            json_file, match_data = find_match_by_summoner_names(streamer, streamer_summoner_name, summoner_names_from_image)

                            if match_data is not None:
                                game_duration_in_seconds = int(match_data["info"]["frames"][-1]["events"][-1]["timestamp"] / 1000) + 1
                                game_end_seconds = game_start_seconds + game_duration_in_seconds

                                video_info["game_" + str(n_game)] = {"summoner_name": streamer_summoner_name,
                                                                    "start": game_start_seconds,
                                                                    "end": game_end_seconds,
                                                                    "duration": game_duration_in_seconds,
                                                                    "json_file": (JSON_PATH / streamer / streamer_summoner_name / json_file).as_posix()}
                                vidcap.set(cv2.CAP_PROP_POS_FRAMES, int((game_end_seconds + 8*60) * vidcap.get(cv2.CAP_PROP_FPS)))
                                print(f"Created video info for game {n_game} of stream {streamer}-{stream}")
                                waiting_time_seconds = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES) / vidcap.get(cv2.CAP_PROP_FPS))


                            else:
                                print(f"No match data found for game {n_game} of stream {streamer}-{stream}")
                                vidcap.set(cv2.CAP_PROP_POS_FRAMES, int((40*60) * vidcap.get(cv2.CAP_PROP_FPS)))
                            
                            n_game += 1
                    
                    else:
                        skip_frames=0

                    success, image = vidcap.read()
                    current_time_seconds = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES) / vidcap.get(cv2.CAP_PROP_FPS))
                    if current_time_seconds > stream_time[1]:
                        success = False
                    if current_time_seconds - waiting_time > 45*60:
                        success = False
                        print(f"No game found for the past 45 mins. Stopping information extraction.")

                with open(video_info_json_path.as_posix(), 'w', encoding='utf-8') as outfile:
                    json.dump(video_info, outfile)

                spent_time_information_extraction = datetime.datetime.now().timestamp() - start_information_extraction
                spent_time_information_extraction = str(datetime.timedelta(seconds=spent_time_information_extraction))
                print(f"End of  stream {streamer}-{stream} information extraction. Total time: {spent_time_information_extraction}")
            
        else:
            print(f"{streamer}-{stream} information was already extracted")

def get_summoner_names_from_image(image_tab_cut):
    template_2 = cv2.imread(STREAMER_SUMMONER_NAME_INDICATOR_TEMPLATE.as_posix())
    template_2 = cv2.resize(template_2, (35, 70))
    result = cv2.matchTemplate(image_tab_cut, template_2, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    streamer_i = max_loc[1] // 70
    streamer_j = max_loc[0] // 400

    summoner_names_from_image = set()
    for j in range(2):
        for i in range(5):
            im_summoner_name = image_tab_cut[5 + 76 * i:37 + 76 * i, 310 + 570 * j:450 + 570 * j, :]
            im_summoner_name = cv2.resize(im_summoner_name, (256, 64))
            #Convert an image from BGR to grayscale mode 
            gray_image = cv2.cvtColor(im_summoner_name, cv2.COLOR_BGR2GRAY)
            gray_image = cv2.bitwise_not(gray_image)
            
            #Convert a grayscale image to black and white using binary thresholding 
            _, BnW_image = cv2.threshold(gray_image, 160, 180, cv2.THRESH_BINARY)

            summoner_name = tes.image_to_string(BnW_image)
            summoner_name = summoner_name.replace("\n", "").strip()

            summoner_names_from_image.add(summoner_name)

            if (streamer_i == i) and (streamer_j == j):
                streamer_summoner_name = summoner_name

    return summoner_names_from_image, streamer_summoner_name

def get_game_start_seconds(image, vidcap):
    time_lol_seconds = get_game_time(image)
    game_start_seconds = vidcap.get(cv2.CAP_PROP_POS_FRAMES) / vidcap.get(cv2.CAP_PROP_FPS) - time_lol_seconds
    return game_start_seconds

def get_game_time(image):

    image_lol_time = image[0:30, 1855:1915, :]
    image_lol_time = cv2.resize(image_lol_time, (120, 60))
    raw_time_lol = tes.image_to_string(image_lol_time)[:-1]
    time_lol_seconds = sum(x * int(t) for x, t in zip([60, 1], raw_time_lol.split(":")))

    return time_lol_seconds

def find_match_by_summoner_names(streamer, streamer_summoner_name, summoner_names_from_image):
    match_found = False
    print("Start of Find match data")
    start = datetime.datetime.now().timestamp()

    json_filepath = JSON_PATH / streamer / streamer_summoner_name
    for json_file in os.listdir(json_filepath):
        with open(json_filepath / json_file, "r", encoding='utf-8') as file:
            match_data = json.load(file)

        summoner_names_from_json = match_data["metadata"]["participants"]

        total_score = 0
        for name_from_json in summoner_names_from_json:
            highest_score = 0
            for name_from_video in summoner_names_from_image:
                score = textdistance.levenshtein.normalized_similarity(name_from_json, name_from_video)
                if score >= highest_score:
                    highest_score = score
                    final_score = score
            total_score += final_score

        if total_score > 7.5:
            time_spent = datetime.datetime.now().timestamp() - start
            print(f"Match data {json_file} found in {round(time_spent, 3)} seconds")
            match_found = True
            break

    if match_found:
        print("End of Find match data")
        return json_file, match_data
    else:
        print("End of Find match data")
        return None, None
