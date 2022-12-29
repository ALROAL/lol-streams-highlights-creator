import argparse
import json
from src import download_videos_from_twitch, extract_streamer_videos_information, get_raw_game_videos_from_streamer, \
    create_highlights_video, video_selector, upload_video_to_youtube
from src.paths import *

if __name__ == "__main__":

    CHAMPIONS_IMAGES_PATH.mkdir(parents=True, exist_ok=True)
    THUMBNAIL_IMAGES_PATH.mkdir(parents=True, exist_ok=True)
    JSON_PATH.mkdir(parents=True, exist_ok=True)
    STREAMS_PATH.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser()

    parser.add_argument("--create_videos", choices=["True", "False"], help="General option to download, extract information and create highlight videos",
                        nargs='?', default="True")
    parser.add_argument("--upload_videos", choices=["True", "False"], help="Option to upload already existing videos to YouTube",
                        nargs='?', default="False")
    parser.add_argument("--download_streams", choices=["True", "False"], help="Option to download new streams from Twitch ",
                        nargs='?', default="True")
    parser.add_argument("--prev_days", type=int, help="Previous days to look for stream videos in Twitch",
                        nargs='?', default=2)
    parser.add_argument("--extract_information", choices=["True", "False"], help="Option to extract information from stream videos",
                        nargs='?', default="True")
    parser.add_argument("--extract_raw_game_videos", choices=["True", "False"], help="Option to extract raw game videos from stream videos",
                        nargs='?', default="False")
    parser.add_argument("--create_highlights_videos", choices=["True", "False"], help="Option to create highlight videos from raw game videos",
                        nargs='?', default="True")
    parser.add_argument("--use_thumbnail", choices=["True", "False"], help="Option to generate and use thumbnail for YouTue video",
                        nargs='?', default="True")
    parser.add_argument("--add_video_intro", choices=["True", "False"], help="Option to add default intro video. To add a custom intro video, replace `./templates/intro.mp4`",
                        nargs='?', default="True")
    parser.add_argument("--add_video_outro", choices=["True", "False"], help="Option to add default outro video. To add a custom outro video, replace `./templates/outro.mp4`",
                        nargs='?', default="True")
    parser.add_argument("--n_videos", type=int, help="Number of videos to upload to YouTube",
                        nargs='?', default=3)

    args = parser.parse_args()
    argv = vars(args)

    print("START")

    try:
        with open(STREAMERS_PATH) as f:
            STREAMERS = [tuple(x) for x in json.load(f)]
    except:
        print("Missing file STREAMERS.json")

    if argv["create_videos"]=="True":
        for streamer, region in STREAMERS:
            if argv["download_streams"]=="True":
                download_videos_from_twitch(streamer, argv["prev_days"])
            if argv["extract_information"]=="True":
                extract_streamer_videos_information(streamer, region, argv["prev_days"])
            if argv["extract_raw_game_videos"]=="True":
                get_raw_game_videos_from_streamer(streamer)
            if argv["create_highlights_videos"]=="True":
                create_highlights_video(streamer, argv["add_video_intro"], argv["add_video_outro"])

    if argv["upload_videos"]=="True":
        selected_videos = video_selector(argv["n_videos"])
        for video_path in selected_videos:
            upload_video_to_youtube(video_path, argv["use_thumbnail"])

    print("END")