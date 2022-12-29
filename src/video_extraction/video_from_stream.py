from moviepy.video.io.VideoFileClip import VideoFileClip
from src.paths import STREAMS_PATH
import json
import os
import datetime
from pathlib import Path

def get_raw_game_videos_from_streamer(streamer):
    streams = STREAMS_PATH / streamer
    for stream in os.listdir(streams):
        stream_video_path = streams / stream / (stream + ".mp4")
        video_data_json = streams / stream / (stream + ".json")

        if (stream_video_path.exists()) & (video_data_json.exists()):
            print(f"Start of Raw game videos extraction from {streamer}-{stream}")
            start_raw_videos_extraction = datetime.datetime.now().timestamp()

            get_videos_from_stream(stream_video_path, video_data_json)

            spent_time_raw_videos_extraction = datetime.datetime.now().timestamp() - start_raw_videos_extraction
            spent_time_raw_videos_extraction = str(datetime.timedelta(seconds=spent_time_raw_videos_extraction))
            print(f"End of Raw game videos extraction from {streamer}-{stream}. Total time: {spent_time_raw_videos_extraction}")

def get_videos_from_stream(stream_video_path, video_data_json):
    with open(video_data_json.as_posix(), "r", encoding='utf-8') as file:
        video_data = json.load(file)
    for game, data in video_data.items():
        if data["duration"] > 14*60:
            output_video_path = Path(f"{stream_video_path.parent}/{stream_video_path.stem}_{game}{stream_video_path.suffix}")
            if not Path(output_video_path).exists():
                print(f"Start of Raw {game} video extraction")
                start_time = data["start"] - 60
                end_time = data["end"] + 60
                with VideoFileClip(stream_video_path.as_posix()) as video:
                    new = video.subclip(start_time, end_time)
                    new.write_videofile(output_video_path.as_posix(), audio_codec='aac')
                print(f"End of Raw {game} video extraction")
            else:
                print(f"Raw {game} video was already extracted")

        else:
            print(f"{game} duration not long enough (<14 mins) to create video")
