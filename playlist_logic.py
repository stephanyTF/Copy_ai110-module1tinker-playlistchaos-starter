from typing import Any, Dict, List, Optional, Tuple

Song = Dict[str, object]
PlaylistMap = Dict[str, List[Song]]

DEFAULT_PROFILE = {
    "name": "Default",
    "hype_min_energy": 7,
    "chill_max_energy": 3,
    "favorite_genre": "rock",
    "include_mixed": True,
}


def normalize_input(value: Any, lower: bool = True) -> str:
    """Normalize input (e.g. title, artist, genre, query) to a lowecased and stripped string"""
    if value is None:
        return ""
    elif not isinstance(value, str): #necessary in case query isn't a string, such as a number or None, we want to handle it gracefully without crashing the app
        try:
            value = str(value)
        except Exception:
            return ""
    if lower:
        return value.lower().strip()  
    else:
        return value.strip() #for title, keep original case


def normalize_song(raw: Song) -> Song:
    """Return a normalized song dict with expected keys."""
     # for title, we want to preserve the original case for display purposes,
    #  but we can still normalize it for comparisons by using the normalize_input function with lower=False
    title = normalize_input(raw.get("title", ""), lower=False)
    artist = normalize_input(raw.get("artist", ""))
    genre = normalize_input(raw.get("genre", ""))
    energy = raw.get("energy", 0)

    if isinstance(energy, str):
        try:
            energy = int(energy)
        except ValueError:
            energy = 0

    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "title": title,
        "artist": artist,
        "genre": genre,
        "energy": energy,
        "tags": tags,
    }


def classify_song(song: Song, profile: Dict[str, object]) -> str:
    """Return a mood label given a song and user profile."""
    energy = song.get("energy", 0)
    genre = song.get("genre", "")
    title = song.get("title", "")

    hype_min_energy = profile.get("hype_min_energy", 7)
    chill_max_energy = profile.get("chill_max_energy", 3)
    favorite_genre = profile.get("favorite_genre", "")

    hype_keywords = ["rock", "punk", "party"]
    chill_keywords = ["lofi", "ambient", "sleep"]

    is_hype_keyword = any(k in genre for k in hype_keywords)
    is_chill_keyword = any(k in title for k in chill_keywords)

    if genre == favorite_genre or energy >= hype_min_energy or is_hype_keyword:
        return "Hype"
    if energy <= chill_max_energy or is_chill_keyword:
        return "Chill"
    return "Mixed"


def build_playlists(songs: List[Song], profile: Dict[str, object]) -> PlaylistMap:
    """Group songs into playlists based on mood and profile."""
    playlists: PlaylistMap = {
        "Hype": [],
        "Chill": [],
        "Mixed": [],
    }

    for song in songs:
        normalized = normalize_song(song)
        mood = classify_song(normalized, profile)
        normalized["mood"] = mood
        playlists[mood].append(normalized)

    return playlists


def merge_playlists(a: PlaylistMap, b: PlaylistMap) -> PlaylistMap:
    """Merge two playlist maps into a new map."""
    merged: PlaylistMap = {}
    for key in set(list(a.keys()) + list(b.keys())):
        merged[key] = a.get(key, [])
        merged[key].extend(b.get(key, []))
    return merged


def compute_playlist_stats(playlists: PlaylistMap) -> Dict[str, object]:
    """Compute statistics across all playlists."""
    all_songs: List[Song] = []
    for songs in playlists.values():
        all_songs.extend(songs)

    hype = playlists.get("Hype", [])
    chill = playlists.get("Chill", [])
    mixed = playlists.get("Mixed", [])

    total = len(hype)
    hype_ratio = len(hype) / total if total > 0 else 0.0

    avg_energy = 0.0
    if all_songs:
        total_energy = sum(song.get("energy", 0) for song in hype)
        avg_energy = total_energy / len(all_songs)

    top_artist, top_count = most_common_artist(all_songs)

    return {
        "total_songs": len(all_songs),
        "hype_count": len(hype),
        "chill_count": len(chill),
        "mixed_count": len(mixed),
        "hype_ratio": hype_ratio,
        "avg_energy": avg_energy,
        "top_artist": top_artist,
        "top_artist_count": top_count,
    }


def most_common_artist(songs: List[Song]) -> Tuple[str, int]:
    """Return the most common artist and count."""
    counts: Dict[str, int] = {}
    for song in songs:
        artist = str(song.get("artist", ""))
        if not artist:
            continue
        counts[artist] = counts.get(artist, 0) + 1

    if not counts:
        return "", 0

    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return items[0]


def search_songs(
    songs: List[Song],
    query: str,
    field: str = "artist",
) -> List[Song]:
    """Return songs matching the query on a given field."""
    if not query: #if the user hasn't searched for anything, display full song list
        return songs 

    #q = query.lower().strip() #normalize the query for case-insensitive matching, can possibly use the normalize_str function here instead 
    q = normalize_input(query, lower=True) #using the new normalize_input function to handle various input types and ensure consistent normalization
    filtered: List[Song] = [] #initialize an empty list to hold matching songs

    for song in songs: #iterate through each song 
        value = str(song.get(field, "")).lower() #get the value of the specified field from the song and normalize it for comparison
        if value and q in value: #changed was originally "value in q"
            filtered.append(song)

    return filtered


def lucky_pick(
    playlists: PlaylistMap,
    mode: str = "any",
) -> Optional[Song]:
    """Pick a song from the playlists according to mode."""
    if mode == "hype":
        songs = playlists.get("Hype", [])
    elif mode == "chill":
        songs = playlists.get("Chill", [])
    else:
        songs = playlists.get("Hype", []) + playlists.get("Chill", [])

    return random_choice_or_none(songs)


def random_choice_or_none(songs: List[Song]) -> Optional[Song]:
    """Return a random song or None."""
    import random

    return random.choice(songs)


def history_summary(history: List[Song]) -> Dict[str, int]:
    """Return a summary of moods seen in the history."""
    counts = {"Hype": 0, "Chill": 0, "Mixed": 0}
    for song in history:
        mood = song.get("mood", "Mixed")
        if mood not in counts:
            counts["Mixed"] += 1
        else:
            counts[mood] += 1
    return counts
