"""
LittleCat screen agent - command line.

    python src/screen_agent --list
    python src/screen_agent --profile littlecat_pong            # play (Ctrl+Alt+P stops)
    python src/screen_agent --profile pong_generic --window "My Game"   # any paddle game, no calibration
    python src/screen_agent --profile pong_generic --window "My Game" --dry-run   # only show what it sees
    python src/screen_agent --from-poc                          # reuse data/screen_agent.json
    python src/screen_agent --bench                             # policies on the built-in Pong

Try it end to end: run `python src/minigames/pong.py` in one terminal and
`python src/screen_agent --profile littlecat_pong` in another.
"""

import argparse
import json
import os
import sys

if __package__ in (None, ""):  # `python src/screen_agent`
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "screen_agent"

from .agent import ScreenAgent, list_profiles, load_profile, profile_from_poc  # noqa: E402


def main():
    from .capture import make_dpi_aware
    make_dpi_aware()   # window coords and captures in the same (physical) pixels
    ap = argparse.ArgumentParser(description="LittleCat screen agent")
    ap.add_argument("--profile", default="littlecat_pong", help="profile name or path to a .json")
    ap.add_argument("--from-poc", action="store_true", help="use the old data/screen_agent.json calibration")
    ap.add_argument("--policy", choices=["predict", "chase", "imitation"], help="override the profile policy")
    ap.add_argument("--window", help="part of the game window's title (overrides the profile)")
    ap.add_argument("--seconds", type=float, default=120.0)
    ap.add_argument("--dry-run", action="store_true", help="perceive and decide, but press no keys")
    ap.add_argument("--list", action="store_true", help="list profiles")
    ap.add_argument("--bench", action="store_true", help="benchmark policies on the built-in Pong")
    args = ap.parse_args()

    if args.list:
        for name in list_profiles():
            print(name)
        return
    if args.bench:
        from .bench import main as bench_main
        bench_main()
        return
    if args.from_poc:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with open(os.path.join(root, "data", "screen_agent.json"), "r", encoding="utf-8") as f:
            profile = profile_from_poc(json.load(f))
    else:
        profile = load_profile(args.profile)
    if args.policy:
        profile["policy"] = args.policy
    if args.window:
        profile["window_title"] = args.window
    ScreenAgent(profile).run(seconds=args.seconds, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
