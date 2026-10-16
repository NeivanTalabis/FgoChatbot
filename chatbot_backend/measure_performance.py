import argparse
import platform
import statistics
import sys
import time

import requests

URL = "http://127.0.0.1:5000/chat"

MESSAGES = [
    "hello there", "what is fgo about", "how do banners work", "how do i beat a tough boss",
    "is there an event right now", "is fgo worth playing", "tell me about gilgamesh", "tamamo",
    "musashi", "who is nero", "what's the weather today", "recommend me a movie", "asdfgh",
    "is there any guaranteed pull", "how do chains work",
]


def percentile(values, pct):
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))
    return ordered[index]


def main(runs):
    session = requests.Session()
    timings = []
    failures = 0

    try:
        start = time.perf_counter()
        first = session.post(URL, json={"message": MESSAGES[0]}, timeout=30)
        first_ms = (time.perf_counter() - start) * 1000
        first.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Could not get a reply from", URL)
        print("Start the server first with:  python app.py   (in another terminal)")
        print("Details:", e)
        sys.exit(1)

    for i in range(runs):
        message = MESSAGES[i % len(MESSAGES)]
        start = time.perf_counter()
        try:
            r = session.post(URL, json={"message": message}, timeout=30)
            ok = r.status_code == 200
        except requests.exceptions.RequestException:
            ok = False
        elapsed_ms = (time.perf_counter() - start) * 1000
        if ok:
            timings.append(elapsed_ms)
        else:
            failures += 1

    if not timings:
        print("Every request failed.")
        sys.exit(1)

    lines = [
        f"Machine: {platform.system()} {platform.release()}, Python {platform.python_version()}",
        f"Requests: {runs} timed + 1 first request, sent one after another (failures: {failures})",
        "",
        f"first request : {first_ms:7.1f} ms",
        f"mean          : {statistics.mean(timings):7.1f} ms",
        f"median        : {statistics.median(timings):7.1f} ms",
        f"95th percentile: {percentile(timings, 95):6.1f} ms",
        f"fastest       : {min(timings):7.1f} ms",
        f"slowest       : {max(timings):7.1f} ms",
        f"throughput    : {1000 / statistics.mean(timings):7.1f} replies per second (one at a time)",
        "",
        "Not measured here: the avatar's load time and frame rate (see the browser's",
        "Network tab and Performance monitor), and the time the server takes to start.",
    ]
    text = "\n".join(lines)
    print(text)
    with open("performance_results.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("\nSaved performance_results.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=60)
    main(parser.parse_args().runs)
