#################################
##### Name: Guanru Wang
##### Uniqname: wguanru
#################################

from bs4 import BeautifulSoup
import plotly.graph_objects as go 
import requests
import json
import time
import re
import webbrowser
import sqlite3
from pathlib import Path

wiki_file = Path("./hero_wiki.sqlite")

OFFICAL_WEBSITE_URL = 'https://playoverwatch.com'
GAMEPEDIA_WEBSITE_URL = 'https://overwatch.gamepedia.com'
OVERBUFF_WEBSITE_URL = 'https://www.overbuff.com/heroes'
OFFICAL_WEBSITE_INDEX_PATH = '/en-us/heroes/'
GAMEPEDIA_WEBSITE_INDEX_PATH = '/Heroes'
CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

headers = {
    'User-Agent': 'UMSI 507 Course Final Project - Overwatch Hero Wiki',
    'From': 'wguanru@umich.edu', ## please replace with your own email
    'Course-Info': 'https://si.umich.edu/programs/courses/507'
}

create_heroes = '''
    CREATE TABLE IF NOT EXISTS "heroes" (
        "Id"          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        "Name"        TEXT NOT NULL,
        "Role"        TEXT NOT NULL,
        "Description" TEXT NOT NULL,
        "Quote"       TEXT NOT NULL,
        "Real_Name"   TEXT NOT NULL,
        "Age"         TEXT NOT NULL,
        "Nationality" TEXT NOT NULL,
        "Occupation"  TEXT NOT NULL,
        "Base"        TEXT NOT NULL,
        "Affiliation" TEXT NOT NULL,
        "Health"      TEXT NOT NULL,
        "Armor"       TEXT NOT NULL,
        "Shield"      TEXT NOT NULL,
        "Pick_Rate"   REAL NOT NULL,
        "Win_Rate"    REAL NOT NULL,
        "Tie_Rate"    REAL NOT NULL,
        "OnFire_Rate" REAL NOT NULL,
        "Pose_URL"    TEXT NOT NULL
    );
'''

drop_heroes = '''
    DROP TABLE IF EXISTS "heroes";
'''

add_hero = '''
    INSERT INTO heroes
    VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
'''

create_abilities = '''
    CREATE TABLE IF NOT EXISTS "abilities" (
        "Id"          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        "Name"        TEXT NOT NULL,
        "Description" TEXT NOT NULL,
        "Stats"       TEXT NOT NULL,
        "HeroId"      INTEGER NOT NULL,
        "Video_URL"   TEXT NOT NULL
    );
'''

drop_abilities = '''
    DROP TABLE IF EXISTS "abilities";
'''

add_ability = '''
    INSERT INTO abilities
    VALUES (NULL, ?, ?, ?, ?, ?)
'''

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    if (params == None):
        return baseurl # the url is our unique key
    else:
        param_strings = []
        connector = '_'
        for k in params.keys():
            param_strings.append(f'{k}_{params[k]}')
        param_strings.sort()
        unique_key = baseurl + connector + connector.join(param_strings)
        return unique_key


def load_cache():
    ''' Loads the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The loaded cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(baseurl, cache, params=None):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    url: string
        The URL for the API endpoint
    cache: dict
        The cache dictionary to search
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    request_key = construct_unique_key(baseurl, params)
    if (request_key in cache.keys()):
        print("Using cache")
        return cache[request_key]
    else:
        print("Fetching")
        time.sleep(1)
        if (params == None):
            response = requests.get(baseurl, headers=headers)
        else:
            response = requests.get(baseurl, headers=headers, params=params)
        cache[request_key] = response.text
        save_cache(cache)
        return cache[request_key] # in both cases, we return cache[request_key]


class Hero:
    '''a overwatch hero

    Instance Attributes
    -------------------
    role: string
        the role of a overwatch hero (e.g. 'Tank', 'Damage', 'Support')
    
    name: string
        the name of a overwatch hero (e.g. 'Ana')

    description: string
        the description of a overwatch hero (e.g. 'Ana’s versatile arsenal allows her to affect heroes...')

    abilities: dict
        the list of abilities of a overwatch hero

    quote: string
        the quote of a overwatch hero (e.g. 'Never stop fighting for what you believe in.')

    hero_pose_url: string
        the URL for the pose of a overwatch hero (e.g. 'https://d1u1mce87gyfbn.cloudfront.net/hero/ana/full-portrait.png')

    health: string
        the health value of a overwatch hero (e.g. '200')
    
    armor: string
        the armor value of a overwatch hero (e.g. '50')
        
    shield: string
        the shield value of a overwatch hero (e.g. '100')

    real_name: string
        the real name of a overwatch hero (e.g. 'Ana Amari (أنا عماري)')
    
    age: string
        the age of a overwatch hero (e.g. '60')
    
    nationality: string
        the nationality of a overwatch hero (e.g. 'Egyptian')

    occupation: string
        the occupation of a overwatch hero (e.g. 'Sharpshooter (formerly) Overwatch second-in-command, captain (formerly) Bounty hunter')

    base: string
        the base of a overwatch hero (e.g. 'Cairo, Egypt')

    affiliation: string
        the affiliation of a overwatch hero (e.g. 'Egyptian security forces (formerly) Overwatch (formerly)')

    pick_rate: float
        the pick rate of a overwatch hero in the competition match
 
    win_rate: float
        the win rate of a overwatch hero in the competition match
    
    tie_rate: float
        the tie rate of a overwatch hero in the competition match

    on_fire_rate: float
        the on fire rate of a overwatch hero in the competition match
    '''
    def __init__(self, role="", name="", description="", abilities={}, quote="", hero_pose_url="", health="0", armor="0", shield="0", real_name="", age="", nationality="", occupation="", base="", affiliation="", pick_rate=0, win_rate=0, tie_rate=0, on_fire_rate=0):
        self.role = role
        self.name = name
        self.description = description
        self.abilities = abilities
        self.quote = quote
        self.hero_pose_url = hero_pose_url
        self.health = health
        self.armor = armor
        self.shield = shield
        self.real_name = real_name
        self.age = age
        self.nationality = nationality
        self.occupation = occupation
        self.base = base
        self.affiliation = affiliation
        self.pick_rate = pick_rate
        self.win_rate = win_rate
        self.tie_rate = tie_rate
        self.on_fire_rate = on_fire_rate
    
    def set_val_by_list(self, list):
        self.role = list[2]
        self.name = list[1]
        self.description = list[3]
        self.abilities = []
        self.quote = list[4]
        self.hero_pose_url = list[18]
        self.health = list[11]
        self.armor = list[12]
        self.shield = list[13]
        self.real_name = list[5]
        self.age = list[6]
        self.nationality = list[7]
        self.occupation = list[8]
        self.base = list[9]
        self.affiliation = list[10]
        self.pick_rate = float(list[14])
        self.win_rate = float(list[15])
        self.tie_rate = float(list[16])
        self.on_fire_rate = float(list[17])


    def info(self):
        return self.name + " (" + self.role + "): " + self.description + "\nQuote: " + self.quote

    def detail_info(self):
        return "Real Name: " + self.real_name + "\nAge: " + self.age + "\nNationality: " + self.nationality + "\nOccupation: " + self.occupation  + "\nBase: " + self.base  + "\nAffiliation: " + self.affiliation

    def stats(self):
        return "Health: " + self.health + "\nArmor: " + self.armor + "\nShield: " + self.shield

    def compete_stats(self):
        return "Pick rate: " + str(self.pick_rate) + "%\nWin rate: " + str(self.win_rate) + "%\nTie rate: " + str(self.tie_rate) +"%\nOn Fire rate: " + str(self.on_fire_rate) + "%"
    
    def show_pose(self):
        print("Showing the pose of " + self.name + " in web browser...")
        webbrowser.open(self.hero_pose_url)


class Ability:
    '''an ability of a overwatch hero

    Instance Attributes
    -------------------    
    name: string
        the name of an ablitiy (e.g. 'Biotic Rifle')

    description: string
        the description of an ability (e.g. "Ana's versatile arsenal allows her to affect heroes...")

    video_url: string
        the URL for the video of an ability (e.g. 'https://d1u1mce87gyfbn.cloudfront.net/hero/ana/ability-biotic-rifle/video-ability.mp4')

    stats: string
        the stats of an ability (e.g. "Type: Weapon. Damage: 70 over 0.6 seconds. Spread angle: Pinpoint...")
    '''
    def __init__(self, name="", description="", video_url="", stats=""):
        self.name = name
        self.description = description
        self.video_url = video_url
        self.stats = stats

    def info(self):
        return self.name + ": " + self.description

    def show_stats(self):
        return self.stats

    def show_video(self):
        print("Showing the video of " + self.name + " in web browser...")
        webbrowser.open(self.video_url)


def build_hero_official_url_dict():
    ''' Make a dictionary that maps hero name to hero page url from "https://playoverwatch.com/en-us/heroes/"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a hero name and value is the url
        e.g. {'Ana':'https://playoverwatch.com/en-us/heroes/ana/', ...}
    '''
    index_page_url = OFFICAL_WEBSITE_URL + OFFICAL_WEBSITE_INDEX_PATH
    url_text = make_url_request_using_cache(index_page_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    hero_official_url_dict = {}

    ## For each hero listed
    hero_listing_parent = soup.find('div', class_="heroes-container", id="heroes-selector-container")
    hero_listing_divs = hero_listing_parent.find_all('div', recursive=False)
    for hero_listing_div in hero_listing_divs:

        ## extract the hero name
        hero_name = hero_listing_div.find('a').find('span', class_="portrait-title").text.strip()

        ## extract the hero details URL
        hero_link_tag = hero_listing_div.find('a')
        hero_details_path = hero_link_tag['href']
        hero_details_url = OFFICAL_WEBSITE_URL + hero_details_path

        ## add the hero info into dict
        hero_official_url_dict[hero_name] = hero_details_url

    return hero_official_url_dict


def get_official_hero_instance(hero_name, hero_url):
    '''Make an instances from hero page URL.
    
    Parameters
    ----------
    hero_name: string
        the name of a overwatch hero (e.g. 'Ana')

    hero_url: string
        The URL for a hero page in playoverwatch.com
    
    Returns
    -------
    instance
        a hero instance
    '''
    url_text = make_url_request_using_cache(hero_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    
    ## extract the hero role
    hero_role_div = soup.find('div', class_="hero-detail-role")
    hero_role_tag = hero_role_div.find('h4')
    hero_role = hero_role_tag.text.strip()

    ## extract the hero description
    hero_description = soup.find('p', class_="hero-detail-description").text.strip()

    ## extract the hero abilities
    hero_abilities_dict = {}
    hero_abilities_parent = soup.find('div', class_="hero-detail-wrapper m-same-pad")
    hero_abilities_divs = hero_abilities_parent.find_all('div', class_="hero-ability")
    for hero_abilities_div in hero_abilities_divs:
        hero_ability_descriptor = hero_abilities_div.find('div', class_="hero-ability-descriptor")
        hero_ability_name = hero_ability_descriptor.find('h4').text.strip().replace("’", "'")
        hero_ability_description = hero_ability_descriptor.find('p').text.strip().replace("’", "'")
        hero_ability_video_parent = hero_abilities_div.find('video', class_="hero-ability-video")
        hero_ability_video_url = hero_ability_video_parent.find('source', type="video/mp4")['src']
        hero_ability = Ability(hero_ability_name, hero_ability_description, hero_ability_video_url)
        hero_abilities_dict[hero_ability_name] = hero_ability

    ## extract the hero quote
    hero_quote = soup.find('p', class_="h4 hero-bio-quote").text.strip()

    ## extract the hero pose image url
    hero_pose_parent = soup.find('div', class_="hero-pose")
    hero_pose_tag = hero_pose_parent.find('div', class_="hero-pose-image")['style']
    hero_pose_url = re.findall(r'.*[(](.*)[)].*', hero_pose_tag)[0]

    return Hero(hero_role, hero_name, hero_description, hero_abilities_dict, hero_quote, hero_pose_url)


def build_hero_gamepedia_url_dict():
    ''' Make a dictionary that maps hero name to hero page url from "https://overwatch.gamepedia.com/Heroes"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a hero name and value is the url
        e.g. {'Ana':'https://overwatch.gamepedia.com/Ana/', ...}
    '''
    index_page_url = GAMEPEDIA_WEBSITE_URL + GAMEPEDIA_WEBSITE_INDEX_PATH
    url_text = make_url_request_using_cache(index_page_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    hero_gamepedia_url_dict = {}

    ## For each hero listed
    hero_table_parent = soup.find('tbody')
    hero_tds = hero_table_parent.find_all('td', style="width:12.5%; font-size:110%; background-color:rgba(243, 192, 174,);")
    for hero_td in hero_tds:

        ## extract the hero name
        hero_name = hero_td.text.strip()

        ## extract the hero details URL
        hero_details_url = hero_td.find('a')['href']

        ## add the hero info into dict
        hero_gamepedia_url_dict[hero_name] = GAMEPEDIA_WEBSITE_URL + hero_details_url

    return hero_gamepedia_url_dict


def add_ability_stats_to_hero_instance(hero_inst, hero_url):
    ''' Add infos from hero page URL into instances  
    
    Parameters
    ----------
    hero_inst: instance
        a hero instance

    hero_url: string
        The URL for a hero page in overwatch.gamepedia.com
    '''
    url_text = make_url_request_using_cache(hero_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    
    hero_abilities_stats_divs = soup.find_all('div', class_="ability_details_main", style="display: flex; flex-wrap: wrap; align-items: flex-start;")
    for hero_abilities_stats_div in hero_abilities_stats_divs:
        hero_ability_name_itr = hero_abilities_stats_div.find('div', class_="abilityHeader", style="font-weight:bold; font-size:140%; border:1px solid #2f4362; border-bottom: 1px solid white; padding:3px 5px; background:rgba(0,0,0,0.4);").strings
        hero_ability_name = list(hero_ability_name_itr)[0]

        hero_ability_type_div = hero_abilities_stats_div.find('div', style="padding:5px 5px; font-size:85%; text-align:center; border-bottom:1px solid white; width:100%")
        hero_ability_type_block = hero_ability_type_div.find('div', style="display:inline-block; width:50%; vertical-align:top;")
        hero_ability_type = hero_ability_type_block.find('div', style="display:block; padding-top:5px;").text.strip()

        hero_ability_block = hero_abilities_stats_div.find('div', style="padding:5px;")
        hero_ability_display_blocks = hero_ability_block.find_all('div', style="display:block;")
        hero_ablility_stats = "\nType: " + hero_ability_type + "\n"
        for hero_ability_display_block in hero_ability_display_blocks:
            hero_ability_display_block_title = hero_ability_display_block.find('div', style="display:inline-block; vertical-align:top; padding-right:3px;").text.strip()
            hero_ability_display_block_content_itr = hero_ability_display_block.find('div', style="display:inline-block;").strings
            hero_ability_display_block_content_list = list(hero_ability_display_block_content_itr)
            hero_ablility_stats += hero_ability_display_block_title
            for hero_ability_display_block_content in hero_ability_display_block_content_list:
                hero_ablility_stats += hero_ability_display_block_content + ". "
            hero_ablility_stats += "\n"

        for hero_ability in hero_inst.abilities.keys():
            if hero_ability_name.lower() == hero_ability.lower():
                hero_inst.abilities[hero_ability].stats += hero_ablility_stats

    hero_info_table = soup.find('table', class_="infoboxtable", style="width:375px")
    hero_info_table_trs = hero_info_table.find_all('tr')
    for hero_info_table_tr in hero_info_table_trs:
        if(hero_info_table_tr.find('div')):
            hero_info_table_tr_tag = hero_info_table_tr.find('div').text.strip()
            if (hero_info_table_tr_tag.lower() == "real name"):
                hero_inst.real_name = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "age"):
                hero_inst.age = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "nationality"):
                hero_inst.nationality = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "occupation"):
                hero_inst.occupation = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "base"):
                hero_inst.base = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "affiliation"):
                hero_inst.affiliation = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "health"):
                hero_inst.health = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "armor"):
                hero_inst.armor = hero_info_table_tr.find_all('td')[1].text.strip()
            elif (hero_info_table_tr_tag.lower() == "shields"):
                hero_inst.shield = hero_info_table_tr.find_all('td')[1].text.strip()


def add_match_stats_to_hero_instance(hero_dict):
    ''' Add infos from hero page URL into instances  
    
    Parameters
    ----------
    hero_dict: dict
        the hero dictionary
    '''
    url_text = make_url_request_using_cache(OVERBUFF_WEBSITE_URL, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    
    hero_match_stats_tbody = soup.find('table', class_="table-data table-sortable").find('tbody')
    hero_match_stats_trs = hero_match_stats_tbody.find_all('tr')
    for hero_match_stats_tr in hero_match_stats_trs:
        hero_match_stats_spans = hero_match_stats_tr.find_all('span')
        hero_match_stats_list = []
        for hero_match_stats_span in hero_match_stats_spans:
            if (hero_match_stats_span.find('a')):
                # print(hero_match_stats_span.find('a').text.strip())
                hero_match_stats_list.append(hero_match_stats_span.find('a').text.strip())
            else:
                # print(hero_match_stats_span.text.strip())
                hero_match_stats_list.append(hero_match_stats_span.text.strip())
        
        hero_name = hero_match_stats_list[0].lower()
        if (hero_dict[hero_name]):
            hero_dict[hero_name].pick_rate = float(hero_match_stats_list[1].strip('%'))
            hero_dict[hero_name].win_rate = float(hero_match_stats_list[2].strip('%'))
            hero_dict[hero_name].tie_rate = float(hero_match_stats_list[3].strip('%'))
            hero_dict[hero_name].on_fire_rate = float(hero_match_stats_list[4].strip('%'))


def create_heroes_table(hero_dict):
    '''Build a Heroes Table from hero dict.
    
    Parameters
    ----------
    hero_dict: dict
        hero dict including all infos of all heroes
    '''
    conn = sqlite3.connect("hero_wiki.sqlite")
    cur = conn.cursor()

    ## create table
    cur.execute(drop_heroes)
    cur.execute(create_heroes)
    conn.commit()

    ## add infos
    for hero_name in hero_dict.keys():
        name = hero_dict[hero_name].name
        role = hero_dict[hero_name].role
        description = hero_dict[hero_name].description
        quote = hero_dict[hero_name].quote
        real_name = hero_dict[hero_name].real_name
        age = hero_dict[hero_name].age
        nationality = hero_dict[hero_name].nationality
        occupation = hero_dict[hero_name].occupation
        base = hero_dict[hero_name].base
        affiliation = hero_dict[hero_name].affiliation
        health = hero_dict[hero_name].health
        armor = hero_dict[hero_name].armor
        shield = hero_dict[hero_name].shield
        pick_rate = hero_dict[hero_name].pick_rate
        win_rate = hero_dict[hero_name].win_rate
        tie_rate = hero_dict[hero_name].tie_rate
        on_fire_rate = hero_dict[hero_name].on_fire_rate
        hero_pose_url = hero_dict[hero_name].hero_pose_url
        cur.execute(add_hero, [name, role, description, quote, real_name, age, nationality, occupation, base, affiliation, health, armor, shield, pick_rate, win_rate, tie_rate, on_fire_rate, hero_pose_url])
        conn.commit()

    conn.close()


def create_abilities_table(hero_dict):
    '''Build an Abilities Table from hero dict.
    
    Parameters
    ----------
    hero_dict: dict
        hero dict including all infos of all heroes
    '''
    conn = sqlite3.connect("hero_wiki.sqlite")
    cur = conn.cursor()

    ## create table
    cur.execute(drop_abilities)
    cur.execute(create_abilities)
    conn.commit()

    ## add infos
    hero_id = 1
    for hero_name in hero_dict.keys():
        for ability_name in hero_dict[hero_name].abilities.keys():
            name = hero_dict[hero_name].abilities[ability_name].name
            description = hero_dict[hero_name].abilities[ability_name].description
            stats = hero_dict[hero_name].abilities[ability_name].stats.lstrip()
            video_url = hero_dict[hero_name].abilities[ability_name].video_url
            cur.execute(add_ability, [name, description, stats, hero_id, video_url])
            conn.commit()
        hero_id += 1

    conn.close()


def search_hero_table_by_name(hero_name):
    connection = sqlite3.connect("hero_wiki.sqlite")
    cursor = connection.cursor()
    query = ''
    query += 'SELECT * From heroes'
    query += ' WHERE Name = "' + hero_name + '"'
    results = cursor.execute(query).fetchall()
    connection.close()
    return results

def search_hero_table_by_role(role=None):
    connection = sqlite3.connect("hero_wiki.sqlite")
    cursor = connection.cursor()
    query = ''
    query += 'SELECT * From heroes'
    if (role is not None):
        query += ' WHERE Role = "' + role + '"'
    results = cursor.execute(query).fetchall()
    connection.close()
    return results

def search_ablility_table_by_ablitity_name(ablitity_name):
    connection = sqlite3.connect("hero_wiki.sqlite")
    cursor = connection.cursor()
    query = ''
    query += 'SELECT abilities.Name, abilities.Description, abilities.Stats, Video_URL, heroes.Name From abilities JOIN heroes ON abilities.HeroId = heroes.Id'
    query += ' WHERE abilities.Name = "' + ablitity_name + '"'
    results = cursor.execute(query).fetchall()
    connection.close()
    return results


def search_ablility_table_by_hero_name(hero_name):
    connection = sqlite3.connect("hero_wiki.sqlite")
    cursor = connection.cursor()
    query = ''
    query += 'SELECT abilities.Name, abilities.Description, abilities.Stats, Video_URL From abilities JOIN heroes ON abilities.HeroId = heroes.Id'
    query += ' WHERE heroes.Name = "' + hero_name + '"'
    results = cursor.execute(query).fetchall()
    connection.close()
    return results

def hero_comparison_barplot(hero_list, cmp_choice):
    x_axis = []
    y_axis = []
    labels = []
    values = []
    if cmp_choice == 1:
        for hero in hero_list:
            x_axis.append(hero.name)
            y_axis.append(hero.health.split(" ")[0])
        bar_data = go.Bar(x=x_axis, y=y_axis)
        basic_layout = go.Layout(title="Hero Comparison by Health")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()
    elif cmp_choice == 2:
        for hero in hero_list:
            x_axis.append(hero.name)
            y_axis.append(hero.armor.split(" ")[0])
        bar_data = go.Bar(x=x_axis, y=y_axis)
        basic_layout = go.Layout(title="Hero Comparison by Armor")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()        
    elif cmp_choice == 3:
        for hero in hero_list:
            x_axis.append(hero.name)
            y_axis.append(hero.shield.split(" ")[0])
        bar_data = go.Bar(x=x_axis, y=y_axis)
        basic_layout = go.Layout(title="Hero Comparison by Shield")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()
    elif cmp_choice == 4:
        for hero in hero_list:
            labels.append(hero.name)
            values.append(hero.pick_rate)
        pie_data = go.Pie(labels=labels, values=values)
        basic_layout = go.Layout(title="Hero Comparison by Pick Rate")
        fig = go.Figure(data=pie_data, layout=basic_layout)
        fig.show()
    elif cmp_choice == 5:
        for hero in hero_list:
            x_axis.append(hero.name)
            y_axis.append(hero.win_rate)
        bar_data = go.Bar(x=x_axis, y=y_axis)
        basic_layout = go.Layout(title="Hero Comparison by Win Rate")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()
    elif cmp_choice == 6:
        for hero in hero_list:
            x_axis.append(hero.name)
            y_axis.append(hero.tie_rate)
        bar_data = go.Bar(x=x_axis, y=y_axis)
        basic_layout = go.Layout(title="Hero Comparison by Tie Rate")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()
    else:
        for hero in hero_list:
            x_axis.append(hero.name)
            y_axis.append(hero.on_fire_rate)
        bar_data = go.Bar(x=x_axis, y=y_axis)
        basic_layout = go.Layout(title="Hero Comparison by On Fire Rate")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()


if __name__ == "__main__":
    ## Load the cache, save in global variable
    CACHE_DICT = load_cache()

    if not wiki_file.exists():
        ## build url dict from official website
        hero_official_url_dict = build_hero_official_url_dict()

        ## build hero dict from official url dict
        hero_dict = {}
        for hero_name in hero_official_url_dict.keys():
            hero_url = hero_official_url_dict[hero_name]
            hero_inst = get_official_hero_instance(hero_name, hero_url)
            hero_dict[hero_name.lower()] = hero_inst
            
        ## build url dict from gamepedia website
        hero_gamepedia_url_dict = build_hero_gamepedia_url_dict()

        ## add gamepedia infos into class Hero in hero dict
        for hero_name in hero_gamepedia_url_dict.keys():
            try:
                add_ability_stats_to_hero_instance(hero_dict[hero_name.lower()], hero_gamepedia_url_dict[hero_name])
            except:
                pass
        
        # add_ability_stats_to_hero_instance(hero_dict['roadhog'], hero_gamepedia_url_dict['Roadhog'])
        # add_ability_stats_to_hero_instance(hero_dict['widowmaker'], hero_gamepedia_url_dict['Widowmaker'])

        ## add overbuff infos into class Hero in hero dict
        add_match_stats_to_hero_instance(hero_dict)

        ## build tables in database
        create_heroes_table(hero_dict)
        create_abilities_table(hero_dict)

        ## display infos in hero dict
        # for hero_name in hero_official_url_dict.keys():
        #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        #     hero_inst = hero_dict[hero_name.lower()]
        #     print(hero_inst.info())
        #     print(hero_inst.detail_info())
        #     print("")
        #     print(hero_inst.quote)
        #     print("")
        #     print(hero_inst.stats())
        #     print(hero_inst.compete_stats())
        #     print("*******************************************")
        #     for ability in hero_inst.abilities.keys():
        #         print(hero_inst.abilities[ability].info())
        #         print(hero_inst.abilities[ability].show_stats())
        #         print("*******************************************")
        #     print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

    ## interface
    while True:
        print("-----------------------------------------------------")
        print("########## Welcome to Overwatch Hero Wiki! ##########")
        print("- What do you want to search for?")
        print("- 1. Heroes")
        print("- 2. Abilities")
        print("- 3. Heroes comparison")
        search_option = input('Enter the number of your choice or "exit": ').lower()
        if search_option == 'exit':
            print("Thank you!")
            break
        elif search_option.isnumeric() and int(search_option) >= 1 and int(search_option) <= 2:
            if (int(search_option) == 1):
                while True:
                    print("-----------------------------------------------------")
                    print("- Which way do you want to search for a hero?")
                    print("- 1. By name")
                    print("- 2. By role")
                    search_hero_option = input('Enter the number of your choice or "back": ').lower()
                    print("-----------------------------------------------------")
                    if search_hero_option == 'back':
                        break
                    elif search_hero_option.isnumeric() and int(search_hero_option) >= 1 and int(search_hero_option) <= 2:
                        if (int(search_hero_option) == 1):
                            search_hero_name = input('Enter the name of the hero: ')
                            print("-----------------------------------------------------")
                            results = search_hero_table_by_name(search_hero_name)
                            if (results):
                                search_hero_result = Hero()
                                search_hero_result.set_val_by_list(results[0])
                                print(search_hero_result.info())
                                while True:
                                    print("-----------------------------------------------------")
                                    print("- What else do you want to know for this hero?")
                                    print("- 1. Detail info")
                                    print("- 2. Abilities info")
                                    print("- 3. Character stats")
                                    print("- 4. Competition match stats")
                                    print("- 5. Pose image")
                                    search_hero_detail_option = input('Enter the number of your choice or "back": ').lower()
                                    print("-----------------------------------------------------")
                                    if search_hero_detail_option == 'back':
                                        break
                                    elif search_hero_detail_option.isnumeric() and int(search_hero_detail_option) >= 1 and int(search_hero_detail_option) <= 5:
                                        if (int(search_hero_detail_option) == 1):
                                            print(search_hero_name + "'s detail information:")
                                            print(search_hero_result.detail_info())
                                        elif (int(search_hero_detail_option) == 2):
                                            results = search_ablility_table_by_hero_name(search_hero_name)
                                            index = 1
                                            print(search_hero_name + "'s abilities:")
                                            for result in results:
                                                print("(" + str(index) + ") " + Ability(result[0], result[1], result[3], result[2]).info())
                                                index += 1                                            
                                        elif (int(search_hero_detail_option) == 3):
                                            print(search_hero_name + "'s character stats:")
                                            print(search_hero_result.stats())
                                        elif (int(search_hero_detail_option) == 4):
                                            print(search_hero_name + "'s competition match stats:")
                                            print(search_hero_result.compete_stats())
                                        elif (int(search_hero_detail_option) == 5):
                                            search_hero_result.show_pose()
                                    else:
                                        print("Invalid choice. Try again.")
                            else:
                                print("No result matches.")
                        elif (int(search_hero_option) == 2):
                            while True:
                                print("-----------------------------------------------------")
                                print("- Which role do you want to search for?")
                                print("- 1. Support")
                                print("- 2. Damage")
                                print("- 3. Tank")
                                search_role_option = input('Enter the number of your choice or "back": ').lower()
                                print("-----------------------------------------------------")
                                if search_role_option == 'back':
                                    break
                                elif search_role_option.isnumeric() and int(search_role_option) >= 1 and int(search_role_option) <= 3:
                                    if (int(search_role_option) == 1):
                                        results = search_hero_table_by_role("Support")
                                        print("Support heroes:")
                                    elif (int(search_role_option) == 2):
                                        results = search_hero_table_by_role("Damage")
                                        print("Damage heroes:")
                                    elif (int(search_role_option) == 3):
                                        results = search_hero_table_by_role("Tank")
                                        print("Tank heroes:")
                                    if (results):
                                        index = 1
                                        hero_list = []
                                        for result in results:
                                            hero = Hero()
                                            hero.set_val_by_list(result)
                                            print("(" + str(index) + ") " + hero.info())
                                            hero_list.append(hero)
                                            index += 1
                                        while True:
                                            print("-----------------------------------------------------")
                                            print("- Which hero do you want to know more about?")
                                            index = 1
                                            for hero in hero_list:                    
                                                print("- " + str(index) + ". " + hero.name)
                                                index += 1
                                            search_hero_index_option = input('Enter the number of your choice or "back": ').lower()
                                            if search_hero_index_option == 'back':
                                                break
                                            elif search_hero_index_option.isnumeric() and int(search_hero_index_option) >= 1 and int(search_hero_index_option) <= len(hero_list):
                                                while True:
                                                    print("-----------------------------------------------------")
                                                    print("- What else do you want to know for this hero?")
                                                    print("- 1. Detail info")
                                                    print("- 2. Abilities info")
                                                    print("- 3. Character stats")
                                                    print("- 4. Competition match stats")
                                                    print("- 5. Pose image")
                                                    search_hero_detail_option = input('Enter the number of your choice or "back": ').lower()
                                                    print("-----------------------------------------------------")
                                                    if search_hero_detail_option == 'back':
                                                        break
                                                    elif search_hero_detail_option.isnumeric() and int(search_hero_detail_option) >= 1 and int(search_hero_detail_option) <= 5:
                                                        if (int(search_hero_detail_option) == 1):
                                                            print(hero_list[int(search_hero_index_option)-1].name + "'s detail information:")
                                                            print(hero_list[int(search_hero_index_option)-1].detail_info())
                                                        elif (int(search_hero_detail_option) == 2):
                                                            results = search_ablility_table_by_hero_name(hero_list[int(search_hero_index_option)-1].name)
                                                            index = 1
                                                            print(hero_list[int(search_hero_index_option)-1].name + "'s abilities:")
                                                            for result in results:
                                                                print("(" + str(index) + ") " + Ability(result[0], result[1], result[3], result[2]).info())
                                                                index += 1                                            
                                                        elif (int(search_hero_detail_option) == 3):
                                                            print(hero_list[int(search_hero_index_option)-1].name + "'s character stats:")
                                                            print(hero_list[int(search_hero_index_option)-1].stats())
                                                        elif (int(search_hero_detail_option) == 4):
                                                            print(hero_list[int(search_hero_index_option)-1].name + "'s competition match stats:")
                                                            print(hero_list[int(search_hero_index_option)-1].compete_stats())
                                                        elif (int(search_hero_detail_option) == 5):
                                                            hero_list[int(search_hero_index_option)-1].show_pose()
                                                    else:
                                                        print("Invalid choice. Try again.")
                                            else:
                                                print("-----------------------------------------------------")
                                                print("Invalid choice. Try again.")
                                    else:
                                        print("No result matches.")
                                else:
                                    print("-----------------------------------------------------")
                                    print("Invalid choice. Try again.")
                    else:
                        print("Invalid choice. Try again.")
                        continue
            elif (int(search_option) == 2):
                while True:
                    print("-----------------------------------------------------")
                    print("- Which way do you want to search for an ability?")
                    print("- 1. By ability name")
                    print("- 2. By hero name")
                    search_ability_option = input('Enter the number of your choice or "back": ').lower()
                    print("-----------------------------------------------------")
                    if search_ability_option == 'back':
                        break
                    elif search_ability_option.isnumeric() and int(search_ability_option) >= 1 and int(search_ability_option) <= 2:
                        if (int(search_ability_option) == 1):
                            search_ability_name = input('Enter the name of the ability: ')
                            print("-----------------------------------------------------")
                            results = search_ablility_table_by_ablitity_name(search_ability_name)
                            if (results):
                                result = results[0]
                                search_ability_result = Ability(result[0], result[1], result[3], result[2])
                                print("Belongs to hero: " + result[4])
                                print(search_ability_result.info())
                                while True:
                                    print("-----------------------------------------------------")
                                    print("- What else do you want to know for this ability?")
                                    print("- 1. Stats")
                                    print("- 2. Instruction video")
                                    search_ability_detail_option = input('Enter the number of your choice or "back": ').lower()
                                    print("-----------------------------------------------------")
                                    if search_ability_detail_option == 'back':
                                        break
                                    elif search_ability_detail_option.isnumeric() and int(search_ability_detail_option) >= 1 and int(search_ability_detail_option) <= 2:
                                        if (int(search_ability_detail_option) == 1):
                                            print("Stats of " + search_ability_name + ":")
                                            print(search_ability_result.show_stats())
                                        elif (int(search_ability_detail_option) == 2):
                                            search_ability_result.show_video()
                                    else:
                                        print("Invalid choice. Try again.")
                            else:
                                print("No result matches.")
                        elif (int(search_ability_option) == 2):
                            search_hero_name = input('Enter the name of the hero: ')
                            print("-----------------------------------------------------")
                            results = search_ablility_table_by_hero_name(search_hero_name)
                            if (results):
                                index = 1
                                ability_list = []
                                print(search_hero_name + "'s abilities:")
                                for result in results:
                                    ability = Ability(result[0], result[1], result[3], result[2])
                                    ability_list.append(ability)
                                    print("(" + str(index) + ") " + ability.info())
                                    index += 1
                                while True:
                                    print("-----------------------------------------------------")
                                    print("- Which ability do you want to know more about?")
                                    index = 1
                                    for ability in ability_list:                    
                                        print("- " + str(index) + ". " + ability.name)
                                        index += 1
                                    search_ability_index_option = input('Enter the number of your choice or "back": ').lower()
                                    if search_ability_index_option == 'back':
                                        break
                                    elif search_ability_index_option.isnumeric() and int(search_ability_index_option) >= 1 and int(search_ability_index_option) <= len(ability_list):
                                        while True:
                                            print("-----------------------------------------------------")
                                            print("- What else do you want to know for this ability?")
                                            print("- 1. Stats")
                                            print("- 2. Instruction video")
                                            search_ability_detail_option = input('Enter the number of your choice or "back": ').lower()
                                            print("-----------------------------------------------------")
                                            if search_ability_detail_option == 'back':
                                                break
                                            elif search_ability_detail_option.isnumeric() and int(search_ability_detail_option) >= 1 and int(search_ability_detail_option) <= 2:
                                                if (int(search_ability_detail_option) == 1):
                                                    print("Stats of " + ability_list[int(search_ability_index_option)-1].name + ":")
                                                    print(ability_list[int(search_ability_index_option)-1].show_stats())
                                                elif (int(search_ability_detail_option) == 2):
                                                    ability_list[int(search_ability_index_option)-1].show_video()
                                            else:
                                                print("Invalid choice. Try again.")
                                else:
                                    print("-----------------------------------------------------")
                                    print("Invalid choice. Try again.")
                            else:
                                print("No result matches.")
                    else:
                        print("Invalid choice. Try again.")
        elif search_option.isnumeric() and int(search_option) == 3:
            while True:
                print("-----------------------------------------------------")
                print("- Which role of heroes do you want to do the comparison?")
                print("- 1. Support")
                print("- 2. Damage")
                print("- 3. Tank")
                print("- 4. All heroes")
                search_role_option = input('Enter the number of your choice or "back": ').lower()
                print("-----------------------------------------------------")
                if search_role_option == 'back':
                    break
                elif search_role_option.isnumeric() and int(search_role_option) >= 1 and int(search_role_option) <= 4:
                    if (int(search_role_option) == 1):
                        results = search_hero_table_by_role("Support")
                    elif (int(search_role_option) == 2):
                        results = search_hero_table_by_role("Damage")
                    elif (int(search_role_option) == 3):
                        results = search_hero_table_by_role("Tank")
                    elif (int(search_role_option) == 4):
                        results = search_hero_table_by_role()
                    if (results):
                        index = 1
                        hero_list = []
                        for result in results:
                            hero = Hero()
                            hero.set_val_by_list(result)
                            hero_list.append(hero)
                            index += 1
                        while True:
                            print("-----------------------------------------------------")
                            print("- Which stats do you want to compare?")
                            print("- 1. Health")
                            print("- 2. Armor")
                            print("- 3. Shield")
                            print("- 4. Pick rate")
                            print("- 5. Win rate")
                            print("- 6. Tie rate")
                            print("- 7. On fire rate")
                            search_cmp_option = input('Enter the number of your choice or "back": ').lower()
                            print("-----------------------------------------------------")
                            if search_cmp_option == 'back':
                                break
                            elif search_cmp_option.isnumeric() and int(search_cmp_option) >= 1 and int(search_cmp_option) <= 7:
                                hero_comparison_barplot(hero_list, int(search_cmp_option))
                            else:
                                print("Invalid choice. Try again.")
                    else:
                        print("No result matches.")
                else:
                    print("Invalid choice. Try again.")
        else:
            print("-----------------------------------------------------")
            print("Invalid choice. Try again.")

