import csv
import os
import re
import sys
import requests

from responses_data import RESPONSES
from servant_data import normalize

URL = "http://127.0.0.1:5000/chat"

BANNED_PHRASES = [
    "weak to enuma elish",   
    "no hard pity",         
    "no pity system",      
    "spark",             
]

TESTS = [
    ("heya", "greeting", None),
    ("hello hello", "greeting", None),
    ("good morning chatbot", "greeting", None),
    ("hi, quick question", "greeting", None),

    ("what's fgo all about", "game_info", None),
    ("give me a quick overview of this game", "game_info", None),
    ("who developed fate grand order", "game_info", None),
    ("can i play fgo on my computer", "game_info", None),

    ("what are my odds of pulling a 5 star", "gacha_info", None),
    ("how do banners work", "gacha_info", None),
    ("how much do i need to spend to summon", "gacha_info", None),
    ("is there any guaranteed pull", "gacha_info", None),

    ("how can i defeat a tough boss", "gameplay_help", None),
    ("explain card chains", "gameplay_help", None),
    ("how do i fill my np gauge", "gameplay_help", None),
    ("which classes are strong against others", "servant_info", "Lancer"), 

    ("is anything happening in the game right now", "event_info", None),
    ("when is the next event", "event_info", None),
    ("what do events give you", "event_info", None),

    ("is it worth starting fgo today", "player_review", None),
    ("can you enjoy fgo without paying", "player_review", None),
    ("is fgo too grindy", "player_review", None),
    ("would you recommend this game to a beginner", "player_review", None),

    ("who is gilgamesh", "servant_info", "Gilgamesh"),
    ("tell me about scathach", "servant_info", "Scathach"),
    ("tamamo", "servant_info", "Tamamo-no-Mae"),
    ("tell me about cu chulainn", "servant_info", "Chulainn"),
    ("cu chulain", "servant_info", "Chulainn"),         
    ("who is nero", "servant_info", "Nero"),
    ("tell me about a servant", "servant_info", None),   
    ("saber", "servant_info", "Lancer"),                  
    ("what are the servant classes", "servant_info", "Berserker"),
   
    ("what's the weather today", "reject", None),
    ("tell me a joke", "reject", None),
    ("what is the capital of france", "reject", None),
    ("recommend me a movie", "reject", None),
    ("asdfgh", "reject", None),
    ("idk", "reject", None),
  
    ("is fgo more generous than other gachas", "player_review", None),

    ("WHAT ARE THE GACHA RATES???", "gacha_info", None),
    ("hello \U0001F60A", "greeting", None),
    ("   ", "error", None),
]


def plain(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def load_training_texts(path="fgo_dataset.csv"):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {plain(row["text"]) for row in csv.DictReader(f)}


def reply_kind(reply, intent):
    if reply in RESPONSES["fallback_unclear"] or reply in RESPONSES["fallback_offtopic"]:
        return "reject"
    return intent


def main():
    lines = []

    def out(text=""):
        print(text)
        lines.append(text)

    passed = 0
    misses = []
    train_set = load_training_texts()
    novel_total = novel_passed = 0

    for message, expected, must_contain in TESTS:
        server_kind = None
        try:
            resp = requests.post(URL, json={"message": message}, timeout=15)
        except requests.exceptions.ConnectionError:
            print("Could not reach the chatbot at", URL)
            print("Start it first with:  python app.py   (in another terminal)")
            sys.exit(1)

        if resp.status_code == 400:
            kind, reply, conf, intent = "error", resp.json().get("error", ""), 0.0, "-"
        else:
            data = resp.json()
            intent = data["intent"]
            reply = data["reply"]
            conf = data["confidence"]
            kind = reply_kind(reply, intent)
            server_kind = data.get("kind")

        ok = kind == expected
        banned = next((b for b in BANNED_PHRASES if b in reply.lower()), None)
        if banned:
            ok, kind = False, f"BANNED: {banned}"
        if resp.status_code != 400:
            if server_kind is None:
                ok, kind = False, "NO kind FIELD (old app.py?)"
            elif (server_kind in ("unclear", "offtopic")) != (reply_kind(reply, intent) == "reject"):
                ok, kind = False, f"kind MISMATCH ({server_kind})"
        if ok and must_contain and normalize(must_contain) not in normalize(reply):
            ok = False
        seen = plain(message) in train_set
        if ok:
            passed += 1
        else:
            misses.append((message, expected, kind, reply))
        if not seen:
            novel_total += 1
            novel_passed += ok

        out(f"[{'PASS' if ok else 'CHECK'}] {message!r}" + ("  (in training data)" if seen else ""))
        out(f"        expected: {expected:14} got: {kind:14} (intent={intent}, conf={conf})")
        out(f"        reply: {reply}")
        out()

    out("=" * 70)
    out(f"{passed}/{len(TESTS)} replies were the expected kind "
        f"({100 * passed // len(TESTS)}%)")
    out(f"{novel_passed}/{novel_total} on questions NOT in the training data "
        f"({100 * novel_passed // max(novel_total, 1)}%) - the fairer number")
    if misses:
        out()
        out("Items to review (a miss is not automatically a bug - the classifier is")
        out("~65% accurate on a small dataset, so some misroutes are expected):")
        for message, expected, kind, reply in misses:
            out(f"  - {message!r}: expected {expected}, got {kind}")

    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\nSaved test_results.txt")


if __name__ == "__main__":
    main()
