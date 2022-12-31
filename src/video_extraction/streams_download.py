from selenium import webdriver
import time
import datetime
from src.paths import STREAMS_PATH
from webdriver_manager.chrome import ChromeDriverManager
import json
import contextlib
from urllib.parse import _splittype
from urllib.error import ContentTooShortError
import os
from urllib.request import urlopen
import cv2


def download_videos_from_twitch(streamer, n_prev_days=3):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('lang=en')
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)

    # open the webpage
    streamer_twitch_videos_page = "https://www.twitch.tv/" + streamer.lower() + "/videos?filter=all&sort=time"
    driver.get(streamer_twitch_videos_page)
    time.sleep(15)

    stream_info_dict = {}
    video_ids = []

    date_threshold = datetime.datetime.today() - datetime.timedelta(days=5)
    for i in range(30):
        date = driver.find_element_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//div[@class='preview-card-thumbnail__image']//img").get_attribute("title")
        date = datetime.datetime.strptime(date, '%b %d, %Y')
        if date < date_threshold:
            break
        try:
            if driver.find_element_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//a[@data-test-selector='GameLink']").get_attribute("textContent") == "League of Legends":
                
                video_link = driver.find_element_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//a[@data-a-target='preview-card-image-link']").get_attribute("href")
                video_id = "".join([s for s in video_link if s.isdigit()])
                video_ids.append(video_id)

                raw_time = driver.find_element_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//div[@class='ScPositionCorner-sc-1shjvnv-1 hoKYhE']").get_attribute("textContent")
                raw_time = raw_time.split(":")
                raw_time.reverse()
                video_length_seconds = sum(int(x) * 60**n for n,x in enumerate(raw_time))
                gameplay_duration = [(0, video_length_seconds)]
                stream_info_dict[video_id] = gameplay_duration
        except:
            time.sleep(1)
            caps_button = driver.find_element_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//button[@class='ScCoreButton-sc-ocjdkq-0 ScCoreButtonSecondary-sc-ocjdkq-2 ibtYyW hUInuk']")
            time.sleep(1)
            webdriver.ActionChains(driver).move_to_element(caps_button).click(caps_button).perform()
            time.sleep(1)
            caps_games = [game_title.get_attribute("textContent") for game_title in driver.find_elements_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//div[@class='Layout-sc-1xcs6mc-0 kBprba']//div[@class='Layout-sc-1xcs6mc-0 media-row__info-text']")]

            if "League of Legends" in caps_games:
                video_link = driver.find_element_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//a[@data-a-target='preview-card-image-link']").get_attribute("href")
                video_id = "".join([s for s in video_link if s.isdigit()])
                video_ids.append(video_id)

                gameplay_duration = []
                caps_times = [game_time.get_attribute("textContent") for game_time in driver.find_elements_by_xpath(f"//div[@data-a-target='video-tower-card-{i}']//div[@class='Layout-sc-1xcs6mc-0 kBprba']//div[@class='Layout-sc-1xcs6mc-0 media-row__info-description']")]
                current_time = 0
                for game_title, game_raw_time in zip(caps_games, caps_times):
                    game_raw_time = game_raw_time.replace("hours", "hour")
                    game_raw_time = game_raw_time.replace("minutes", "minute")
                    game_raw_time = game_raw_time.replace("seconds", "second")
                    text = [w for w in game_raw_time.split() if w.isalpha()]
                    numbers = [w for w in game_raw_time.split() if w.isnumeric()]
                    time_dict = {w:n for w, n in zip(text, numbers)}

                    hours = time_dict.get('hour') if time_dict.get('hour') else 0
                    minutes = time_dict.get('minute') if time_dict.get('minute') else 0
                    seconds = time_dict.get('second') if time_dict.get('second') else 0

                    game_raw_time = f"{hours} hour {minutes} minute {seconds} second"
                    game_raw_time = datetime.datetime.strptime(game_raw_time, '%H hour %M minute %S second')

                    game_time_seconds = 3600*game_raw_time.hour + 60*game_raw_time.minute + game_raw_time.second
                    
                    if game_title == "League of Legends":
                        gameplay_duration += [(current_time, game_time_seconds)]

                    current_time += game_time_seconds
                
                stream_info_dict[video_id] = gameplay_duration

    for video_id in video_ids:
        download_folder_path = STREAMS_PATH / streamer / video_id
        download_folder_path.mkdir(parents=True, exist_ok=True)
        video_path = download_folder_path / (video_id + ".mp4")
        stream_times_json_path = download_folder_path / ("stream_times" + ".json")
        last_game_time_seconds = stream_info_dict[video_id][-1][1]
        with open(stream_times_json_path.as_posix(), 'w', encoding='utf-8') as outfile:
            json.dump(stream_info_dict[video_id], outfile)

        try:
            video = cv2.VideoCapture(video_path.as_posix())
            duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS)
        except:
            duration=-1
        if (not video_path.exists()) or (duration <= last_game_time_seconds):
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('window-size=1920x1080')
            chrome_options.add_argument('lang=en')
            driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
            download_link = r"https://youtube4kdownloader.com/download/video/https%253A%252F%252Fwww.twitch.tv%252Fvideos%252F" + video_id
            driver.get(download_link)
            time.sleep(60)

            download_divs = driver.find_elements_by_css_selector("a[class='downloadBtn']")
            download_link = download_divs[0].get_attribute("href")

            print(f"Download of {streamer} stream with id {video_id} in progress")
            urlretrieve(download_link, video_path.as_posix(), last_game_time_seconds)
            print("Finished download")
        else:
            print(f"{streamer} stream with id {video_id} already downloaded")

def urlretrieve(url, filename, last_game_time_seconds):
    """
    Retrieve a URL into a temporary location on disk.

    Requires a URL argument. If a filename is passed, it is used as
    the temporary file location. The reporthook argument should be
    a callable that accepts a block number, a read size, and the
    total file size of the URL target. The data argument should be
    valid URL encoded data.

    If a filename is passed and the URL points to a local resource,
    the result is a copy from local file to new file.

    Returns a tuple containing the path to the newly created
    data file as well as the resulting HTTPMessage object.
    """
    url_type, path = _splittype(url)

    with contextlib.closing(urlopen(url)) as fp:
        headers = fp.info()

        # Just return the local path and the "headers" for file://
        # URLs. No sense in performing a copy unless requested.
        if url_type == "file" and not filename:
            return os.path.normpath(path), headers

        tfp = open(filename, 'wb')

        continue_download = True
        with tfp:
            result = filename, headers
            bs = 1024*8
            size = -1
            read = 0
            blocknum = 0
            if "content-length" in headers:
                size = int(headers["Content-Length"])

            while continue_download:
                block = fp.read(bs)
                if not block:
                    break
                read += len(block)
                tfp.write(block)
                blocknum += 1
                if blocknum % (1000*6*5) == 0:
                    video = cv2.VideoCapture(filename)
                    duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS)
                    if duration > last_game_time_seconds:
                        continue_download = False

    if size >= 0 and read < size:
        raise ContentTooShortError(
            "retrieval incomplete: got only %i out of %i bytes"
            % (read, size), result)

    return result

