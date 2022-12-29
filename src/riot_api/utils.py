import requests
import datetime
import json
import time
from src.paths import JSON_PATH, STREAMERS_SUMMONERS_NAMES_JSON_PATH, RIOT_API_KEY_PATH
import os

with open(RIOT_API_KEY_PATH, "r", encoding='utf-8') as file:
    RIOT_API_KEY = json.load(file)["RIOT_API_KEY"]

def extract_games_json_by_username(streamer_summoner_name, region, prev_days):

    print(f"Start of Extraction of games data from RIOT API for {streamer_summoner_name} in region {region}")

    start_games_data_extraction = datetime.datetime.now().timestamp()
    with open(STREAMERS_SUMMONERS_NAMES_JSON_PATH, "r",
              encoding='utf-8') as file:
        streamers_summoner_names = json.load(file)
    for streamer, streamer_summoner_names in streamers_summoner_names.items():
        if streamer_summoner_name in streamer_summoner_names:
            break
    if region in ["euw1", "eun1", "ru", "tr1"]:
        region_1 = "europe"
    elif region in ["na1", "la1", "la2", "br1", "ru", "tr1"]:
        region_1 = "americas"
    else:
        region_1 = "asia"
    puuid = get_puuid_by_username(streamer_summoner_name, region=region)
    n=max(100, prev_days*25)
    match_ids = get_list_of_matches_by_puuid(puuid, queue_type="ranked", n=n, region=region_1)

    json_filepath = JSON_PATH / streamer /streamer_summoner_name
    json_filepath.mkdir(parents=True, exist_ok=True)
    for match_id in match_ids:
        if (match_id + ".json") not in os.listdir(json_filepath):
            get_game_info_by_matchid(match_id, streamer, streamer_summoner_name, region_1=region_1, region_2=region)
            time.sleep(0.5)

    date_threshold = datetime.datetime.today() - datetime.timedelta(days=20)
    for f in [os.path.join(json_filepath, f) for f in os.listdir(json_filepath)]:
        if datetime.datetime.fromtimestamp(os.stat(f).st_mtime) < date_threshold:
            os.remove(f)
    spent_time_games_data_extraction = datetime.datetime.now().timestamp() - start_games_data_extraction
    spent_time_games_data_extraction = str(datetime.timedelta(seconds=spent_time_games_data_extraction))
    print(f"End of Extraction of games data from RIOT API. Time: {spent_time_games_data_extraction}")

def get_puuid_by_username(username, region="euw1"):
    """
    :param username: LoL summoner name
    :param region: Possible regions are ["euw1", "na1", "eun1", "la1", "la2", "br1", "oc1", "jp1", "kr", "ru", "tr1"]
    :return: puuid associated to the summoner name
    """
    query = "https://" + region + ".api.riotgames.com/lol/summoner/v4/summoners/by-name/" + username + "?api_key=" + RIOT_API_KEY
    response = requests.get(query).json()

    return response["puuid"]

def get_list_of_matches_by_puuid(puuid, queue_type="ranked", n=20, region="europe"):
    """
    :param puuid: Player puuid
    :param queue_type: Possible queue types are ["ranked", "normal", "tourney", "tutorial"]
    :param n: Number of matches to extract
    :param region: Possible regions are ["europe", "americas", "asia"]
    :return: List of matches of the player
    """
    query = "https://" + region + ".api.riotgames.com/lol/match/v5/matches/by-puuid/" + puuid \
            + "/ids?type=" + queue_type +"&start=0&count=" + str(n) + "&api_key=" + RIOT_API_KEY
    response = requests.get(query).json()

    return response

def get_username_by_puuid(puuid, region="euw1"):
    """
    :param puuid: Player puuid
    :param region: Possible regions are ["euw1", "na1", "eun1", "la1", "la2", "br1", "oc1", "jp1", "kr", "ru", "tr1"]
    :return: Summoner name of the player
    """
    query = "https://" + region + ".api.riotgames.com/lol/summoner/v4/summoners/by-puuid/" + puuid + "?api_key=" + RIOT_API_KEY
    response = requests.get(query).json()
    return response["name"]

def get_game_info_by_matchid(match_id, streamer, streamer_summoner_name, region_1="europe", region_2="euw1"):
    """
    :param match_id: Match id
    :param streamer: Streamer name
    :param region_1: Possible regions are ["europe", "americas", "asia"]
    :param region_2: Possible regions are ["euw1", "na1", "eun1", "la1", "la2", "br1", "oc1", "jp1", "kr", "ru", "tr1"]
    """
    query = "https://" + region_1 + ".api.riotgames.com/lol/match/v5/matches/" + match_id + "/timeline?api_key=" + RIOT_API_KEY
    response = requests.get(query).json()

    players = []
    for puuid in response["metadata"]["participants"]:
        players.append(get_username_by_puuid(puuid, region=region_2))
        time.sleep(1.5)

    response["metadata"]["participants"] = players
    json_filepath = JSON_PATH / streamer / streamer_summoner_name
    if not os.path.isdir(json_filepath):
        os.makedirs(json_filepath)
    with open(json_filepath / (match_id + ".json"), 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False, indent=4)

def get_game_metadata_by_matchid(match_id):
    region = match_id.split("_")[0].lower()
    if region in ["euw1", "eun1", "ru", "tr1"]:
        region_1 = "europe"
    elif region in ["na1", "la1", "la2", "br1", "ru", "tr1"]:
        region_1 = "americas"
    else:
        region_1 = "asia"
    query = "https://" + region_1 + ".api.riotgames.com/lol/match/v5/matches/" + match_id + "?api_key=" + RIOT_API_KEY
    response = requests.get(query).json()

    return response

