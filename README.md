League of Legends Twitch streams highlights creator
==============================

<img src="https://imgur.com/zWuos61" width="1024" height="512">

Download League of Legends Twitch streams and process the raw stream video to create gameplay highlights videos. Optionally, automatically upload them to YouTube.

- [Quick start](#quick-start)
- [Description](#description)
- [Usage](#results)
- [Results](#report)

## Quick start

1. Install dependencies
```bash
pip install -r requirements.txt
```
2. Install Tesseract-OCR following the [installation guide](https://tesseract-ocr.github.io/tessdoc/Installation.html).

3. Install Google Chrome from the [official page](https://www.google.com/chrome/).

4. Get an [API key from Riot Games](https://developer.riotgames.com/) and paste it to `./database/KEYS/RIOT_API_KEY.json` (follow the format provided).
```json
{"RIOT_API_KEY": "your_riot_api_key"}
```

5. Specify the Twitch username and the League of Legends region they play in ("euw1", "na1", "eun1", "la1", "la2", "br1", "oc1", "jp1", "kr", "ru", "tr1") of the streamers you would like to extract videos from in `./database/STREAMERS.json` (follow the format provided).
```json
[["twitch_username_1", "na1"], ["twitch_username_2", "euw1"]]
```

These steps are enough to download stream videos from Twitch and create the highlights videos. However, the automatic upload to YouTube requires a [Google account](https://www.google.com/account/about/) as well as authentication and authorization to use [Google APIs following the OAuth 2.0 protocol](https://developers.google.com/identity/protocols/oauth2/web-server).

5. Get `client_secrets.json` (it would be necessary to rename it) from Google API and save it to `./database/KEYS/client_secrets.json`.

**Enable APIs for your project**
Any application that calls Google APIs needs to enable those APIs in the API Console.
To enable an API for your project:

1. [Open the API Library](https://console.developers.google.com/apis/library) in the Google API Console.
2. If prompted, select a project, or create a new one.
3. The API Library lists all available APIs, grouped by product family and popularity. Select the YouTube Data API v3, then click the Enable button.
5. If prompted, enable billing.
6. If prompted, read and accept the API's Terms of Service.

**Create authorization credentials**

Any application that uses OAuth 2.0 to access Google APIs must have authorization credentials that identify the application to Google's OAuth 2.0 server. The following steps explain how to create credentials for your project. Your applications can then use the credentials to access APIs that you have enabled for that project.

1. Go to the [Credentials page](https://console.developers.google.com/apis/credentials).
2. Click Create credentials > OAuth client ID.
3. Select the Web application application type.

Fill in the form and click Create. You must specify authorized redirect URIs. The redirect URIs are the endpoints to which the OAuth 2.0 server can send responses. These endpoints must adhere to Google’s validation rules. For our purpose, you can specify URIs that refer to the local machine, such as http://localhost:8080.

After creating your credentials, download the `client_secrets.json` (it would be necessary to rename it) file from the API Console and save it to `./database/KEYS/client_secrets.json`.

6. Obtain OAuth 2.0 access tokens. As long as the secrets file is saved at `./database/KEYS/client_secrets.json`, if necessary, running the `main.py `script will generate and save the credentials to `./database/KEYS/token.pickle` (after the required manual authentication and authorization). These credentials expire, so eventually it would be necessary to manually authenticate and authorize again. Alternatively, the `credentials.py` script allows to generate and save the credentials beforehand to avoid the authentication and authorization steps while running the `main.py`.

> **_NOTE:_** The `./database` folder is created by default in the project's directory. All raw stream videos, games videos and highlights videos will be stored there. If facing storage problems, it is possible to change the database location by specifying the desired path (i.e `D:/database/`) in the `./src/paths.py` script. Just remember to create/move `./database/STREAMERS.json` and `./database/KEYS` and its content to the new database location.

Alternatively, download the Docker image from here and follow the instructions from there.

## Description
This project automatizes the whole process of video editing [League of Legends](https://www.leagueoflegends.com/) streams from [Twitch](https://www.twitch.tv/) and uploading them to [YouTube](https://www.youtube.com/). First, the videos are downloaded from Twitch using Selenium and the online video downloader [youtube4kdownloader](https://youtube4kdownloader.com/). Then, raw stream videos are processed to find the League of Legends games and extract identifying information from the games that is later used to download the games data in JSON format from [Riot's API](https://developer.riotgames.com/). The game data includes timestamps from the relevant events from the game that are used to create the final highlights video. Finally, the highlights videos can be uploaded to YouTube using the [Youtube Data API v3](https://developers.google.com/youtube/v3) (requires OAuth 2.0).

![project-workflow](https://imgur.com/pBmFHD5)
## Usage

```console
> python main.py -h
usage: main.py [-h] [--create_videos [{True,False}]] [--upload_videos [{True,False}]] [--download_streams [{True,False}]] [--prev_days [PREV_DAYS]] [--extract_information [{True,False}]]
               [--extract_raw_game_videos [{True,False}]] [--create_highlights_videos [{True,False}]] [--use_thumbnail [{True,False}]] [--add_video_intro [{True,False}]]
               [--add_video_outro [{True,False}]] [--n_videos [N_VIDEOS]]

options:
  -h, --help            show this help message and exit
  --create_videos [{True,False}]
                        General option to download, extract information and create highlight videos
  --upload_videos [{True,False}]
                        Option to upload already existing videos to YouTube
  --download_streams [{True,False}]
                        Option to download new streams from Twitch
  --prev_days [PREV_DAYS]
                        Previous days to look for stream videos in Twitch
  --extract_information [{True,False}]
                        Option to extract information from stream videos
  --extract_raw_game_videos [{True,False}]
                        Option to extract raw game videos from stream videos
  --create_highlights_videos [{True,False}]
                        Option to create highlight videos from raw game videos
  --use_thumbnail [{True,False}]
                        Option to generate and use thumbnail for YouTue video
  --add_video_intro [{True,False}]
                        Option to add default intro video. To add a custom intro video, replace `./templates/intro.mp4`
  --add_video_outro [{True,False}]
                        Option to add default outro video. To add a custom outro video, replace `./templates/outro.mp4`
  --n_videos [N_VIDEOS]
                        Number of videos to upload to YouTube
```

## Results

I created the YouTube channel ([Shimmer Addict](https://www.youtube.com/channel/UCTQQV9W6Pwjjn0PCIXuEzPw)) to upload the created highglights videos for people to watch them. The sucess of the channel could be an indicator of the quality of the videos created with this project. Go have a look and feel free to subscribe ;)