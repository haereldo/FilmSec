
import os
import re
import random
import json
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

import ttkbootstrap as tb
from ttkbootstrap.constants import *

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

APP_NAME = "FilmSec"


# ================================
# PLATFORM + VERİ KLASÖRÜ
# ================================
def sys_platform() -> str:
    try:
        import sys
        return sys.platform
    except Exception:
        return "unknown"


def app_data_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys_platform() == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


DATA_DIR = app_data_dir()
LISTS_DIR = os.path.join(DATA_DIR, "lists")
os.makedirs(LISTS_DIR, exist_ok=True)

WATCHED_FILE = os.path.join(DATA_DIR, "watched_movies.txt")
LISTS_META_FILE = os.path.join(DATA_DIR, "lists.json")
MOVIE_RATINGS_FILE = os.path.join(DATA_DIR, "movie_ratings.json")
MOVIE_NOTES_FILE = os.path.join(DATA_DIR, "movie_notes.json")
WATCH_DATES_FILE = os.path.join(DATA_DIR, "watch_dates.json")
WATCH_HISTORY_FILE = os.path.join(DATA_DIR, "watch_history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

POSTERS_DIR = os.path.join(DATA_DIR, "posters")
os.makedirs(POSTERS_DIR, exist_ok=True)


# ================================
# DOSYA OKU-YAZ
# ================================
def read_file(file_name: str) -> list[str]:
    if not os.path.exists(file_name):
        return []
    with open(file_name, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    lines.sort(key=str.lower)
    return lines


def write_file(file_name: str, data_list: list[str]) -> None:
    data_list = sorted(list(dict.fromkeys([x.strip() for x in data_list if x and x.strip()])), key=str.lower)
    with open(file_name, "w", encoding="utf-8") as f:
        for item in data_list:
            f.write(item + "\n")


def contains_ci(items: list[str], value: str) -> bool:
    v = value.strip().lower()
    return any(x.strip().lower() == v for x in items)


def remove_ci(items: list[str], value: str) -> list[str]:
    v = value.strip().lower()
    return [x for x in items if x.strip().lower() != v]


def normalize_movie(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()


# ================================
# PUAN VE NOT YÖNETİMİ
# ================================
def load_ratings() -> dict:
    """Film puanlarını yükle"""
    if not os.path.exists(MOVIE_RATINGS_FILE):
        return {}
    try:
        with open(MOVIE_RATINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ratings(ratings: dict) -> None:
    """Film puanlarını kaydet"""
    with open(MOVIE_RATINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)


def load_notes() -> dict:
    """Film notlarını yükle"""
    if not os.path.exists(MOVIE_NOTES_FILE):
        return {}
    try:
        with open(MOVIE_NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_notes(notes: dict) -> None:
    """Film notlarını kaydet"""
    with open(MOVIE_NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def load_watch_dates() -> dict:
    """İzlenme tarihlerini yükle - format: {movie_key: [date1, date2, ...]}"""
    if not os.path.exists(WATCH_DATES_FILE):
        return {}
    try:
        with open(WATCH_DATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_watch_dates(dates: dict) -> None:
    """İzlenme tarihlerini kaydet"""
    with open(WATCH_DATES_FILE, "w", encoding="utf-8") as f:
        json.dump(dates, f, ensure_ascii=False, indent=2)


def add_watch_date(movie: str, dates: dict) -> dict:
    """Filme yeni izlenme tarihi ekle"""
    from datetime import datetime
    movie_key = get_movie_key(movie)
    today = datetime.now().strftime("%d.%m.%Y")
    
    if movie_key not in dates:
        dates[movie_key] = []
    
    if today not in dates[movie_key]:
        dates[movie_key].append(today)
    
    return dates


def load_watch_history() -> dict:
    """İzlenme geçmişini yükle - format: {movie_key: list_id}"""
    if not os.path.exists(WATCH_HISTORY_FILE):
        return {}
    try:
        with open(WATCH_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_watch_history(history: dict) -> None:
    """İzlenme geçmişini kaydet"""
    with open(WATCH_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_to_watch_history(movie: str, list_id: str, history: dict) -> dict:
    """Filme hangi listeden eklendiğini kaydet"""
    movie_key = get_movie_key(movie)
    history[movie_key] = list_id
    return history


def load_settings() -> dict:
    """Ayarları yükle"""
    if not os.path.exists(SETTINGS_FILE):
        return {"first_launch": True, "tmdb_api_key": ""}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"first_launch": True, "tmdb_api_key": ""}


def save_settings(settings: dict) -> None:
    """Ayarları kaydet"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_movie_key(movie: str) -> str:
    """Film için benzersiz anahtar oluştur (büyük/küçük harf duyarsız)"""
    return normalize_movie(movie)


# ================================
# 1) Adnan'ın DVD listesi (TAM)
# ================================
DEFAULT_DVD_LIST = [
    ".45 (2006)",
    "11:14 (2003)",
    "120 (2008)",
    "1408 (2007)",
    "15 Minutes (2001)",
    "2001: A Space Odyssey (1968)",
    "2010: The Year We Make Contact (1984)",
    "30 Days of Night (2007)",
    "3:10 to Yuma (2007)",
    "50 First Dates (2004)",
    "8½ (1963)",
    "A Bronx Tale (1993)",
    "A Dangerous Man (2009)",
    "A Madonna in Laleli (1999)",
    "A Romantic Comedy 2 (2013)",
    "A Very Long Engagement (2004)",
    "A.I. Artificial Intelligence (2001)",
    "Ace Ventura: Pet Detective (1994)",
    "Ace Ventura: When Nature Calls (1995)",
    "Ali G Indahouse (2002)",
    "Alice in Wonderland (2010)",
    "Amadeus (1984)",
    "American Beauty (1999)",
    "American Gangster (2007)",
    "American Outlaws (2001)",
    "American Pie (1999)",
    "American Pie 2 (2001)",
    "American Pie Presents: Band Camp (2005)",
    "American Pie Presents: Beta House (2007)",
    "American Wedding (2003)",
    "America's Sweethearts (2001)",
    "Amistad (1997)",
    "Analyze That (2002)",
    "Analyze This (1999)",
    "Anatomy (2000)",
    "Angel Heart (1987)",
    "Angels & Demons (2009)",
    "Anna and the King (1999)",
    "Apocalypto (2006)",
    "Argo (2012)",
    "Awake (2007)",
    "Ballistic: Ecks vs. Sever (2002)",
    "Barry Lyndon (1975)",
    "Basic Instinct 2 (2006)",
    "Battleship (2012)",
    "Becoming Queen (2004)",
    "Behind Enemy Lines (2001)",
    "Being John Malkovich (1999)",
    "Beyond Borders (2021)",
    "Beyond the Clouds (1995)",
    "Billy Elliot (2000)",
    "Bitter Moon (1992)",
    "Black Hawk Down (2001)",
    "Blade (1998)",
    "Blade II (2002)",
    "Blade: Trinity (2004)",
    "Blood Diamond (2006)",
    "Blow (2001)",
    "Blues Brothers 2000 (1998)",
    "Boats Out of Watermelon Rinds (2004)",
    "Body of Lies (2008)",
    "Bonnie and Clyde (1967)",
    "Born on the Fourth of July (1989)",
    "Borrowed Bride (2005)",
    "Bride & Prejudice (2004)",
    "Bugsy (1991)",
    "Bullitt (1968)",
    "Captain Corelli's Mandolin (2001)",
    "Casualties of War (1989)",
    "Cat People (1982)",
    "Chaos (2005)",
    "Charlie's Angels (2000)",
    "Cholera Street (1997)",
    "City of God (2002)",
    "Climates (2006)",
    "Closer (2004)",
    "Con Air (1997)",
    "Conspiracy Theory (1997)",
    "Cowboy (1958)",
    "Cube (1997)",
    "Cube 2: Hypercube (2002)",
    "Curse of the Golden Flower (2006)",
    "Dance with the Jackals (2010)",
    "Dances with Wolves (1990)",
    "Darkness (2002)",
    "Death Race (2008)",
    "Death Race 2 (2010)",
    "Deception (2008)",
    "Demolition Man (1993)",
    "Derailed (2005)",
    "Diamonds Are Forever (1971)",
    "Die Another Day (2002)",
    "Dirty Dancing (1987)",
    "Dirty Harry (1971)",
    "Distant (2002)",
    "District B13 (2004)",
    "Double Trouble (1984)",
    "Driving Miss Daisy (1989)",
    "Due Date (2010)",
    "Dune (1984)",
    "Elephants and Grass (2000)",
    "Enemy at the Gates (2001)",
    "Escape from New York (1981)",
    "EuroTrip (2004)",
    "Evan Almighty (2007)",
    "Expat Şaban (1985)",
    "Eye for an Eye (1996)",
    "Face/Off (1997)",
    "Fazıl Say - Fenerbahçe Senfonisi (2007)",
    "Feeling Minnesota (1996)",
    "Femme Fatale (2002)",
    "Final Destination (2000)",
    "Final Destination 2 (2003)",
    "Final Destination 5 (2011)",
    "Flags of Our Fathers (2006)",
    "Flatliners (1990)",
    "Flight (2012)",
    "Flightplan (2005)",
    "Flyboys (2006)",
    "For Your Eyes Only (1981)",
    "Fracture (2007)",
    "Freddy vs. Jason (2003)",
    "Friday the 13th (1980)",
    "Friday the 13th Part III (1982)",
    "Friday the 13th Part VI: Jason Lives (1986)",
    "Fried Green Tomatoes (1991)",
    "G.I. Joe: Retaliation (2013)",
    "Gamer (2009)",
    "Glory (1989)",
    "God Send (2019)",
    "Gods and Generals (2003)",
    "GoldenEye (1995)",
    "Gothika (2003)",
    "Green Street Hooligans (2005)",
    "Gremlins (1984)",
    "Halloween: Resurrection (2002)",
    "Head in the Clouds (2004)",
    "Headhunters (2011)",
    "Heartbreak Ridge (1986)",
    "Heaven & Earth (1993)",
    "Hero (2002)",
    "He's Convict Now (2005)",
    "He's Just Not That Into You (2009)",
    "Hitman (2007)",
    "Hollow Man (2000)",
    "Hook (1991)",
    "Hotel Rwanda (2004)",
    "Hours (2013)",
    "How to Lose a Guy in 10 Days (2003)",
    "I Am Sam (2001)",
    "In Time (2011)",
    "Indecent Proposal (1993)",
    "Indiana Jones and the Kingdom of the Crystal Skull (2008)",
    "Insomnia (2002)",
    "Internal Affairs (1990)",
    "Interview with the Vampire (1994)",
    "Into the Blue (2005)",
    "Jack Frost (1998)",
    "Jeepers Creepers (2001)",
    "Jeepers Creepers 2 (2003)",
    "Jerry Maguire (1996)",
    "JFK (1991)",
    "Jumanji (1995)",
    "Jumper (2008)",
    "K-19: The Widowmaker (2002)",
    "K-PAX (2001)",
    "Kill Bill: Vol. 2 (2004)",
    "Killer Elite (2011)",
    "Killing the Shadows (2006)",
    "Kiss Kiss Bang Bang (2005)",
    "Kutsal Damacana (2007)",
    "L.A. Confidential (1997)",
    "Last Man Standing (1996)",
    "Law Abiding Citizen (2009)",
    "Lawrence of Arabia (1962)",
    "Leaving Las Vegas (1995)",
    "Legends of the Fall (1994)",
    "Les Misérables (1998)",
    "Lethal Weapon 4 (1998)",
    "Life Is a Miracle (2004)",
    "Limitless (2011)",
    "Little Buddha (1993)",
    "Little Children (2006)",
    "Little Fockers (2010)",
    "Live and Let Die (1973)",
    "Live Free or Die Hard (2007)",
    "Lord of War (2005)",
    "Lost Highway (1997)",
    "Lovelorn (2005)",
    "Lucky Number Slevin (2006)",
    "Machete (2010)",
    "Magic Carpet Ride (2005)",
    "Man of Fire (2021)",
    "Mary Reilly (1996)",
    "Mary Shelley's Frankenstein (1994)",
    "Mazi Kalbimde Yaradır (1970)",
    "Me Myself & Irene (2000)",
    "Meet the Fockers (2004)",
    "Meet the Parents (2000)",
    "Men in Black (1997)",
    "Men in Black 3 (2012)",
    "Men in Black II (2002)",
    "Million Dollar Baby (2004)",
    "Mindhunters (2004)",
    "Minority Report (2002)",
    "Mission: Impossible III (2006)",
    "Mongol: The Rise of Genghis Khan (2007)",
    "Moulin Rouge! (2001)",
    "Mr. & Mrs. Smith (2005)",
    "Murder by Numbers (2002)",
    "My World (2013)",
    "National Security (2003)",
    "Night of the Living Dead (1968)",
    "Noi the Albino (2003)",
    "Octopussy (1983)",
    "Old Dogs (2009)",
    "Oldboy (2003)",
    "One Missed Call (2003)",
    "One Night at McCool's (2001)",
    "Operation Pacific (1951)",
    "Osama (2003)",
    "Outland (1981)",
    "P.S. I Love You (2007)",
    "Panic Room (2002)",
    "Pan's Labyrinth (2006)",
    "Paranormal Activity (2007)",
    "Patch Adams (1998)",
    "Pathology (2008)",
    "Paycheck (2003)",
    "Pearl Harbor (2001)",
    "Perfect Stranger (2007)",
    "Pet Sematary II (1992)",
    "Peter Pan (2003)",
    "Planet Earth (2006)",
    "Planet Terror (2007)",
    "Platoon (1986)",
    "Poison Ivy (1992)",
    "Poltergeist (1982)",
    "Premonition (2007)",
    "Rambo (2008)",
    "Recep Ivedik (2008)",
    "Recep Ivedik 2 (2009)",
    "Recep Ivedik 3 (2010)",
    "Reservoir Dogs (1992)",
    "Resident Evil: Apocalypse (2004)",
    "Resident Evil: Extinction (2007)",
    "Revolver (2005)",
    "Rhapsody in August (1991)",
    "Riddick (2013)",
    "Rise of the Planet of the Apes (2011)",
    "Road to Perdition (2002)",
    "Road Trip (2000)",
    "Robin Hood (2010)",
    "Romeo + Juliet (1996)",
    "Romeo Must Die (2000)",
    "Rose Red (2002)",
    "RRRrrrr!!! (2004)",
    "Rumble Fish (1983)",
    "Runaway Bride (1999)",
    "Runaway Jury (2003)",
    "Safe House (2012)",
    "Salt (2010)",
    "Saving Private Ryan (1998)",
    "Saw II (2005)",
    "Scary Movie 4 (2006)",
    "Scream 4 (2011)",
    "Seed of Chucky (2004)",
    "Seven Pounds (2008)",
    "Shallow Hal (2001)",
    "Shaolin Soccer (2001)",
    "Sherlock Holmes (2009)",
    "Sherlock Holmes: A Game of Shadows (2011)",
    "Shine (1996)",
    "Shooter (2007)",
    "Signs (2002)",
    "Sin City (2005)",
    "Sleepers (1996)",
    "Sliding Doors (1998)",
    "Slumdog Millionaire (2008)",
    "Smokin' Aces (2006)",
    "Sneakers (1992)",
    "Something's Gotta Give (2003)",
    "Sommersby (1993)",
    "Source Code (2011)",
    "Sphere (1998)",
    "Spy Game (2001)",
    "Stargate (1994)",
    "Stealing Beauty (1996)",
    "Stepmom (1998)",
    "Stigmata (1999)",
    "Sunshine (1999)",
    "Taken (2008)",
    "Taken 2 (2012)",
    "Taking Lives (2004)",
    "Takva: A Man's Fear of God (2006)",
    "Taxi 2 (2000)",
    "Taxi 3 (2003)",
    "The 13th Warrior (1999)",
    "The Alamo (2004)",
    "The Animatrix (2003)",
    "The Astronaut's Wife (1999)",
    "The Avengers (1998)",
    "The Aviator (2004)",
    "The Barber of Siberia (1998)",
    "The Beach (2000)",
    "The Big Lebowski (1998)",
    "The Book of Eli (2010)",
    "The Break-Up (2006)",
    "The Breath (2009)",
    "The Bridge on the River Kwai (1957)",
    "The Butterfly Effect (2004)",
    "The Butterfly Effect 2 (2006)",
    "The Cowboys (1972)",
    "The Crimson Rivers (2000)",
    "The Curious Case of Benjamin Button (2008)",
    "The Da Vinci Code (2006)",
    "The Deer Hunter (1978)",
    "The Departed (2006)",
    "The Exorcism of Emily Rose (2005)",
    "The Expendables 2 (2012)",
    "The Family Man (2000)",
    "The Final Destination (2009)",
    "The Forbidden Kingdom (2008)",
    "The Fugitive (1993)",
    "The Game (1997)",
    "The Getaway (1972)",
    "The Girl Who Kicked the Hornet's Nest (2009)",
    "The Girl with the Dragon Tattoo (2011)",
    "The Godfather Part III (1990)",
    "The Green Mile (1999)",
    "The Grudge (2004)",
    "The Haunting (1999)",
    "The Heir Apparent: Largo Winch (2008)",
    "The Hitcher (2007)",
    "The Hunger Games (2012)",
    "The Hurt Locker (2008)",
    "The Illusionist (2006)",
    "The Incredible Hulk (2008)",
    "The Jacket (2005)",
    "The King's Speech (2010)",
    "The Lake House (2006)",
    "The League of Extraordinary Gentlemen (2003)",
    "The Legend of Suriyothai (2001)",
    "The Legend of Zorro (2005)",
    "The Life of Mammals (2002)",
    "The Magician (2006)",
    "The Magnificent Seven (1960)",
    "The Matrix (1999)",
    "The Matrix Reloaded (2003)",
    "The Matrix Revolutions (2003)",
    "The Merchant of Venice (2004)",
    "The Messenger: The Story of Joan of Arc (1999)",
    "The Mexican (2001)",
    "The Mists of Avalon (2001)",
    "The Model Solution (2002)",
    "The Next Three Days (2010)",
    "The Notebook (2004)",
    "The Omen (2006)",
    "The Perfect Storm (2000)",
    "The Portrait of a Lady (1996)",
    "The Possession (2012)",
    "The Postman (1997)",
    "The Professionals (1966)",
    "The Punisher (2004)",
    "The Pursuit of Happyness (2006)",
    "The Recruit (2003)",
    "The Ring (2002)",
    "The Ring Two (2005)",
    "The Score (2001)",
    "The Specialist (1994)",
    "The Taking of Pelham 1 2 3 (2009)",
    "The Texas Chain Saw Massacre (1974)",
    "The Tourist (2010)",
    "The Transporter (2002)",
    "The Twilight Saga: New Moon (2009)",
    "The Village (2004)",
    "Thelma & Louise (1991)",
    "Thir13en Ghosts (2001)",
    "Thor (2011)",
    "Three Colours: Red (1994)",
    "Three Colours: White (1994)",
    "Three Monkeys (2008)",
    "Thunderball (1965)",
    "Top Gun (1986)",
    "Torque (2004)",
    "Toss-Up (2004)",
    "Traffic (2000)",
    "Transformers: Dark of the Moon (2011)",
    "True Grit (2010)",
    "True Lies (1994)",
    "Turks in Space (2006)",
    "U Turn (1997)",
    "Ultraviolet (2006)",
    "Under Construction (2003)",
    "Underground (1995)",
    "Underworld (2003)",
    "Underworld: Awakening (2012)",
    "Underworld: Evolution (2006)",
    "Unknown (2011)",
    "Unleashed (2005)",
    "Urban Legend (1998)",
    "Urban Legends: Final Cut (2000)",
    "Vali (2009)",
    "Vanilla Sky (2001)",
    "Vantage Point (2008)",
    "Vertical Limit (2000)",
    "Vidocq (2001)",
    "Vizontele Tuuba (2004)",
    "Wag the Dog (1997)",
    "We Don't Live Here Anymore (2004)",
    "We Were Soldiers (2002)",
    "What Happened in Vegas (2017)",
    "Windtalkers (2002)",
    "Wrath of the Titans (2012)",
    "X2 (2003)",
    "xXx (2002)",
    "Yahşi Batı (2009)",
    "Yamakasi (2001)",
    "You Got Served (2004)",
    "You Me and Dupree (2006)",
    "…And God Created Woman (1956)",
]

# ================================
# 2) Letterboxd Top 250 listesi
# ================================
LETTERBOXD_TOP_LIST = [
    "Harakiri (1962)",
    "The Human Condition III: A Soldier's Prayer (1961)",
    "12 Angry Men (1957)",
    "Come and See (1985)",
    "Seven Samurai (1954)",
    "High and Low (1963)",
    "The Godfather Part II (1974)",
    "The Shawshank Redemption (1994)",
    "The Human Condition I: No Greater Love (1959)",
    "City of God (2002)",
    "The Lord of the Rings: The Return of the King (2003)",
    "Yi Yi (2000)",
    "Schindler's List (1993)",
    "Parasite (2019)",
    "The Godfather (1972)",
    "Ikiru (1952)",
    "Ran (1985)",
    "The Good, the Bad and the Ugly (1966)",
    "La Haine (1995)",
    "Le Trou (1960)",
    "Cinema Paradiso (1988)",
    "A Brighter Summer Day (1991)",
    "Autumn Sonata (1978)",
    "The Dark Knight (2008)",
    "The Human Condition II: Road to Eternity (1959)",
    "Grave of the Fireflies (1988)",
    "Neon Genesis Evangelion: The End of Evangelion (1997)",
    "Woman in the Dunes (1964)",
    "There Will Be Blood (2007)",
    "GoodFellas (1990)",
    "The Battle of Algiers (1966)",
    "The Cranes Are Flying (1957)",
    "Paths of Glory (1957)",
    "Spirited Away (2001)",
    "Andrei Rublev (1966)",
    "I Am Cuba (1964)",
    "Incendies (2010)",
    "Tokyo Story (1953)",
    "Apocalypse Now (1979)",
    "It's a Wonderful Life (1946)",
    "The Apartment (1960)",
    "Sunset Boulevard (1950)",
    "Interstellar (2014)",
    "The Ascent (1977)",
    "The Passion of Joan of Arc (1928)",
    "The Lord of the Rings: The Two Towers (2002)",
    "Sansho the Bailiff (1954)",
    "Fanny and Alexander (1982)",
    "Whiplash (2014)",
    "Mishima: A Life in Four Chapters (1985)",
    "Portrait of a Lady on Fire (2019)",
    "Memories of Murder (2003)",
    "Close-Up (1990)",
    "The Red Shoes (1948)",
    "Red Beard (1965)",
    "Nights of Cabiria (1957)",
    "Spider-Man: Across the Spider-Verse (2023)",
    "Nobody Knows (2004)",
    "Barry Lyndon (1975)",
    "Stalker (1979)",
    "Witness for the Prosecution (1957)",
    "The Pianist (2002)",
    "Do the Right Thing (1989)",
    "A Woman Under the Influence (1974)",
    "Life Is Beautiful (1997)",
    "The Empire Strikes Back (1980)",
    "Lawrence of Arabia (1962)",
    "Spider-Man: Into the Spider-Verse (2018)",
    "Eternity and a Day (1998)",
    "The Handmaiden (2016)",
    "Persona (1966)",
    "Princess Mononoke (1997)",
    "Once Upon a Time in the West (1968)",
    "Love Exposure (2008)",
    "Farewell My Concubine (1993)",
    "Perfect Blue (1997)",
    "The Lord of the Rings: The Fellowship of the Ring (2001)",
    "Satantango (1994)",
    "Paper Moon (1973)",
    "Scenes from a Marriage (1974)",
    "In the Mood for Love (2000)",
    "War and Peace (1967)",
    "The Voice of Hind Rajab (2025)",
    "An Elephant Sitting Still (2018)",
    "Dune: Part Two (2024)",
    "Where Is the Friend's House? (1987)",
    "Paris, Texas (1984)",
    "Sherlock Jr. (1924)",
    "A Separation (2011)",
    "Oldboy (2003)",
    "Apur Sansar (1959)",
    "Good Will Hunting (1997)",
    "One Flew Over the Cuckoo's Nest (1975)",
    "Rear Window (1954)",
    "It's Such a Beautiful Day (2012)",
    "Swing Girls (2004)",
    "Se7en (1995)",
    "Landscape in the Mist (1988)",
    "All About Eve (1950)",
    "Army of Shadows (1969)",
    "Inglourious Basterds (2009)",
    "The Wages of Fear (1953)",
    "Z (1969)",
    "Ordet (1955)",
    "Central Station (1998)",
    "Howl's Moving Castle (2004)",
    "Chainsaw Man – The Movie: Reze Arc (2025)",
    "Amadeus (1984)",
    "The Thing (1982)",
    "A Man Escaped (1956)",
    "Judgment at Nuremberg (1961)",
    "Singin' in the Rain (1952)",
    "How to Make Millions Before Grandma Dies (2024)",
    "All That Jazz (1979)",
    "Still Walking (2008)",
    "Raise the Red Lantern (1991)",
    "Three Colours: Red (1994)",
    "Late Spring (1949)",
    "A Special Day (1977)",
    "The Silence of the Lambs (1991)",
    "I'm Still Here (2024)",
    "Dead Poets Society (1989)",
    "The Departed (2006)",
    "To Be or Not to Be (1942)",
    "Monster (2023)",
    "Wild Strawberries (1957)",
    "City Lights (1931)",
    "The Seventh Seal (1957)",
    "The Great Dictator (1940)",
    "Funeral Parade of Roses (1969)",
    "Brief Encounter (1945)",
    "Mirror (1975)",
    "Taste of Cherry (1997)",
    "Das Boot (1981)",
    "Django Unchained (2012)",
    "Pather Panchali (1955)",
    "The Young Girls of Rochefort (1967)",
    "Prisoners (2013)",
    "Rocco and His Brothers (1960)",
    "Before Sunset (2004)",
    "The Celebration (1998)",
    "Mommy (2014)",
    "Tampopo (1985)",
    "The Best of Youth (2003)",
    "Twin Peaks: Fire Walk with Me (1992)",
    "No Country for Old Men (2007)",
    "Underground (1995)",
    "Psycho (1960)",
    "Werckmeister Harmonies (2000)",
    "Perfect Days (2023)",
    "Wings of Desire (1987)",
    "Dog Day Afternoon (1975)",
    "The 400 Blows (1959)",
    "Shoplifters (2018)",
    "Sing Sing (2023)",
    "Before Sunrise (1995)",
    "Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1964)",
    "Yojimbo (1961)",
    "Children of Men (2006)",
    "Chinatown (1974)",
    "Heat (1995)",
    "M (1931)",
    "Opening Night (1977)",
    "Fantastic Mr. Fox (2009)",
    "The Treasure of the Sierra Madre (1948)",
    "The Cremator (1969)",
    "The Sacrifice (1986)",
    "Samurai Rebellion (1967)",
    "The Elephant Man (1980)",
    "Bicycle Thieves (1948)",
    "Dersu Uzala (1975)",
    "The Lives of Others (2006)",
    "Children of Paradise (1945)",
    "The Father (2020)",
    "La Notte (1961)",
    "Terminator 2: Judgment Day (1991)",
    "Secrets & Lies (1996)",
    "The Man Who Shot Liberty Valance (1962)",
    "Evangelion: 3.0+1.0 Thrice Upon a Time (2021)",
    "The Hunt (2012)",
    "Nostalgia (1983)",
    "Chungking Express (1994)",
    "Puella Magi Madoka Magica the Movie Part III: Rebellion (2013)",
    "Akira (1988)",
    "Life, and Nothing More… (1992)",
    "8½ (1963)",
    "Azur & Asmar: The Princes' Quest (2006)",
    "We All Loved Each Other So Much (1974)",
    "Malcolm X (1992)",
    "The Iron Giant (1999)",
    "Ace in the Hole (1951)",
    "Casablanca (1942)",
    "Cure (1997)",
    "Throne of Blood (1957)",
    "The Prestige (2006)",
    "The Green Mile (1999)",
    "Some Like It Hot (1959)",
    "Look Back (2024)",
    "Who's Afraid of Virginia Woolf? (1966)",
    "Fail Safe (1964)",
    "Fight Club (1999)",
    "La Dolce Vita (1960)",
    "Ritual (2000)",
    "Rififi (1955)",
    "Jeanne Dielman, 23, quai du Commerce, 1080 Bruxelles (1975)",
    "Ugetsu (1953)",
    "Mary and Max (2009)",
    "Song of the Sea (2014)",
    "Sorcerer (1977)",
    "A Matter of Life and Death (1946)",
    "Network (1976)",
    "Modern Times (1936)",
    "Interstella 5555: The 5tory of the 5ecret 5tar 5ystem (2003)",
    "Aparajito (1956)",
    "Mulholland Drive (2001)",
    "The Night of the Hunter (1955)",
    "Double Indemnity (1944)",
    "The Tale of The Princess Kaguya (2013)",
    "Umberto D. (1952)",
    "2001: A Space Odyssey (1968)",
    "Everything Everywhere All at Once (2022)",
    "Il Sorpasso (1962)",
    "Winter Light (1963)",
    "Alien (1979)",
    "The Holdovers (2023)",
    "Saving Private Ryan (1998)",
    "The Face of Another (1966)",
    "The First Slam Dunk (2022)",
    "Kes (1969)",
    "Metropolis (1927)",
    "Anatomy of a Murder (1959)",
    "Sweet Smell of Success (1957)",
    "The Best Years of Our Lives (1946)",
    "Tokyo Godfathers (2003)",
    "The Bridge on the River Kwai (1957)",
    "Marcel the Shell with Shoes On (2021)",
    "The Third Man (1949)",
    "The Grand Budapest Hotel (2014)",
    "Pulp Fiction (1994)",
    "4 Months, 3 Weeks and 2 Days (2007)",
    "A Moment of Innocence (1996)",
    "Eternal Sunshine of the Spotless Mind (2004)",
    "Kwaidan (1964)",
    "The Disappearance of Haruhi Suzumiya (2010)",
    "Quo Vadis, Aida? (2020)",
    "Macario (1960)",
    "Son of the White Mare (1981)",
    "Nayakan (1987)",
    "Napoleon (1927)",
    "The King of Comedy (1982)",
]

# ================================
# 3) Rastgele Film Önerileri
# ================================
RANDOM_RECOMMENDATIONS = [
    "The Prestige (2006)",
    "Se7en (1995)",
    "Whiplash (2014)",
    "Interstellar (2014)",
    "Inception (2010)",
    "The Truman Show (1998)",
    "The Grand Budapest Hotel (2014)",
    "Prisoners (2013)",
    "Sicario (2015)",
    "Arrival (2016)",
    "Blade Runner (1982)",
    "Blade Runner 2049 (2017)",
    "The Thing (1982)",
    "Alien (1979)",
    "Aliens (1986)",
    "Heat (1995)",
    "Fight Club (1999)",
    "The Usual Suspects (1995)",
    "The Departed (2006)",
    "Oldboy (2003)",
    "City of God (2002)",
    "Spirited Away (2001)",
    "Princess Mononoke (1997)",
    "Your Name. (2016)",
    "Parasite (2019)",
    "The Handmaiden (2016)",
    "Django Unchained (2012)",
    "No Country for Old Men (2007)",
    "Mad Max: Fury Road (2015)",
    "The Wolf of Wall Street (2013)",
    "Goodfellas (1990)",
    "The Godfather (1972)",
    "The Shawshank Redemption (1994)",
    "The Dark Knight (2008)",
    "12 Angry Men (1957)",
    "The Matrix (1999)",
    "The Lord of the Rings: The Fellowship of the Ring (2001)",
    "The Lord of the Rings: The Return of the King (2003)",
    "Pulp Fiction (1994)",
    "The Green Mile (1999)",
    "The Silence of the Lambs (1991)",
    "Back to the Future (1985)",
    "Memento (2000)",
    "The Pianist (2002)",
    "American Beauty (1999)",
    "Amélie (2001)",
    "The Lives of Others (2006)",
    "Chernobyl (2019) [Mini Dizi]",
]


# ================================
# LİSTE METADATA (3 sabit liste)
# ================================
BUILTIN_LISTS = [
    {"id": "adnan_dvd", "name": "Adnan'ın DVD Listesi", "filename": "adnan_dvd.txt", "builtin": True},
    {"id": "letterboxd_top", "name": "Letterboxd Önerileri", "filename": "letterboxd_top.txt", "builtin": True},
    {"id": "random_picks", "name": "Rastgele Film Önerileri", "filename": "random_picks.txt", "builtin": True},
]


def load_lists_meta() -> dict:
    if not os.path.exists(LISTS_META_FILE):
        meta = {"lists": BUILTIN_LISTS, "selected": "adnan_dvd"}
        with open(LISTS_META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return meta
    with open(LISTS_META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_lists_meta(meta: dict) -> None:
    with open(LISTS_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def list_file_path(list_id: str, meta: dict) -> str:
    for it in meta["lists"]:
        if it["id"] == list_id:
            return os.path.join(LISTS_DIR, it["filename"])
    return os.path.join(LISTS_DIR, f"{list_id}.txt")


def ensure_builtin_lists(meta: dict) -> None:
    # Adnan'ın DVD listesi
    dvd_path = list_file_path("adnan_dvd", meta)
    if not os.path.exists(dvd_path) or not read_file(dvd_path):
        write_file(dvd_path, DEFAULT_DVD_LIST)

    # Letterboxd önerileri
    letterboxd_path = list_file_path("letterboxd_top", meta)
    if not os.path.exists(letterboxd_path) or not read_file(letterboxd_path):
        write_file(letterboxd_path, LETTERBOXD_TOP_LIST)

    # Rastgele film önerileri
    random_path = list_file_path("random_picks", meta)
    if not os.path.exists(random_path) or not read_file(random_path):
        write_file(random_path, RANDOM_RECOMMENDATIONS)


def remove_movie_from_all_lists(meta: dict, movie: str) -> None:
    """Bir film izlenenlere atılınca tüm listelerden otomatik silinir."""
    for it in meta["lists"]:
        p = os.path.join(LISTS_DIR, it["filename"])
        items = read_file(p)
        new_items = remove_ci(items, movie)
        if len(new_items) != len(items):
            write_file(p, new_items)


# ================================
# UYGULAMA
# ================================
class FilmSecApp(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.current_theme = "darkly"

        self.meta = load_lists_meta()
        ensure_builtin_lists(self.meta)

        # Puan ve notları yükle
        self.ratings = load_ratings()
        self.notes = load_notes()
        self.watch_dates = load_watch_dates()
        self.watch_history = load_watch_history()
        self.settings = load_settings()

        self.title("FilmSec")
        self.geometry("1120x650")
        self.minsize(980, 560)

        # ---------- ÜST BAR ----------
        top = tb.Frame(self, padding=(16, 14))
        top.pack(fill=X)

        tb.Label(top, text="🎬 FilmSec", font=("Segoe UI", 18, "bold")).pack(side=LEFT)

        self.count_badge = tb.Label(
            top,
            text="Liste: 0 | İzlenen: 0",
            bootstyle="secondary",
            padding=(10, 6),
            font=("Segoe UI", 10, "bold"),
        )
        self.count_badge.pack(side=RIGHT)

        # ---------- ANA ALAN ----------
        content = tb.Frame(self, padding=(16, 10))
        content.pack(fill=BOTH, expand=True)

        left = tb.Frame(content)
        left.pack(side=LEFT, fill=BOTH, expand=True)

        right = tb.Frame(content)
        right.pack(side=RIGHT, fill=Y, padx=(14, 0))

        lists_area = tb.Frame(left)
        lists_area.pack(fill=BOTH, expand=True)

        # ✅ Ayarlanabilir alan: Liste ↔ İzlenenler (sürüklenebilir ayırıcı)
        self.splitter = tb.Panedwindow(lists_area, orient=HORIZONTAL)
        self.splitter.pack(fill=BOTH, expand=True)

        # Sol panel: Liste
        pool_container = tb.Frame(self.splitter)
        self.pool_card = tb.Labelframe(pool_container, text="Liste", padding=12, bootstyle="info")
        self.pool_card.pack(fill=BOTH, expand=True)

        # Sağ panel: İzlenenler
        watched_container = tb.Frame(self.splitter)
        self.watched_card = tb.Labelframe(watched_container, text="İzlenenler", padding=12, bootstyle="warning")
        self.watched_card.pack(fill=BOTH, expand=True)

        # PanedWindow içine ekle (başlangıç oranı)
        self.splitter.add(pool_container, weight=1)
        self.splitter.add(watched_container, weight=1)

        watched_card = self.watched_card

        # --- Liste seçim barı ---
        bar = tb.Frame(self.pool_card)
        bar.pack(fill=X, pady=(0, 10))

        tb.Label(bar, text="Liste:", font=("Segoe UI", 10, "bold")).pack(side=LEFT)

        self.list_names = [it["name"] for it in self.meta["lists"]]
        self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}

        current_id = self.meta.get("selected", "adnan_dvd")
        current_name = next((it["name"] for it in self.meta["lists"] if it["id"] == current_id), self.meta["lists"][0]["name"])

        self.selected_list_var = tk.StringVar(value=current_name)
        self.list_combo = tb.Combobox(
            bar,
            textvariable=self.selected_list_var,
            values=self.list_names,
            state="readonly",
            width=26,
        )
        self.list_combo.pack(side=LEFT, padx=(8, 10))
        self.list_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change_list())

        tb.Button(bar, text="➕", bootstyle="success-outline", command=self.add_new_list, width=3).pack(side=LEFT, padx=(0, 5))
        tb.Button(bar, text="🗑", bootstyle="danger-outline", command=self.remove_current_list, width=3).pack(side=LEFT, padx=(0, 10))

        tb.Button(bar, text="✨ Yenilikler", bootstyle="secondary-outline", command=self.show_whats_new, width=12).pack(side=RIGHT, padx=(0, 8))
        tb.Button(bar, text="❓ Yardım", bootstyle="secondary-outline", command=self.show_help, width=10).pack(side=RIGHT)

        # --- Listbox + scrollbar (seçili listenin içi) ---
        pool_wrap = tb.Frame(self.pool_card)
        pool_wrap.pack(fill=BOTH, expand=True)

        pool_scroll = tb.Scrollbar(pool_wrap, orient=VERTICAL)
        pool_scroll.pack(side=RIGHT, fill=Y)

        self.pool_list = tk.Listbox(
            pool_wrap,
            font=("Segoe UI", 10),
            activestyle="none",
            highlightthickness=0,
            selectborderwidth=0,
        )
        self.pool_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.pool_list.config(yscrollcommand=pool_scroll.set)
        pool_scroll.config(command=self.pool_list.yview)

        # --- İzlenen listbox + scrollbar ---
        watched_wrap = tb.Frame(watched_card)
        watched_wrap.pack(fill=BOTH, expand=True)

        watched_scroll = tb.Scrollbar(watched_wrap, orient=VERTICAL)
        watched_scroll.pack(side=RIGHT, fill=Y)

        self.watched_list = tk.Listbox(
            watched_wrap,
            font=("Segoe UI", 10),
            activestyle="none",
            highlightthickness=0,
            selectborderwidth=0,
        )
        self.watched_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.watched_list.config(yscrollcommand=watched_scroll.set)
        watched_scroll.config(command=self.watched_list.yview)

        # ---------- INFO ----------
        self.info = tb.Label(
            left,
            text="Hazır. Bir işlem seç 🙂",
            bootstyle="secondary",
            padding=(12, 10),
            font=("Segoe UI", 11),
            anchor=W,
        )
        self.info.pack(fill=X, pady=(12, 0))

        # ---------- SAĞ PANEL ----------
                # ---------- POSTER (AFİŞ) ----------
        self.poster_card = tb.Labelframe(right, text="Afiş", padding=10, bootstyle="secondary")
        self.poster_card.pack(fill=X, pady=(0, 10))

        self.poster_title_var = tk.StringVar(value="")
        tb.Label(
            self.poster_card,
            textvariable=self.poster_title_var,
            font=("Segoe UI", 9, "bold"),
            wraplength=260,
            justify=LEFT,
        ).pack(anchor=W, pady=(0, 6))

        # Görsel alan 
        self.poster_img_label = tb.Label(
            self.poster_card,
            text="🎬 Bir film seç",
            bootstyle="secondary",
            anchor=CENTER,
            padding=6,
        )
        self.poster_img_label.pack(fill=X)
        self.poster_photo = None  

        tb.Button(
            self.poster_card,
            text="🔑 TMDb",
            bootstyle="secondary-outline",
            command=self.set_tmdb_key,
            width=10,
        ).pack(anchor=E, pady=(8, 0))

        panel = tb.Labelframe(right, text="Kontroller", padding=14, bootstyle="secondary")
        panel.pack(fill=Y)

        btn = {"width": 26, "padding": (10, 10)}

        tb.Button(panel, text="🎲 Rastgele Seç", command=self.pick_movie_popup, bootstyle="success", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="➕ Film Ekle", command=self.add_movie, bootstyle="primary", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="🔍 Film Ara", command=self.search_movie, bootstyle="info", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="↔ Liste ⇄ İzlenenlere Taşı", command=self.toggle_move_selected, bootstyle="warning", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="🗑 Seçileni Kaldır", command=self.delete_selected_anywhere, bootstyle="danger", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="📂 Veri Klasörünü Aç", command=self.open_data_dir, bootstyle="secondary", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="🌓 Mod Değiştir (Light/Dark)", command=self.toggle_theme, bootstyle="secondary", **btn).pack(fill=X, pady=(0, 10))
        tb.Button(panel, text="❌ Çıkış", command=self.destroy, bootstyle="secondary-outline", **btn).pack(fill=X, pady=(6, 0))

        # ---------- EVENTLAR ----------
        self.pool_list.bind("<<ListboxSelect>>", lambda e: self._on_select("pool"))
        self.watched_list.bind("<<ListboxSelect>>", lambda e: self._on_select("watched"))

        self.pool_list.bind("<Double-Button-1>", lambda e: self._on_double_click("pool"))
        self.watched_list.bind("<Double-Button-1>", lambda e: self._on_double_click("watched"))

        # Sürükle-bırak eventları
        self.pool_list.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, "pool"))
        self.pool_list.bind("<B1-Motion>", self._on_drag_motion)
        self.pool_list.bind("<ButtonRelease-1>", lambda e: self._on_drag_drop(e, "pool"))
        
        self.watched_list.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, "watched"))
        self.watched_list.bind("<B1-Motion>", self._on_drag_motion)
        self.watched_list.bind("<ButtonRelease-1>", lambda e: self._on_drag_drop(e, "watched"))
        
        self.drag_data = {"item": None, "source": None, "x": 0, "y": 0}
        
        self.drag_label = None

        self.apply_listbox_theme()
        self.refresh_lists()

        try:
            self.after(150, lambda: self.splitter.sashpos(0, int(self.winfo_width() * 0.5)))
        except Exception:
            pass

        
        if self.settings.get("first_launch", True):
            self.settings["first_launch"] = False
            save_settings(self.settings)

        self._set_info("💡 İpucu: Filmlere puan ve not vermek için çift tıklayın!", "info")
        self.after(5000, lambda: self._set_info("Hazır. Bir işlem seç 🙂", "secondary"))

    # ================================
    # Yardım
    # ================================
    def show_help(self):
        text = (
            "🎬 Film Seçici - Kısa Kullanım\n\n"
            "• Üstteki listeden hangi film listesini görmek istediğini seç.\n"
            "• 🎲 Rastgele Seç: Bir film önerir. 'Evet' dersen izlenenlere taşır ve tüm listelerden düşer.\n"
            "• ➕ Film Ekle: Film adını yazarsın, hangi listeye eklemek istediğini sorar.\n"
            "• 🔍 Film Ara: Havuzda (seçili listede) veya izlenenlerde arar.\n"
            "• ↔ Taşı: Seçili filmi liste ile izlenenler arasında taşır.\n"
            "• 🗑 Kaldır: Seçili filmi bulunduğu yerden tamamen siler.\n\n"
            "⭐ YENİ ÖZELLİK - Puan ve Not:\n"
            "• Herhangi bir filme ÇIFT TIKLA!\n"
            "• Açılan pencereden 0-10 arası puan verebilirsin\n"
            "• İstersen notlar ekleyebilirsin\n"
            "• Puanlar film adının yanında ⭐ ile görünür\n"
            "• Notlu filmler 📝 işareti ile gösterilir\n\n"
            "3 Film Listesi:\n"
            "- Adnan'ın DVD Listesi: Kişisel DVD koleksiyonu\n"
            "- Letterboxd Önerileri: Letterboxd'dan seçilmiş filmler\n"
            "- Rastgele Film Önerileri: Çeşitli öneriler"
        )
        messagebox.showinfo("Yardım", text)

    
    def show_whats_new(self):
        """Yeni özellikler penceresini aç (kullanıcı isterse)."""
        win = tb.Toplevel(self)
        win.title("✨ Yenilikler")
        win.geometry("520x420")
        win.minsize(480, 360)
        win.transient(self)

        header = tb.Frame(win, bootstyle="primary", padding=18)
        header.pack(fill=X)
        tb.Label(
            header,
            text="✨ Yeni Özellikler",
            font=("Segoe UI", 14, "bold"),
            bootstyle="inverse-primary",
        ).pack()

        content = tb.Frame(win, padding=18)
        content.pack(fill=BOTH, expand=True)

        info_text = (
            "⭐ Puan & Not Sistemi\n"
            "• Herhangi bir filme ÇİFT TIKLA\n"
            "• 0-10 arası puan ver\n"
            "• Not ekle, düşüncelerini kaydet\n\n"
            "🖱️ Daha Kolay Puanlama\n"
            "• Yıldızlara tıklayarak da puan verebilirsin\n"
            "• Puanlar 0.5 adım ile artar (3.5 gibi)\n\n"
            "📌 Diğer\n"
            "• İzlenenlere atılan film tüm listelerden düşer\n"
            "• Sürükle-bırak ile taşıma desteklenir"
        )

        tb.Label(
            content,
            text=info_text,
            font=("Segoe UI", 10),
            justify=LEFT,
            wraplength=470,
        ).pack(anchor=W)

        btn_frame = tb.Frame(win, padding=(18, 12))
        btn_frame.pack(fill=X)

        tb.Button(btn_frame, text="Kapat", bootstyle="secondary", command=win.destroy, width=12).pack(side=RIGHT)
    def show_first_launch_info(self):
            """İlk açılışta yeni özellikler hakkında bilgi göster"""
            info_win = tb.Toplevel(self)
            info_win.title("🎉 Yeni Özellikler!")
            info_win.geometry("500x400")
            info_win.transient(self)
            info_win.grab_set()

            # İkon ve başlık
            header = tb.Frame(info_win, bootstyle="primary", padding=20)
            header.pack(fill=X)

            tb.Label(
                header,
                text="🎉 FilmSec'e Hoş Geldiniz!",
                font=("Segoe UI", 16, "bold"),
                bootstyle="inverse-primary"
            ).pack()

            # İçerik
            content = tb.Frame(info_win, padding=20)
            content.pack(fill=BOTH, expand=True)

            info_text = (
                "Artık filmlerinize puan ve not ekleyebilirsiniz!\n\n"
                "⭐ PUAN VERMEk:\n"
                "• Herhangi bir filme ÇIFT TIKLAYIN\n"
                "• 0-10 arası puan verin\n"
                "• Puanlar film adının yanında görünür\n\n"
                "📝 NOT EKLEMEK:\n"
                "• Aynı pencerede notunuzu yazın\n"
                "• Düşüncelerinizi, izleme tarihini vs. ekleyin\n"
                "• Notlu filmler 📝 işareti ile gösterilir\n\n"
                "💡 İPUCU:\n"
                "Hem havuz listelerinde hem de izlenenlerde\n"
                "tüm filmlere puan ve not ekleyebilirsiniz!"
            )

            tb.Label(
                content,
                text=info_text,
                font=("Segoe UI", 10),
                justify=LEFT,
                wraplength=450
            ).pack(pady=10)

            # Checkbox - bir daha gösterme
            self.dont_show_var = tk.BooleanVar(value=False)
            tb.Checkbutton(
                content,
                text="Bu mesajı bir daha gösterme",
                variable=self.dont_show_var,
                bootstyle="primary-round-toggle"
            ).pack(pady=10)

            # Butonlar
            btn_frame = tb.Frame(info_win, padding=10)
            btn_frame.pack(fill=X)

            def close_info():
                if self.dont_show_var.get():
                    self.settings["first_launch"] = False
                    save_settings(self.settings)
                info_win.destroy()
                # İlk 5 saniye ipucu göster
                self._set_info("💡 İpucu: Filmlere puan ve not vermek için çift tıklayın!", "info")
                self.after(5000, lambda: self._set_info("Hazır. Bir işlem seç 🙂", "secondary"))

            tb.Button(
                btn_frame,
                text="Anladım, Başlayalım! 🚀",
                bootstyle="success",
                command=close_info,
                width=30
            ).pack()

    # ================================
    # UI yardımcıları
    # ================================
    def _set_info(self, text: str, style: str = "secondary"):
        self.info.configure(text=text, bootstyle=style)

    def current_list_id(self) -> str:
        name = self.selected_list_var.get().strip()
        return self.list_id_by_name.get(name, "adnan_dvd")

    def current_list_path(self) -> str:
        return list_file_path(self.current_list_id(), self.meta)

    def _update_counts(self):
        pool = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)
        pool_visible = [m for m in pool if not contains_ci(watched, m)]
        self.count_badge.configure(text=f"Liste: {len(pool_visible)} | İzlenen: {len(watched)}")

        self.pool_card.configure(text=f"Liste: {self.selected_list_var.get()}")

    def refresh_lists(self):
        pool = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)

        pool = [m for m in pool if not contains_ci(watched, m)]
        pool.sort(key=str.lower)

        self.pool_list.delete(0, tk.END)
        for m in pool:
            display_text = self._format_movie_display(m)
            self.pool_list.insert(tk.END, display_text)

        self.watched_list.delete(0, tk.END)
        for m in watched:
            display_text = self._format_movie_display(m)
            self.watched_list.insert(tk.END, display_text)

        self._update_counts()

    def _format_movie_display(self, movie: str) -> str:
        """Film adını puan, izlenme tarihi ve not ikonlarıyla formatla"""
        movie_key = get_movie_key(movie)
        display = movie
        
        # Puan varsa ekle
        if movie_key in self.ratings:
            rating = self.ratings[movie_key]
            display += f" ⭐ {rating}"
        
        # İzlenme tarihi varsa ekle (sadece son izlenme)
        if movie_key in self.watch_dates and self.watch_dates[movie_key]:
            last_watch = self.watch_dates[movie_key][-1]
            display += f" 📅 {last_watch}"
        
        # Not varsa ikon ekle
        if movie_key in self.notes and self.notes[movie_key].strip():
            display += " 📝"
        
        return display

    def on_change_list(self):
        self.meta["selected"] = self.current_list_id()
        save_lists_meta(self.meta)
        self.refresh_lists()
        self._set_info(f"📁 Liste seçildi: {self.selected_list_var.get()}", "info")

    # ================================
    # Sürükle-Bırak İşlemleri
    # ================================
    def _on_drag_start(self, event, source):
        """Sürükleme başladığında"""
        widget = event.widget
        index = widget.nearest(event.y)
        
        if index >= 0 and index < widget.size():
            self.drag_data["item"] = widget.get(index)
            self.drag_data["source"] = source
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)
            
            # Görsel sürükleme elemanı oluştur
            self._create_drag_label(event)

    def _create_drag_label(self, event):
        """Sürükleme sırasında gösterilecek label oluştur"""
        if self.drag_label:
            self.drag_label.destroy()
        
        # Film adını kısalt (çok uzunsa)
        movie_text = self.drag_data["item"]
        if len(movie_text) > 50:
            movie_text = movie_text[:47] + "..."
        
        # Toplevel pencere oluştur (üstte kalması için)
        self.drag_label = tk.Toplevel(self)
        self.drag_label.wm_overrideredirect(True)  # Başlık çubuğu yok
        self.drag_label.wm_attributes("-alpha", 0.8)  # Yarı saydam
        self.drag_label.wm_attributes("-topmost", True)  # Her zaman üstte
        
        # Label içeriği
        label = tb.Label(
            self.drag_label,
            text=f"🎬 {movie_text}",
            bootstyle="info",
            padding=10,
            font=("Segoe UI", 10, "bold")
        )
        label.pack()
        
        # Pozisyonu ayarla
        self.drag_label.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _on_drag_motion(self, event):
        """Sürüklerken - label'ı hareket ettir"""
        if self.drag_label and self.drag_data["item"]:
            self.drag_label.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _on_drag_drop(self, event, source):
        """Bırakıldığında"""
        # Sürükleme label'ını kaldır
        if self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None
        
        if not self.drag_data["item"] or not self.drag_data["source"]:
            return
        
        # Fare pozisyonunu kontrol et - karşı listeye bırakıldı mı?
        drop_target = None
        
        # Pool list'in konumunu al
        pool_x = self.pool_list.winfo_rootx()
        pool_y = self.pool_list.winfo_rooty()
        pool_w = self.pool_list.winfo_width()
        pool_h = self.pool_list.winfo_height()
        
        # Watched list'in konumunu al
        watched_x = self.watched_list.winfo_rootx()
        watched_y = self.watched_list.winfo_rooty()
        watched_w = self.watched_list.winfo_width()
        watched_h = self.watched_list.winfo_height()
        
        # Fare pozisyonu (root koordinatları)
        mouse_x = event.x_root
        mouse_y = event.y_root
        
        # Hangi liste üzerine bırakıldı kontrol et
        if pool_x <= mouse_x <= pool_x + pool_w and pool_y <= mouse_y <= pool_y + pool_h:
            drop_target = "pool"
        elif watched_x <= mouse_x <= watched_x + watched_w and watched_y <= mouse_y <= watched_y + watched_h:
            drop_target = "watched"
        
        # Farklı listeye bırakıldıysa taşı
        if drop_target and drop_target != self.drag_data["source"]:
            movie = self.drag_data["item"]
            original_movie = self._extract_original_movie_name(movie)
            
            watched = read_file(WATCHED_FILE)
            
            if self.drag_data["source"] == "pool" and drop_target == "watched":
                # Havuzdan izlenenlere taşı
                if not contains_ci(watched, original_movie):
                    watched.append(original_movie)
                    write_file(WATCHED_FILE, watched)
                    
                    # İzlenme tarihini kaydet
                    self.watch_dates = add_watch_date(original_movie, self.watch_dates)
                    save_watch_dates(self.watch_dates)
                    
                    # Hangi listeden eklendiğini kaydet
                    current_list_id = self.current_list_id()
                    self.watch_history = add_to_watch_history(original_movie, current_list_id, self.watch_history)
                    save_watch_history(self.watch_history)
                
                remove_movie_from_all_lists(self.meta, original_movie)
                self.refresh_lists()
                self._set_info(f"✅ '{original_movie}' izlenenlere taşındı", "success")
                
            elif self.drag_data["source"] == "watched" and drop_target == "pool":
                # İzlenenlerden havuza taşı
                watched = remove_ci(watched, original_movie)
                write_file(WATCHED_FILE, watched)
                
                p = self.current_list_path()
                items = read_file(p)
                if not contains_ci(items, original_movie):
                    items.append(original_movie)
                    write_file(p, items)
                
                self.refresh_lists()
                self._set_info(f"↩ '{original_movie}' seçili listeye geri eklendi", "info")
        
        self.drag_data = {"item": None, "source": None, "x": 0, "y": 0}

    def _on_select(self, which: str):
        if which == "pool":
            if self.pool_list.curselection():
                self.watched_list.selection_clear(0, tk.END)
        else:
            if self.watched_list.curselection():
                self.pool_list.selection_clear(0, tk.END)
        # Seçili filme göre afişi güncelle
        self.update_poster_from_selection()


    def _on_double_click(self, which: str):
        movie = self._get_selected(which)
        if movie:
            # Formatlanmış metinden asıl film adını çıkar
            original_movie = self._extract_original_movie_name(movie)
            self.open_rating_note_popup(original_movie)

    def _get_selected(self, which: str):
        lb = self.pool_list if which == "pool" else self.watched_list
        sel = lb.curselection()
        if not sel:
            return None
        return lb.get(sel[0])

    def _get_selected_anywhere(self):
        movie_pool = self._get_selected("pool")
        if movie_pool:
            return "pool", movie_pool
        movie_watched = self._get_selected("watched")
        if movie_watched:
            return "watched", movie_watched
        return None, None

    
    def update_poster_from_selection(self):
        """Hangi listede seçim varsa o filme göre afişi güncelle."""
        which, movie = self._get_selected_anywhere()
        if not which or not movie:
            # seçim yoksa temizle
            self.poster_title_var.set("")
            self.poster_img_label.configure(image="", text="🎬 Bir film seç")
            self.poster_photo = None
            return

        original_movie = self._extract_original_movie_name(movie)
        self.update_poster_preview(original_movie)

    def _extract_original_movie_name(self, display_text: str) -> str:
        """Formatlanmış metinden orijinal film adını çıkar

        Not: Listbox'ta film adının sonuna şu eklentiler gelebiliyor:
        - ' ⭐ <puan>'
        - ' 📅 <tarih>'
        - ' 📝'
        Bu fonksiyon her durumda saf film adını döndürür.
        """
        clean = display_text
        for marker in (" ⭐", " 📅", " 📝"):
            if marker in clean:
                clean = clean.split(marker)[0]
        return clean.strip()

    # ================================
    # Puan ve Not Popup
    # ================================
    def open_rating_note_popup(self, movie: str):
        """Film için puan ve not girişi popup'ı aç"""
        movie_key = get_movie_key(movie)
        
        popup = tb.Toplevel(self)
        popup.title("⭐ Puan & Not")
        popup.geometry("650x620")
        popup.minsize(620, 560)
        popup.transient(self)
        popup.grab_set()

        # Başlık
        header = tb.Frame(popup, bootstyle="info", padding=15)
        header.pack(fill=X)
        
        tb.Label(
            header,
            text=movie,
            font=("Segoe UI", 13, "bold"),
            bootstyle="inverse-info",
            wraplength=500
        ).pack()

        content = tb.Frame(popup, padding=20)
        content.pack(fill=BOTH, expand=True)

        # PUAN KISMI
        rating_frame = tb.Labelframe(content, text="⭐ Puan (0-10)", padding=15, bootstyle="warning")
        rating_frame.pack(fill=X, pady=(0, 15))

        current_rating = self.ratings.get(movie_key, 0.0)
        try:
            current_rating = round(float(current_rating) * 2) / 2
        except Exception:
            current_rating = 0.0

        rating_var = tk.DoubleVar(value=current_rating)
        rating_label_var = tk.StringVar(value=f"{current_rating:.1f}")

        def snap_to_half(val: float) -> float:
            """Puanı 0.5 adımlara sabitle."""
            try:
                v = float(val)
            except Exception:
                v = 0.0
            return round(v * 2) / 2

        def update_rating_label(val):
            snapped = snap_to_half(val)
            if abs(rating_var.get() - snapped) > 1e-9:
                rating_var.set(snapped)
            rating_label_var.set(f"{snapped:.1f}")

        # Slider
        slider = tb.Scale(
            rating_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=rating_var,
            command=update_rating_label,
            bootstyle="warning"
        )
        slider.pack(fill=X, pady=(0, 10))

        # Puan göstergesi
        rating_display = tb.Label(
            rating_frame,
            textvariable=rating_label_var,
            font=("Segoe UI", 24, "bold"),
            bootstyle="warning"
        )
        rating_display.pack()

        # Yıldız gösterimi
        stars_label = tb.Label(
            rating_frame,
            text="",
            font=("Segoe UI", 20),
            cursor="hand2",
        )
        stars_label.pack(pady=(6, 0))
        def update_stars(*args):
            val = snap_to_half(rating_var.get())
            if abs(rating_var.get() - val) > 1e-9:
                rating_var.set(val)
        
            full_stars = int(val)
            half_star = 1 if (val - full_stars) >= 0.5 else 0
            empty_stars = 10 - full_stars - half_star
        
            # Puan sembolleri
            stars = "★" * full_stars
            if half_star:
                stars += "⯨"  
            stars += "☆" * empty_stars
        
            stars_label.config(text=stars)

        rating_var.trace_add("write", update_stars)
        update_stars()

        def set_rating_by_click(event):
            """Yıldızların üstüne tıklayarak puan ver (0.5 adım)."""
            w = stars_label.winfo_width()
            if w <= 0:
                return
            x = max(0, min(event.x, w))
            ratio = x / w
            raw = ratio * 10  # 0-10
            snapped = snap_to_half(raw)
            rating_var.set(snapped)
            rating_label_var.set(f"{snapped:.1f}")

        stars_label.bind("<Button-1>", set_rating_by_click)

        # NOT KISMI
        note_frame = tb.Labelframe(content, text="📝 Not / Yorum", padding=15, bootstyle="info")
        note_frame.pack(fill=BOTH, expand=True, pady=(0, 15))

        # İzlenme tarihleri varsa göster
        if movie_key in self.watch_dates and self.watch_dates[movie_key]:
            dates_text = ", ".join(self.watch_dates[movie_key])
            tb.Label(
                note_frame,
                text=f"📅 İzlenme: {dates_text}",
                font=("Segoe UI", 9),
                bootstyle="success",
                wraplength=450
            ).pack(anchor=W, pady=(0, 8))

        current_note = self.notes.get(movie_key, "")

        note_scroll = tb.Scrollbar(note_frame)
        note_scroll.pack(side=RIGHT, fill=Y)

        note_text = tk.Text(
            note_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            height=6,
            yscrollcommand=note_scroll.set
        )
        note_text.pack(side=LEFT, fill=BOTH, expand=True)
        note_scroll.config(command=note_text.yview)

        if current_note:
            note_text.insert("1.0", current_note)

        # BUTONLAR
        btn_frame = tb.Frame(popup, padding=10)
        btn_frame.pack(fill=X)

        def save_data():
            # Puanı kaydet
            new_rating = snap_to_half(rating_var.get())
            if new_rating > 0:
                self.ratings[movie_key] = new_rating
            elif movie_key in self.ratings:
                del self.ratings[movie_key]
            
            save_ratings(self.ratings)

            # Notu kaydet
            new_note = note_text.get("1.0", tk.END).strip()
            if new_note:
                self.notes[movie_key] = new_note
            elif movie_key in self.notes:
                del self.notes[movie_key]
            
            save_notes(self.notes)

            popup.destroy()
            self.refresh_lists()
            
            if new_rating > 0 or new_note:
                self._set_info(f"✅ '{movie}' için puan ve not kaydedildi!", "success")
            else:
                self._set_info(f"ℹ️ '{movie}' için veriler temizlendi", "info")

        def clear_data():
            if messagebox.askyesno("Onay", "Bu film için tüm puan ve notları silmek istiyor musunuz?"):
                if movie_key in self.ratings:
                    del self.ratings[movie_key]
                    save_ratings(self.ratings)
                
                if movie_key in self.notes:
                    del self.notes[movie_key]
                    save_notes(self.notes)
                
                popup.destroy()
                self.refresh_lists()
                self._set_info(f"🗑 '{movie}' için tüm veriler silindi", "warning")

        tb.Button(
            btn_frame,
            text="💾 Kaydet",
            bootstyle="success",
            command=save_data,
            width=15
        ).pack(side=LEFT, padx=5)

        tb.Button(
            btn_frame,
            text="❌ İptal",
            bootstyle="secondary",
            command=popup.destroy,
            width=15
        ).pack(side=LEFT, padx=5)

        tb.Button(
            btn_frame,
            text="🗑 Temizle",
            bootstyle="danger",
            command=clear_data,
            width=15
        ).pack(side=LEFT, padx=5)

    def _select_movie_in_pool(self, movie: str):
        try:
            self.pool_list.selection_clear(0, tk.END)
            self.watched_list.selection_clear(0, tk.END)

            pool_now = read_file(self.current_list_path())
            watched = read_file(WATCHED_FILE)
            pool_now = [m for m in pool_now if not contains_ci(watched, m)]

            for i, m in enumerate(pool_now):
                if normalize_movie(m) == normalize_movie(movie):
                    self.pool_list.selection_set(i)
                    self.pool_list.see(i)
                    break
        except Exception:
            pass

    # ================================
    # Light/Dark Toggle + Listbox tema
    # ================================
    def toggle_theme(self):
        self.current_theme = "darkly" if self.current_theme == "flatly" else "flatly"
        self.style.theme_use(self.current_theme)
        self.apply_listbox_theme()
        self.refresh_lists()
        self._set_info(f"🌓 Mod değişti: {self.current_theme}", "secondary")

    def apply_listbox_theme(self):
        if self.current_theme == "darkly":
            bg = "#1f2328"
            fg = "#ffffff"
            selbg = "#3b82f6"
        else:
            bg = "#ffffff"
            fg = "#111827"
            selbg = "#93c5fd"

        self.pool_list.config(bg=bg, fg=fg, selectbackground=selbg, selectforeground=fg)
        self.watched_list.config(bg=bg, fg=fg, selectbackground=selbg, selectforeground=fg)

    # ================================
    # Rastgele Seçim (popup)
    # ================================
    def pick_movie_popup(self):
        pool_all = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)
        pool = [m for m in pool_all if not contains_ci(watched, m)]

        if not pool:
            self._set_info("Bu listede izlenmemiş film kalmamış 🙂", "warning")
            messagebox.showinfo("Bilgi", "Bu listede izlenmemiş film kalmamış.")
            return

        movie = random.choice(pool)
        answer = messagebox.askyesno("Film Önerisi", f"🎲 Tavsiye: {movie}\n\nŞimdi izleyecek misin?")
        if answer:
            watched = read_file(WATCHED_FILE)
            if not contains_ci(watched, movie):
                watched.append(movie)
                write_file(WATCHED_FILE, watched)
                
                # İzlenme tarihini kaydet
                self.watch_dates = add_watch_date(movie, self.watch_dates)
                save_watch_dates(self.watch_dates)
                
                # Hangi listeden eklendiğini kaydet
                current_list_id = self.current_list_id()
                self.watch_history = add_to_watch_history(movie, current_list_id, self.watch_history)
                save_watch_history(self.watch_history)

            remove_movie_from_all_lists(self.meta, movie)

            self.refresh_lists()
            self._set_info(f"✅ '{movie}' izlenenlere aktarıldı. İyi seyirler! 🍿", "success")
        else:
            self._set_info(f"🙂 Tamamdır. Tavsiye: {movie} (Listede kaldı)", "secondary")
            self._select_movie_in_pool(movie)

    # ================================
    # Film Ekle (hangi listeye?)
    # ================================
    def add_movie(self):
        new_movie = simpledialog.askstring("Film Ekle", "Eklemek istediğiniz filmin adını yazın:")
        if not new_movie:
            return
        new_movie = new_movie.strip()
        if not new_movie:
            return

        watched = read_file(WATCHED_FILE)
        if contains_ci(watched, new_movie):
            messagebox.showinfo("Bilgi", "Bu film izlenenlerde var. Listeye eklemeye gerek yok 🙂")
            return

        list_choice = tb.Toplevel(self)
        list_choice.title("Liste Seç")
        list_choice.geometry("360x220")
        list_choice.transient(self)
        list_choice.grab_set()

        tb.Label(list_choice, text="Bu filmi hangi listeye ekleyelim?", padding=(10, 10)).pack()

        var = tk.StringVar(value=self.selected_list_var.get())
        cb = tb.Combobox(list_choice, values=self.list_names, textvariable=var, state="readonly", width=28)
        cb.pack(pady=8)

        def do_add():
            target_name = var.get()
            target_id = self.list_id_by_name.get(target_name)
            if not target_id:
                return

            for it in self.meta["lists"]:
                p = os.path.join(LISTS_DIR, it["filename"])
                items = read_file(p)
                if contains_ci(items, new_movie):
                    messagebox.showinfo("Bilgi", f"Bu film zaten '{it['name']}' listesinde var.")
                    list_choice.destroy()
                    return

            p = list_file_path(target_id, self.meta)
            items = read_file(p)
            items.append(new_movie)
            write_file(p, items)

            self.refresh_lists()
            self._set_info(f"➕ '{new_movie}' eklendi: {target_name}", "success")
            list_choice.destroy()

        tb.Button(list_choice, text="Ekle", bootstyle="success", command=do_add, width=10).pack(pady=(12, 6))
        tb.Button(list_choice, text="İptal", bootstyle="secondary", command=list_choice.destroy, width=10).pack()

    # ================================
    # Film Ara
    # ================================
    def search_movie(self):
        query = simpledialog.askstring("Film Ara", "Aramak istediğiniz kelime/film adı:")
        if not query:
            return
        q = query.strip().lower()
        if not q:
            return

        pool_all = read_file(self.current_list_path())
        watched = read_file(WATCHED_FILE)

        pool_results = [m for m in pool_all if q in m.lower() and not contains_ci(watched, m)]
        watched_results = [m for m in watched if q in m.lower()]

        if not pool_results and not watched_results:
            messagebox.showinfo("Arama Sonuçları", "Sonuç bulunamadı.")
            return

        win = tb.Toplevel(self)
        win.title("Arama Sonuçları")
        win.geometry("580x440")
        win.transient(self)
        win.grab_set()

        tb.Label(win, text="Bir filme çift tıkla: ana listede seçili olsun.", padding=(10, 10)).pack()

        container = tb.Frame(win, padding=10)
        container.pack(fill=BOTH, expand=True)

        lf_pool = tb.Labelframe(container, text=f"Seçili Liste: {self.selected_list_var.get()}", padding=10, bootstyle="info")
        lf_pool.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        lb_pool = tk.Listbox(lf_pool, font=("Segoe UI", 10), activestyle="none", highlightthickness=0)
        lb_pool.pack(fill=BOTH, expand=True)
        for m in pool_results:
            lb_pool.insert(tk.END, m)

        lf_w = tb.Labelframe(container, text="İzlenenler", padding=10, bootstyle="warning")
        lf_w.pack(side=LEFT, fill=BOTH, expand=True)

        lb_w = tk.Listbox(lf_w, font=("Segoe UI", 10), activestyle="none", highlightthickness=0)
        lb_w.pack(fill=BOTH, expand=True)
        for m in watched_results:
            lb_w.insert(tk.END, m)

        def select_in_main(which: str, movie: str):
            if which == "pool":
                self.watched_list.selection_clear(0, tk.END)
                self.pool_list.selection_clear(0, tk.END)

                pool_visible = [m for m in read_file(self.current_list_path()) if not contains_ci(read_file(WATCHED_FILE), m)]
                for i, mm in enumerate(pool_visible):
                    if normalize_movie(mm) == normalize_movie(movie):
                        self.pool_list.selection_set(i)
                        self.pool_list.see(i)
                        break

                self._set_info(f"🔍 Listede bulundu: {movie}", "info")
            else:
                self.pool_list.selection_clear(0, tk.END)
                self.watched_list.selection_clear(0, tk.END)

                all_w = read_file(WATCHED_FILE)
                for i, mm in enumerate(all_w):
                    if normalize_movie(mm) == normalize_movie(movie):
                        self.watched_list.selection_set(i)
                        self.watched_list.see(i)
                        break

                self._set_info(f"🔍 İzlenenlerde bulundu: {movie}", "warning")

            win.destroy()

        lb_pool.bind("<Double-Button-1>", lambda e: (lb_pool.curselection() and select_in_main("pool", lb_pool.get(lb_pool.curselection()[0]))))
        lb_w.bind("<Double-Button-1>", lambda e: (lb_w.curselection() and select_in_main("watched", lb_w.get(lb_w.curselection()[0]))))

        tb.Button(win, text="Kapat", bootstyle="secondary", command=win.destroy, width=12).pack(pady=(0, 12))

    # ================================
    # Seçili filmi liste ⇄ izlenen arasında taşı
    # ================================
    def toggle_move_selected(self):
        which, movie = self._get_selected_anywhere()
        if not which or not movie:
            messagebox.showwarning("Uyarı", "Taşımak için listeden veya izlenenlerden bir film seç.")
            return

        watched = read_file(WATCHED_FILE)

        if which == "pool":
            # Orijinal film adını çıkar
            original_movie = self._extract_original_movie_name(movie)
            
            if not contains_ci(watched, original_movie):
                watched.append(original_movie)
                write_file(WATCHED_FILE, watched)
                
                # İzlenme tarihini kaydet
                self.watch_dates = add_watch_date(original_movie, self.watch_dates)
                save_watch_dates(self.watch_dates)
                
                # Hangi listeden eklendiğini kaydet
                current_list_id = self.current_list_id()
                self.watch_history = add_to_watch_history(original_movie, current_list_id, self.watch_history)
                save_watch_history(self.watch_history)

            remove_movie_from_all_lists(self.meta, original_movie)

            self.refresh_lists()
            self._set_info(f"✅ '{original_movie}' izlenenlere taşındı ve tüm listelerden çıkarıldı.", "success")
        else:
            # Orijinal film adını çıkar (⭐, 📅, 📝 ekleri olmadan)
            original_movie = self._extract_original_movie_name(movie)
            movie_key = get_movie_key(original_movie)

            # Bu film izlenenlere hangi listeden eklenmişti kontrolünü yap
            target_list_id = self.watch_history.get(movie_key)

            # İzlenenlerden kaldır (büyük/küçük harf ve boşluk duyarsız)
            watched = read_file(WATCHED_FILE)
            target_norm = normalize_movie(original_movie)
            watched_cleaned = [m for m in watched if normalize_movie(m) != target_norm]
            write_file(WATCHED_FILE, watched_cleaned)

            # Orijinal listeye (biliniyorsa) ya da seçili listeye geri ekle
            if target_list_id:
                target_path = list_file_path(target_list_id, self.meta)
                if os.path.exists(target_path):
                    items = read_file(target_path)
                    if not contains_ci(items, original_movie):
                        items.append(original_movie)
                        write_file(target_path, items)

                    target_list_name = next((it["name"] for it in self.meta["lists"] if it["id"] == target_list_id), "bilinmeyen liste")
                    self.refresh_lists()
                    self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve '{target_list_name}' listesine geri eklendi.", "info")
                    return

            # Geçmiş yoksa / liste yoksa şu anki listeye ekle
            p = self.current_list_path()
            items = read_file(p)
            if not contains_ci(items, original_movie):
                items.append(original_movie)
                write_file(p, items)

            self.refresh_lists()
            self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve seçili listeye geri eklendi.", "info")


    # ================================
    # Liste Ekleme
    # ================================
    def add_new_list(self):
        choice_win = tb.Toplevel(self)
        choice_win.title("Yeni Liste Ekle")
        choice_win.geometry("400x260")
        choice_win.transient(self)
        choice_win.grab_set()

        tb.Label(
            choice_win, 
            text="Yeni liste nasıl oluşturulsun?", 
            font=("Segoe UI", 12, "bold"),
            padding=(10, 15)
        ).pack()

        btn_frame = tb.Frame(choice_win, padding=20)
        btn_frame.pack(fill=BOTH, expand=True)

        def file_upload():
            choice_win.destroy()
            self._add_list_from_file()

        def manual_create():
            choice_win.destroy()
            self._add_list_manually()

        tb.Button(
            btn_frame,
            text="📁 Dosya Yükle",
            bootstyle="primary",
            command=file_upload,
            width=25,
            padding=(12, 12)
        ).pack(pady=(0, 15))

        tb.Label(
            btn_frame,
            text="TXT dosyası yükleyin.\nHer satırda 1 film olmalı.",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(pady=(0, 20))

        tb.Button(
            btn_frame,
            text="✍ Manuel Liste Oluştur",
            bootstyle="info",
            command=manual_create,
            width=25,
            padding=(12, 12)
        ).pack(pady=(0, 15))

        tb.Label(
            btn_frame,
            text="Her satıra 1 film yazın.",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack()

    def _add_list_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Film Listesi Dosyası Seçin",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                movies = [line.strip() for line in f.readlines() if line.strip()]
            
            if not movies:
                messagebox.showwarning("Uyarı", "Dosya boş veya geçersiz!")
                return

            list_name = simpledialog.askstring(
                "Liste Adı",
                f"Bu liste için bir isim girin:\n({len(movies)} film yüklendi)"
            )
            
            if not list_name or not list_name.strip():
                return

            list_name = list_name.strip()

            # Liste ID'si oluştur
            list_id = re.sub(r'[^a-z0-9_]', '_', list_name.lower())
            list_id = re.sub(r'_+', '_', list_id).strip('_')
            
            # Aynı isimde liste var mı kontrol et
            if any(it["name"].lower() == list_name.lower() for it in self.meta["lists"]):
                messagebox.showwarning("Uyarı", "Bu isimde bir liste zaten var!")
                return

            # Yeni listeyi ekle
            new_list = {
                "id": list_id,
                "name": list_name,
                "filename": f"{list_id}.txt",
                "builtin": False
            }
            
            self.meta["lists"].append(new_list)
            save_lists_meta(self.meta)

            # Dosyayı kaydet
            list_path = list_file_path(list_id, self.meta)
            write_file(list_path, movies)

            # UI'ı güncelle
            self.list_names = [it["name"] for it in self.meta["lists"]]
            self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}
            self.list_combo.configure(values=self.list_names)
            self.selected_list_var.set(list_name)
            self.meta["selected"] = list_id
            save_lists_meta(self.meta)

            self.refresh_lists()
            self._set_info(f"✅ '{list_name}' listesi eklendi ({len(movies)} film)", "success")

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yüklenirken hata oluştu:\n{e}")

    def _add_list_manually(self):
        manual_win = tb.Toplevel(self)
        manual_win.title("Manuel Liste Oluştur")
        manual_win.geometry("600x550")
        manual_win.transient(self)
        manual_win.grab_set()

        tb.Label(
            manual_win,
            text="Her satıra 1 film yazın:",
            font=("Segoe UI", 11, "bold"),
            padding=(10, 10)
        ).pack()

        text_frame = tb.Frame(manual_win, padding=10)
        text_frame.pack(fill=BOTH, expand=True)

        scroll = tb.Scrollbar(text_frame)
        scroll.pack(side=RIGHT, fill=Y)

        text_widget = tk.Text(
            text_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            yscrollcommand=scroll.set
        )
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.config(command=text_widget.yview)

        text_widget.insert("1.0", "Örnek:\nThe Matrix (1999)\nInception (2010)\nInterstellar (2014)")

        def save_manual_list():
            content = text_widget.get("1.0", tk.END)
            movies = [line.strip() for line in content.split("\n") if line.strip()]
            
            if not movies:
                messagebox.showwarning("Uyarı", "En az bir film girmelisiniz!")
                return

            list_name = simpledialog.askstring(
                "Liste Adı",
                f"Bu liste için bir isim girin:\n({len(movies)} film)"
            )
            
            if not list_name or not list_name.strip():
                return

            list_name = list_name.strip()

            # Liste ID'si oluştur
            list_id = re.sub(r'[^a-z0-9_]', '_', list_name.lower())
            list_id = re.sub(r'_+', '_', list_id).strip('_')
            
            # Aynı isimde liste var mı kontrol et
            if any(it["name"].lower() == list_name.lower() for it in self.meta["lists"]):
                messagebox.showwarning("Uyarı", "Bu isimde bir liste zaten var!")
                return

            # Yeni listeyi ekle
            new_list = {
                "id": list_id,
                "name": list_name,
                "filename": f"{list_id}.txt",
                "builtin": False
            }
            
            self.meta["lists"].append(new_list)
            save_lists_meta(self.meta)

            # Dosyayı kaydet
            list_path = list_file_path(list_id, self.meta)
            write_file(list_path, movies)

            # UI'ı güncelle
            self.list_names = [it["name"] for it in self.meta["lists"]]
            self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}
            self.list_combo.configure(values=self.list_names)
            self.selected_list_var.set(list_name)
            self.meta["selected"] = list_id
            save_lists_meta(self.meta)

            manual_win.destroy()
            self.refresh_lists()
            self._set_info(f"✅ '{list_name}' listesi oluşturuldu ({len(movies)} film)", "success")

        button_frame = tb.Frame(manual_win, padding=10)
        button_frame.pack(fill=X)

        tb.Button(
            button_frame,
            text="Listeyi Kaydet",
            bootstyle="success",
            command=save_manual_list,
            width=15
        ).pack(side=LEFT, padx=(0, 10))

        tb.Button(
            button_frame,
            text="İptal",
            bootstyle="secondary",
            command=manual_win.destroy,
            width=15
        ).pack(side=LEFT)

    # ================================
    # Listeyi Kaldır
    # ================================
    def remove_current_list(self):
        current_id = self.current_list_id()
        current_name = self.selected_list_var.get()

        # Sabit listeleri kaldırmaya izin verme
        current_list_obj = next((it for it in self.meta["lists"] if it["id"] == current_id), None)
        if current_list_obj and current_list_obj.get("builtin", False):
            messagebox.showwarning("Uyarı", "Varsayılan listeler kaldırılamaz!")
            return

        # En az bir liste kalmalı
        if len(self.meta["lists"]) <= 1:
            messagebox.showwarning("Uyarı", "En az bir liste olmalı!")
            return

        # Onay iste
        answer = messagebox.askyesno(
            "Onay",
            f"'{current_name}' listesi kalıcı olarak silinecek.\n\nEmin misiniz?"
        )
        
        if not answer:
            return

        # Liste dosyasını sil
        list_path = self.current_list_path()
        if os.path.exists(list_path):
            try:
                os.remove(list_path)
            except Exception as e:
                messagebox.showerror("Hata", f"Liste dosyası silinirken hata oluştu:\n{e}")
                return

        
        self.meta["lists"] = [it for it in self.meta["lists"] if it["id"] != current_id]
        
        
        if self.meta["lists"]:
            self.meta["selected"] = self.meta["lists"][0]["id"]
        
        save_lists_meta(self.meta)

       
        self.list_names = [it["name"] for it in self.meta["lists"]]
        self.list_id_by_name = {it["name"]: it["id"] for it in self.meta["lists"]}
        self.list_combo.configure(values=self.list_names)
        
        if self.meta["lists"]:
            self.selected_list_var.set(self.meta["lists"][0]["name"])
        
        self.refresh_lists()
        self._set_info(f"🗑 '{current_name}' listesi kaldırıldı", "danger")

    # ================================
    # Seçileni kaldır (bulunduğu yerden)
    # ================================
    def delete_selected_anywhere(self):
        which, movie = self._get_selected_anywhere()
        if not which or not movie:
            messagebox.showwarning("Uyarı", "Kaldırmak için listeden veya izlenenlerden bir film seç.")
            return

        # Orijinal film adını çıkar (⭐, 📅, 📝 ikonları olmadan)
        original_movie = self._extract_original_movie_name(movie)

        if which == "pool":
            if not messagebox.askyesno("Onay", f"'{original_movie}' listeden tamamen silinsin mi?"):
                return
            
            p = self.current_list_path()
            items = read_file(p)
            items = remove_ci(items, original_movie)
            write_file(p, items)
            self.refresh_lists()
            self._set_info(f"🗑 '{original_movie}' seçili listeden kaldırıldı.", "danger")
        else:
            # İzlenenlerden kaldırma - orijinal listeye geri dön
            movie_key = get_movie_key(original_movie)
            target_list_id = self.watch_history.get(movie_key)
            
            if target_list_id:
                target_list_name = next((it["name"] for it in self.meta["lists"] if it["id"] == target_list_id), "bilinmeyen liste")
                answer = messagebox.askyesno(
                    "İzlenenlerden Çıkar",
                    f"'{original_movie}' izlenenlerden çıkarılsın ve '{target_list_name}' listesine geri eklensin mi?"
                )
            else:
                answer = messagebox.askyesno(
                    "İzlenenlerden Çıkar",
                    f"'{original_movie}' izlenenlerden çıkarılsın ve seçili listeye geri eklensin mi?"
                )
            
            if not answer:
                return
            
            # DOĞRUDAN dosya okuma
            target_normalized = normalize_movie(original_movie)
            
            with open(WATCHED_FILE, "r", encoding="utf-8") as f:
                all_lines = [line.strip() for line in f.readlines() if line.strip()]
            
            print(f"🔍 ÖNCE: {len(all_lines)} film var")
            
            # Filmi temizle
            cleaned_lines = []
            for line in all_lines:
                if normalize_movie(line) != target_normalized:
                    cleaned_lines.append(line)
            
            print(f"🔍 SONRA: {len(cleaned_lines)} film kaldı")
            print(f"🔍 Silindi mi? {len(all_lines) - len(cleaned_lines) > 0}")
            
            # DOĞRUDAN dosya yazma
            with open(WATCHED_FILE, "w", encoding="utf-8") as f:
                for line in cleaned_lines:
                    f.write(line + "\n")
            
            # TÜM verileri temizle (puan, not, izlenme tarihi, geçmiş)
            if movie_key in self.watch_dates:
                del self.watch_dates[movie_key]
                save_watch_dates(self.watch_dates)
            
            if movie_key in self.ratings:
                del self.ratings[movie_key]
                save_ratings(self.ratings)
            
            if movie_key in self.notes:
                del self.notes[movie_key]
                save_notes(self.notes)
            
            if movie_key in self.watch_history:
                del self.watch_history[movie_key]
                save_watch_history(self.watch_history)
            
            # Önbellekleri yeniden yükle (refresh_lists bunları kullanacak)
            self.watch_dates = load_watch_dates()
            self.ratings = load_ratings()
            self.notes = load_notes()
            self.watch_history = load_watch_history()
            
            # FORCE: Dosyayı tekrar oku ve kontrol et
            final_watched = read_file(WATCHED_FILE)
            print(f"🔍 DEBUG: İzlenenler listesi: {len(final_watched)} film")
            print(f"🔍 DEBUG: '{original_movie}' listede var mı? {any(normalize_movie(m) == normalize_movie(original_movie) for m in final_watched)}")
            
            # Orijinal listeye veya şu anki listeye geri ekle
            if target_list_id:
                target_path = list_file_path(target_list_id, self.meta)
                if os.path.exists(target_path):
                    items = read_file(target_path)
                    if not contains_ci(items, original_movie):
                        items.append(original_movie)
                        write_file(target_path, items)
                    target_list_name = next((it["name"] for it in self.meta["lists"] if it["id"] == target_list_id), "bilinmeyen liste")
                    self.refresh_lists()
                    self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve '{target_list_name}' listesine geri eklendi.", "info")
                    return
            
            # Liste bulunamazsa şu anki listeye ekle
            p = self.current_list_path()
            items = read_file(p)
            if not contains_ci(items, original_movie):
                items.append(original_movie)
                write_file(p, items)
            
            self.refresh_lists()
            self._set_info(f"↩ '{original_movie}' izlenenlerden çıkarıldı ve seçili listeye geri eklendi.", "info")

    
    # ================================
    # Poster (Afiş) - TMDb 
    # ================================
    def set_tmdb_key(self):
        """Kullanıcıdan TMDb API anahtarı al ve kaydet."""
        key = simpledialog.askstring(
            "TMDb API Anahtarı",
            """Afişleri otomatik getirmek için TMDb API anahtarınızı girin.

• Ücretsiz anahtar: themoviedb.org/settings/api
• Boş bırakırsanız afiş indirme kapalı kalır.""",
        )
        if key is None:
            return
        self.settings["tmdb_api_key"] = key.strip()
        save_settings(self.settings)
        self._set_info("✅ TMDb anahtarı kaydedildi.", "success")
    
        self.update_poster_from_selection()

    def _tmdb_key(self) -> str:
        return (self.settings.get("tmdb_api_key") or "").strip()

    def _poster_cache_path(self, movie: str) -> str:
        safe = re.sub(r"[^a-z0-9_\-]+", "_", normalize_movie(movie))
        safe = re.sub(r"_+", "_", safe).strip("_")
        return os.path.join(POSTERS_DIR, f"{safe}.jpg")

    def _parse_title_year(self, movie: str):
        s = movie.strip()
        m = re.match(r"^(.*)\((\d{4})\)\s*$", s)
        if m:
            return m.group(1).strip(), m.group(2)
        return s, None

    def _tmdb_search(self, title: str, year: str | None):
        key = self._tmdb_key()
        if not key:
            return None

        params = {
            "api_key": key,
            "query": title,
            "include_adult": "false",
            "language": "tr-TR",
        }
        if year:
            params["year"] = year

        url = "https://api.themoviedb.org/3/search/movie?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FilmSec/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
            results = data.get("results") or []
            if not results:
                return None
            return results[0]
        except Exception:
            return None

    def _download_poster(self, movie: str) -> str | None:
        key = self._tmdb_key()
        if not key:
            return None

        title, year = self._parse_title_year(movie)
        result = self._tmdb_search(title, year)
        if not result:
            return None

        poster_path = result.get("poster_path")
        if not poster_path:
            return None

        img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        out_path = self._poster_cache_path(movie)

        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": "FilmSec/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                img_bytes = r.read()
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            return out_path
        except Exception:
            return None

    def _get_poster_path(self, movie: str) -> str | None:
        p = self._poster_cache_path(movie)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return p
        return self._download_poster(movie)
    def update_poster_preview(self, movie: str):
        """Seçili film için afişi sağ panelde göster."""
        movie = (movie or "").strip()
        self.poster_title_var.set(movie)

        if not movie:
            self.poster_img_label.configure(image="", text="🎬 Bir film seç")
            self.poster_photo = None
            return

        
        if Image is None or ImageTk is None:
            self.poster_img_label.configure(image="", text="(Afiş için Pillow gerekli)\npython -m pip install pillow")
            self.poster_photo = None
            return

        key = self._tmdb_key()
        if not key:
            self.poster_img_label.configure(image="", text="TMDb anahtarı yok\n(🔑 TMDb Anahtarı butonu ile ekleyin)")
            self.poster_photo = None
            return

        poster_path = self._get_poster_path(movie)
        if not poster_path:
            self.poster_img_label.configure(image="", text="Afiş bulunamadı")
            self.poster_photo = None
            return

        try:
            img = Image.open(poster_path)
            
            target_w = 260
            w, h = img.size
            if w and h:
                target_h = max(80, int(h * (target_w / w)))
                img = img.resize((target_w, target_h))

            photo = ImageTk.PhotoImage(img)
            self.poster_photo = photo  
            self.poster_img_label.configure(image=photo, text="")
        except Exception:
            self.poster_img_label.configure(image="", text="Afiş yüklenemedi")
            self.poster_photo = None

    
    def open_data_dir(self):
        try:
            if os.name == "nt":
                os.startfile(DATA_DIR)
            elif sys_platform() == "darwin":
                os.system(f'open "{DATA_DIR}"')
            else:
                os.system(f'xdg-open "{DATA_DIR}"')
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı: {e}")


if __name__ == "__main__":
    FilmSecApp().mainloop()
