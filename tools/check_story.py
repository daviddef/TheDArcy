#!/usr/bin/env python3
"""`npm run check:story`: the kit's gate on the family story (/story/), pointed at the right build and the right living list.

    python3 ../tools/check_story.py          # from site/, as the build runs it

The story page is drawn by the kit's StoryBook from site/src/data/story.json, and the kit's checkfamilystory.py holds that
data to its grammar (kit/docs/story.md): every paragraph graded, the world kept apart and sourced, no date beside a living
person, every map dot inside its map, every link resolving, and the BUILT page read back. Two things it cannot do by itself
in this archive, which is why this wrapper exists and does nothing else:

  - it does not read ARCHIVE_OUT, so it is handed the build that tools/outdir.py names (the environment beats the default,
    as everywhere here);
  - it knows the living only from the story's own flags, so it is handed the living list the build itself writes outside the
    repository (tools/build_names_index.py: the names of every noindex person page, plus the private feed where this machine
    has it). In CI that list holds the committed living flags alone, which is what CI can know.

Then the kit's self-test, which plants its faults in the kit's own example and requires each to be caught.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import outdir
import build_names_index as bni

ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
GATE = os.path.join(SITE, "node_modules", "@daviddef", "archive-kit", "kit", "tools", "checkfamilystory.py")


def main():
    dist = outdir.out()
    cmd = [sys.executable, GATE, "--story", os.path.join(SITE, "src", "data", "story.json"), "--dist", dist,
           "--person-base", "/people/"]
    live = bni.paths(dist)[1]
    if os.path.isfile(live):
        cmd += ["--living", live]
    else:
        print("  ..    story      no living list from the build at this path, so the story's own flags alone say who is living")
    r = subprocess.run(cmd)
    if r.returncode:
        return r.returncode
    return subprocess.run([sys.executable, GATE, "--selftest"]).returncode


if __name__ == "__main__":
    sys.exit(main())
