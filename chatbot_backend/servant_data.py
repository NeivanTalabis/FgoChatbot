import difflib
import json
import os
import re
import unicodedata
import requests

CACHE_FILE = "servant_cache.json"
BASIC_ROSTER_URL = "https://api.atlasacademy.io/export/NA/basic_servant.json"


def normalize(name):
    name = name.lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[-'\u2019()/]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def fetch_roster(force_refresh=False):
    if not force_refresh and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    resp = requests.get(BASIC_ROSTER_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return data


def build_lookup(roster):
    groups = {}
    for svt in roster:
        name = svt.get("name", "")
        if not name or svt.get("type") not in ("normal", "heroine"):
            continue
        groups.setdefault(normalize(name), []).append(svt)

    lookup = {}
    for key, group in groups.items():
        group = sorted(group, key=lambda s: s.get("collectionNo", 9999))
        chosen = dict(group[0])       
        chosen["_other_forms"] = [
            {"className": s.get("className", ""), "rarity": s.get("rarity", 0)}
            for s in group[1:]
        ]
        lookup[key] = chosen
    return lookup

ALIAS_BLOCKLIST = {
    "the", "with", "and", "king", "queen", "lord", "lady", "saint", "holy", "dark",
    "black", "white", "red", "blue", "great", "little", "super", "mysterious",
    "summer", "winter", "santa", "alter", "lily", "ruler", "rider", "saber",
    "archer", "lancer", "caster", "assassin", "berserker", "shielder", "beast",
    "avenger", "foreigner", "pretender", "demon", "ancient", "young", "old",
    "space", "master", "witch", "princess", "knight", "shadow",
}

MAX_BARE_NAME_WORDS = 2

FILLER_WORDS = {
    "tell", "me", "about", "who", "is", "are", "was", "what", "whats", "s", "the", "a", "an",
    "of", "do", "does", "did", "you", "know", "can", "could", "please", "pls", "give", "info",
    "information", "on", "show", "explain", "describe", "more", "i", "want", "to", "see", "how",
    "good", "best", "strong", "strongest", "servant", "servants", "character", "characters",
    "hero", "profile", "stats", "details", "detail", "his", "her", "their", "and", "or", "for",
    "with", "in", "it", "this", "that", "looking", "like", "think", "class", "classes",
}


def _content_words(tokens):
    return [t for t in tokens if t not in FILLER_WORDS]

ALIAS_OVERRIDES = {
    "tamamo": "tamamo no mae",
    "artoria": "altria pendragon",   
    "arturia": "altria pendragon",
}

PHRASE_ALIASES = {
    "artoria pendragon": "altria pendragon",
    "arturia pendragon": "altria pendragon",
    "artoria alter": "altria pendragon alter",
    "arturia alter": "altria pendragon alter",
    "saber alter": "altria pendragon alter",
}


def _base_tokens(svt):
    name = re.sub(r"\([^)]*\)", " ", svt.get("name", ""))
    return normalize(name).split()


def build_alias_lookup(lookup):
    first_groups, last_groups = {}, {}
    for svt in lookup.values():
        tokens = _base_tokens(svt)
        if len(tokens) < 2:
            continue
        for word, groups in ((tokens[0], first_groups), (tokens[-1], last_groups)):
            if len(word) < 4 or word in ALIAS_BLOCKLIST or word in lookup:
                continue
            groups.setdefault(word, []).append(svt)

    groups = dict(first_groups)
    for word, members in last_groups.items():
        groups.setdefault(word, members)

    aliases = {}
    for word in set(groups) | set(ALIAS_OVERRIDES):
        group = sorted(groups.get(word, []), key=lambda s: s.get("collectionNo", 9999))
        chosen = group[0] if group else None
        override_key = ALIAS_OVERRIDES.get(word)
        if override_key and override_key in lookup:
            chosen = lookup[override_key]
        if chosen is None:
            continue
        entry = dict(chosen)           
        entry["_similar_names"] = [
            s.get("name", "") for s in group
            if s.get("name") and s.get("name") != chosen.get("name")
        ][:3]
        aliases[word] = entry
    return aliases


def find_servant_in_text(text, lookup, alias_lookup=None):
    text_norm = normalize(text)

    for phrase, key in PHRASE_ALIASES.items():
        if key in lookup and re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text_norm):
            return lookup[key]

    for name in sorted(lookup.keys(), key=len, reverse=True):
        if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", text_norm):
            return lookup[name]

    if alias_lookup and len(_content_words(text_norm.split())) <= MAX_BARE_NAME_WORDS:
        for token in text_norm.split():
            if token in alias_lookup:
                return alias_lookup[token]

    return fuzzy_match(text_norm, lookup, alias_lookup)


FUZZY_CUTOFF = 0.88      
FUZZY_MIN_LENGTH = 6    


def fuzzy_match(text_norm, lookup, alias_lookup=None):
    tokens = text_norm.split()
    pool = {}
    if alias_lookup and len(_content_words(tokens)) <= MAX_BARE_NAME_WORDS:
        pool.update(alias_lookup)
    pool.update(lookup)            
    keys = list(pool.keys())

    for size in range(min(4, len(tokens)), 0, -1):
        for start in range(len(tokens) - size + 1):
            window = " ".join(tokens[start:start + size])
            if len(window) < FUZZY_MIN_LENGTH or window in ALIAS_BLOCKLIST or window in FILLER_WORDS:
                continue
            close = difflib.get_close_matches(window, keys, n=1, cutoff=FUZZY_CUTOFF)
            if close:
                return pool[close[0]]
    return None


if __name__ == "__main__":
    roster = fetch_roster()
    print(f"Fetched {len(roster)} servant entries.")
    lookup = build_lookup(roster)
    aliases = build_alias_lookup(lookup)
    print(f"Built {len(aliases)} first-name aliases.")
    for test_text in ["tell me about gilgamesh", "tamamo", "nero",
                      "is fgo more generous than other gachas"]:
        match = find_servant_in_text(test_text, lookup, aliases)
        print(f"{test_text!r} -> {match.get('name') if match else None}")

CLASS_WORDS = {
    "saber": "saber", "archer": "archer", "lancer": "lancer", "rider": "rider", "caster": "caster",
    "assassin": "assassin", "berserker": "berserker", "ruler": "ruler", "avenger": "avenger",
    "shielder": "shielder", "foreigner": "foreigner", "pretender": "pretender",
    "moon cancer": "moonCancer", "mooncancer": "moonCancer", "alter ego": "alterEgo",
    "alterego": "alterEgo", "beast": "beast",
}


def find_class_in_text(text):
    tokens = normalize(text).split()
    if len(_content_words(tokens)) > MAX_BARE_NAME_WORDS:
        return None
    text_norm = " ".join(tokens)
    for phrase in sorted(CLASS_WORDS, key=len, reverse=True):
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text_norm):
            return CLASS_WORDS[phrase]
    return None


def mentions_classes(text):
    return re.search(r"(?<![a-z0-9])class(es)?(?![a-z0-9])", normalize(text)) is not None


def class_overview(roster, class_key):
    members = [s for s in roster if s.get("className") == class_key and s.get("type") in ("normal", "heroine")]
    members.sort(key=lambda s: s.get("collectionNo", 9999))
    names, seen = [], set()
    for svt in members:
        name = svt.get("name")
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return len(names), names[:3]
