import pandas as pd
import re
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from youtube_upload.client import YoutubeUploader
from src.paths import EDITED_VIDEOS_INFO_PATH, TOKEN_PICKLE_PATH, CLIENT_SECRETS_PATH
from src.video_generation import generate_thumbnail


def video_selector(n_videos):
    edited_videos_info = pd.read_excel(EDITED_VIDEOS_INFO_PATH)
    edited_videos_info = edited_videos_info[~edited_videos_info["published"]]
    edited_videos_info.sort_values(by=["score", "date", "duration"], ascending=[False, False, True], inplace=True)
    selected_videos = edited_videos_info.iloc[0:n_videos]["video_path"].values.tolist()
    print(f"Selected {len(selected_videos)} videos to upload.")
    return selected_videos


def upload_video_to_youtube(video_path, use_thumbnail=True):

    # token.pickle stores the user's credentials from previously successful logins
    if os.path.exists(TOKEN_PICKLE_PATH):
        print('Loading Credentials From File...')
        with open(TOKEN_PICKLE_PATH, 'rb') as token:
            credentials = pickle.load(token)
    else:
        credentials = None
        print('No credentials found')

# If there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        try:
            if credentials.expired and credentials.refresh_token:
                print('Refreshing Access Token...')
                credentials.refresh(Request())
        except:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_PATH,
                scopes=[
                    'https://www.googleapis.com/auth/youtube.upload'
                ]
            )
            flow.run_local_server(host="localhost", bind_addr="0.0.0.0", port=8080)
            credentials = flow.credentials

            # Save the credentials for the next run
            with open(TOKEN_PICKLE_PATH, 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)

    uploader = YoutubeUploader(client_id=credentials.client_id, client_secret=credentials.client_secret)
    uploader.authenticate(access_token=credentials.token, refresh_token=credentials.refresh_token)

    edited_videos_info = pd.read_excel(EDITED_VIDEOS_INFO_PATH)
    video_info = edited_videos_info[edited_videos_info["video_path"]==video_path]
    title, description, thumbnail_path = video_info[["title", "description", "thumbnail_path"]].values[0]
    if use_thumbnail:
        generate_thumbnail(video_path)
    tags = [tag[1:] for tag in re.findall("#\w*", description) if len(tag)>1]
    # Video options
    options = {
        "title" : title, # The video title
        "description" : description, # The video description
        "tags" : tags,
        "categoryId" : "22",
        "privacyStatus" : "private", # Video privacy. Can either be "public", "private", or "unlisted"
        "kids" : False, # Specifies if the Video if for kids or not. Defaults to False.
        "thumbnailLink" : thumbnail_path if use_thumbnail else None # Optional. Specifies video thumbnail.
    }

    # upload video
    uploader.upload(video_path, options)

    edited_videos_info.loc[edited_videos_info["video_path"] == video_path, ["published"]] = True
    edited_videos_info.to_excel(EDITED_VIDEOS_INFO_PATH, index=False)

    print(f"Video {video_path} uploaded")