#!/usr/bin/env python3
"""SafeBump: build docs/index.html from open OpenClaw GitHub issues, one verdict per release."""
import datetime as dt
import html
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request

REPO = "openclaw/openclaw"
N_RELEASES = 12
WINDOW_DAYS = 14  # only count issues opened within this many days of the release
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
SEVERE = {"P0", "impact:crash-loop", "impact:ux-release-blocker", "impact:data-loss", "bug:crash"}


def token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


TOKEN = token()


def get(path, params=None):
    url = "https://api.github.com/" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "safebump",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("GitHub API failed: " + path)


def releases():
    rel = [r for r in get(f"repos/{REPO}/releases", {"per_page": 40})
           if not r["draft"] and r["tag_name"].startswith("v20")]
    rel.sort(key=lambda r: r["published_at"], reverse=True)
    return rel[:N_RELEASES]


def issues_for(version, since):
    until = (dt.date.fromisoformat(since) + dt.timedelta(days=WINDOW_DAYS)).isoformat()
    q = f'repo:{REPO} is:issue "{version}" in:title,body created:{since}..{until}'
    items = []
    for page in (1, 2, 3):
        res = get("search/issues", {"q": q, "per_page": 100, "page": page, "sort": "comments"})
        items += res["items"]
        time.sleep(2.2)  # search API: 30 req/min
        if len(res["items"]) < 100:
            break
    return items


def summarise(version, rel):
    published = rel["published_at"][:10]
    items = issues_for(version, published)
    out = []
    for it in items:
        labels = {l["name"] for l in it["labels"]}
        sev = sorted(labels & SEVERE)
        prio = next((p for p in ("P0", "P1", "P2", "P3") if p in labels), "")
        out.append({
            "number": it["number"], "title": it["title"], "url": it["html_url"],
            "state": it["state"], "comments": it["comments"], "created": it["created_at"][:10],
            "prio": prio, "severe": sev, "reactions": it.get("reactions", {}).get("total_count", 0),
        })
    open_ = [i for i in out if i["state"] == "open"]
    open_p0 = [i for i in open_ if i["prio"] == "P0"]
    open_severe = [i for i in open_ if i["severe"]]
    age_h = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00"))).total_seconds() / 3600
    if age_h < 48:
        verdict, why = "too-new", f"Released {int(age_h)}h ago. Most regressions are reported in the first 72h. Wait."
    elif open_p0 or len(open_severe) >= 3:
        verdict, why = "hold", f"{len(open_p0)} open P0 and {len(open_severe)} open crash/blocker issues reported against it."
    elif open_severe:
        verdict, why = "caution", f"{len(open_severe)} open crash/blocker issue(s). Check whether they touch your setup."
    else:
        verdict, why = "ok", "No open P0, crash-loop or release-blocker issues reported against it yet."
    top = sorted(open_, key=lambda i: (bool(i["severe"]), i["prio"] == "P0", i["comments"]), reverse=True)[:8]
    line = "beta" if rel["prerelease"] else ("extended-stable" if re.search(r"extended.stable", (rel.get("body") or "")[:600], re.I) else "stable")
    return {
        "version": version, "line": line, "tag": rel["tag_name"], "published": published, "prerelease": rel["prerelease"],
        "url": rel["html_url"], "age_hours": int(age_h), "issues_total": len(out), "issues_open": len(open_),
        "open_p0": len(open_p0), "open_severe": len(open_severe), "verdict": verdict, "why": why, "top": top,
    }


BADGE = {"ok": ("No known blockers", "#1a7f37"), "caution": ("Caution", "#9a6700"),
         "hold": ("Hold: do not update", "#cf222e"), "too-new": ("Too new: wait", "#6e7781")}


def render(data):
    e = html.escape
    rows, cards = [], []
    for v in data["versions"]:
        label, color = BADGE[v["verdict"]]
        pre = "" if v["line"] == "stable" else f' <small>({v["line"]})</small>'
        rows.append(
            f'<tr><td><a href="v/{e(v["version"])}.html">{e(v["version"])}</a>{pre}</td><td>{v["published"]}</td>'
            f'<td><span class="b" style="background:{color}">{label}</span></td>'
            f'<td>{v["open_p0"]}</td><td>{v["open_severe"]}</td><td>{v["issues_open"]}/{v["issues_total"]}</td></tr>')
        lis = "".join(
            f'<li><a href="{e(i["url"])}">#{i["number"]}</a> {e(i["title"][:110])} '
            f'<small>{e(" ".join(([i["prio"]] if i["prio"] else []) + i["severe"]))} · {i["comments"]} comments</small></li>'
            for i in v["top"]) or "<li>No open issues mention this version yet.</li>"
        cards.append(
            f'<section id="v{e(v["version"])}"><h3>{e(v["version"])}{pre} <span class="b" style="background:{color}">{label}</span></h3>'
            f'<p>{e(v["why"])} <a href="{e(v["url"])}">Release notes</a></p><ul>{lis}</ul></section>')
    best, ext = data.get("recommended"), data.get("recommended_extended")
    rec = ('<p class="rec">' + (f'Newest <b>stable</b> release with no known blockers: <b>{e(best)}</b>.' if best else
           'Every recent <b>stable</b> release has open crash or P0 issues. If yours works, <b>stay where you are</b>.')
           + (f'<br>Newest <b>extended-stable</b> (LTS) release with no known blockers: <b>{e(ext)}</b>. '
              'New installs that need stability can start there with <code>openclaw update --channel extended-stable</code>. '
              'Moving an existing install <i>down</i> from a 2026.9.x release is a downgrade and needs a pre-update backup, '
              'because newer releases migrate your databases.' if ext else '') + '</p>')
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")) as f:
        tpl = f.read()
    return (tpl.replace("{{UPDATED}}", data["generated_at"]).replace("{{REC}}", rec)
            .replace("{{ROWS}}", "\n".join(rows)).replace("{{CARDS}}", "\n".join(cards)))


def version_pages(data):
    e = html.escape
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")) as f:
        tpl = f.read()
    head = tpl.split("<body>")[0] + "<body>"
    offer = '<div class="offer"' + tpl.split('<div class="offer"')[1].split("</div>")[0] + "</div>"
    offer = offer.replace('href="pay.html"', 'href="../pay.html"')
    tail = tpl[tpl.index("<script data-goatcounter"):]
    os.makedirs(os.path.join(OUT, "v"), exist_ok=True)
    for v in data["versions"]:
        label, color = BADGE[v["verdict"]]
        title = f"Is OpenClaw {v['version']} safe to update? Known issues and verdict | SafeBump"
        h = head.replace(head[head.index("<title>"):head.index("</title>") + 8], f"<title>{e(title)}</title>")
        lis = "".join(
            f'<li><a href="{e(i["url"])}">#{i["number"]}</a> {e(i["title"][:140])} '
            f'<small>{e(" ".join(([i["prio"]] if i["prio"] else []) + i["severe"]))} · {i["comments"]} comments · opened {i["created"]}</small></li>'
            for i in v["top"]) or "<li>No open issues mention this version yet.</li>"
        alt = data.get("recommended_extended")
        page = (h + f'<p><a href="../">SafeBump</a> / {e(v["version"])}</p>'
                f'<h1>Is OpenClaw {e(v["version"])} safe to update?</h1>'
                f'<p class="rec"><span class="b" style="background:{color}">{label}</span> {e(v["why"])}</p>'
                f'<p>Line: <b>{e(v["line"])}</b>. Released {v["published"]} (<a href="{e(v["url"])}">release notes</a>). '
                f'Issues opened in the {data["window_days"]} days after release that name this version: {v["issues_total"]}, of which {v["issues_open"]} are still open, '
                f'{v["open_p0"]} open P0 and {v["open_severe"]} open crash-loop or release-blocker. Updated {data["generated_at"]}.</p>'
                f'<h2>Top open issues reported against {e(v["version"])}</h2><ul>{lis}</ul>'
                + (f'<p>Want stability over features? The newest extended-stable (LTS) release without known blockers is <b>{e(alt)}</b>.</p>' if alt else "")
                + '<p>Update already failed? <a href="../failures.html">Look up your reason code</a>.</p>'
                + offer + '<p><a href="../">All releases</a></p>' + tail)
        with open(os.path.join(OUT, "v", v["version"] + ".html"), "w") as f:
            f.write(page)


def main():
    vs = []
    for rel in releases():
        version = rel["tag_name"].lstrip("v")
        vs.append(summarise(version, rel))
    def best(line):
        ok = [v for v in vs if v["line"] == line and v["verdict"] == "ok"]
        return ok[0]["version"] if ok else None
    data = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "repo": REPO, "window_days": WINDOW_DAYS, "recommended": best("stable"),
            "recommended_extended": best("extended-stable"), "versions": vs}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "data.json"), "w") as f:
        json.dump(data, f, indent=1)
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(render(data))
    version_pages(data)
    print(json.dumps([(v["version"], v["verdict"], v["open_p0"], v["open_severe"], v["issues_total"]) for v in vs]))


if __name__ == "__main__":
    main()
