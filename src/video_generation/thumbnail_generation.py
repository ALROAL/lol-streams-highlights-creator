import requests
import bs4 as bs
import json
import re
import os
from PIL import ImageFont, Image, ImageDraw
import cv2
import pandas as pd
import numpy as np
from src.paths import EDITED_VIDEOS_INFO_PATH, CHAMPIONS_IMAGES_PATH, THUMBNAIL_IMAGES_PATH, FRIZ_QUADRATA_BOLD_FONT_PATH


def generate_thumbnail(video_path):

    download_champions_images()

    edited_videos_info = pd.read_excel(EDITED_VIDEOS_INFO_PATH)
    video_info = edited_videos_info[edited_videos_info["video_path"]==video_path]
    streamer, champion_name, stream_date, title = video_info[["streamer", "played_champion", "date", "title"]][video_info["video_path"] == video_path].values[0]
    title = title.split(" ft.")[0]

    champ_img = cv2.imread(CHAMPIONS_IMAGES_PATH.as_posix() + "/{}_OriginalSkin.png".format(champion_name))
    champ_img = cv2.cvtColor(champ_img, cv2.COLOR_BGR2RGB)
    champ_img = cv2.resize(champ_img, (1280, 720))

    H, W, _ = champ_img.shape
    image = put_black_rectangle(champ_img, 40, 450, W - 40 - 40, H - 450 - 30)
    image = put_black_rectangle(champ_img, 250, 15, W - 250 * 2, 150)

    im_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(im=im_pil)

    font = ImageFont.truetype(font=FRIZ_QUADRATA_BOLD_FONT_PATH.as_posix(), size=80)
    date_font = ImageFont.truetype(font=FRIZ_QUADRATA_BOLD_FONT_PATH.as_posix(), size=50)

    # Draw the text onto our image
    draw.text(xy=(W / 2, 510), text=streamer, font=font, fill='white', anchor='mm')
    draw.text(xy=(W / 2, 40), text=stream_date.strftime("%d/%m/%Y"), font=date_font, fill='white', anchor='mm')
    draw.text(xy=(W / 2, 630), text=title, font=font, fill='white', anchor='mm')
    draw.text(xy=(W / 2, 110), text="Stream Highlights", font=font, fill='white', anchor='mm')

    thumbnail_image_path = THUMBNAIL_IMAGES_PATH.as_posix() + "/{}_{}_{}.png".format(streamer, title, stream_date.strftime("%d-%m-%Y"))
    im_pil.save(thumbnail_image_path)

def download_champions_images():
    list_of_champions_from_wiki = get_champions_list_from_wiki()
    list_of_champions_from_files = [img_filename.split("_")[0] for img_filename in os.listdir(CHAMPIONS_IMAGES_PATH)]

    list_of_champions_to_get_images = list(set(list_of_champions_from_wiki) - set(list_of_champions_from_files))

    for champ in list_of_champions_to_get_images:
        champion_skins_page = "https://leagueoflegends.fandom.com/wiki/{}/LoL/Cosmetics".format(champ)
        response = requests.get(champion_skins_page)
        soup = bs.BeautifulSoup(response.text, 'lxml')
        original_skin_link = [link.attrs["href"] for link in soup.find_all('a', class_="image") if "OriginalSkin.jpg" in link.attrs["href"]][0]
        img_data = requests.get(original_skin_link).content
        image_path = CHAMPIONS_IMAGES_PATH.as_posix() + "/{}_OriginalSkin.png".format(champ)
        with open(image_path, 'wb') as image:
            image.write(img_data)

def get_champions_list_from_wiki():

    base_url = "https://leagueoflegends.fandom.com/api.php?"
    action = "action=query"
    content = "&prop=revisions&rvslots=*&rvprop=content"
    dataformat = "&format=json"

    title = "&titles=" + "List_of_champions"
    query = "%s%s%s%s%s" % (base_url, action, title, content, dataformat)

    req = requests.get(query).text
    req = json.loads(req)

    raw_text = req["query"]["pages"][list(req["query"]["pages"].keys())[0]]["revisions"][0]["slots"]["main"]["*"]
    list_of_champions_from_wiki = [name.strip() for name in re.findall('(?<=List of champions row\|)[A-ZAa-zÀ-ÿ .\']+', raw_text)]

    return list_of_champions_from_wiki


def put_black_rectangle(image, x, y, w, h):
    color = (0, 0, 0)
    thickness = 10

    sub_img = image[y:y + h, x:x + w]
    white_rect = np.zeros(sub_img.shape, dtype=np.uint8) * 255

    res = cv2.addWeighted(sub_img, 0.2, white_rect, 0.5, 1.0)

    # Putting the image back to its position
    image[y:y + h, x:x + w] = res

    # Using cv2.rectangle() method
    # Draw a rectangle with blue line borders of thickness of 2 px
    image = cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)

    return image