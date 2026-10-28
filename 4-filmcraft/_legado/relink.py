"""Relink media items to their own path (clears transient MEDIA UNREADABLE on G:). Usage: python relink.py item ..."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
fc = FC()
ms = {m["item"]: m for m in fc.run("media.status")}
for it in map(int, sys.argv[1:]):
    m = ms[it]
    try:
        print(m["name"], fc.run("media.relink", item=it, path=os.path.normpath(m["path"])))
    except Exception as e:
        print(m["name"], "ERR", str(e)[:300])
