#!/usr/bin/env python3
"""Post approved replies from posts/github-comment-drafts.json. Skips issues a human already answered. Usage: post_comments.py [max] [--dry]"""
import json, os, sys, urllib.request, datetime as dt
import generate

MAX = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5
DRY = "--dry" in sys.argv
BOTS = {"clawsweeper", "github-actions", "openclaw-bot"}
LOG = "posts/posted.jsonl"
done = {json.loads(l)["number"] for l in open(LOG)} if os.path.exists(LOG) else set()
drafts = json.load(open("posts/github-comment-drafts.json"))
posted = 0
for d in drafts:
    if posted >= MAX:
        break
    if d["number"] in done:
        continue
    issue = generate.get(f"repos/openclaw/openclaw/issues/{d['number']}")
    if issue["state"] != "open":
        continue
    comments = generate.get(f"repos/openclaw/openclaw/issues/{d['number']}/comments", {"per_page": 100})
    humans = [c["user"]["login"] for c in comments if c["user"]["type"] != "Bot" and c["user"]["login"] not in BOTS and not c["user"]["login"].endswith("[bot]")]
    if humans:
        print("skip (human replied):", d["number"], humans)
        continue
    print(("DRY " if DRY else "") + "post:", d["url"])
    if DRY:
        posted += 1
        continue
    req = urllib.request.Request(f"https://api.github.com/repos/openclaw/openclaw/issues/{d['number']}/comments",
                                 data=json.dumps({"body": d["draft"]}).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {generate.TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "safebump"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    with open(LOG, "a") as f:
        f.write(json.dumps({"number": d["number"], "comment_url": res["html_url"], "at": dt.datetime.now(dt.timezone.utc).isoformat()}) + "\n")
    posted += 1
print("posted", posted)
