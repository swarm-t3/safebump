#!/usr/bin/env python3
"""SafeBump: index of OpenClaw "Update failure: <reason> (<version>)" reports, grouped by reason code."""
import collections
import datetime as dt
import html
import json
import os
import re
import time

from generate import get, OUT, REPO

DOCS = "https://docs.openclaw.ai"
MANUAL = f"{DOCS}/install/updating/update-methods#alternative-manual-npm-pnpm-or-bun"
TROUBLE = f"{DOCS}/install/update-troubleshooting"

# Plain-English guidance, paraphrased from the official docs (linked). Keep it conservative.
GUIDE = {
    "global-install-failed": (
        "The package manager's install, staging, verification or launcher swap exited with an error, and the updater then tried to roll back.",
        "Check the report's <i>Rollback outcome</i> line, then run <code>openclaw update status</code> and <code>openclaw gateway status --deep</code> to confirm what is actually serving. "
        "The docs name two causes that live in the <b>2026.9.3 and 2026.9.4 updaters themselves</b> (a launcher-permission mismatch on macOS, and a 30-second baseline timeout on busy hosts or slow disks). A newer release can't fix an updater that's already installed, so use the "
        f"<a href=\"{MANUAL}\">manual npm/pnpm/bun procedure</a> once. Back up first, then stop the Gateway, install, run Doctor, and restart."),
    "runtime-verification-failed": (
        "The new version installed, but its runtime check (often the candidate Gateway canary) didn't pass before the deadline.",
        "If you're updating <b>from 2026.9.4</b> and it fails near 300 seconds, that's a known updater limit: the deadline is shared across checks, even with a larger <code>--timeout</code>. "
        f"The docs recommend the <a href=\"{MANUAL}\">manual package-manager procedure</a>, then <code>openclaw doctor --fix</code> and a Gateway restart."),
    "plugin-target-unavailable": (
        "An enabled npm plugin has no version that resolves for the new core, or its registry metadata couldn't be read. The update refuses <i>before</i> it changes anything.",
        "Retry later, pin the core with <code>openclaw update --tag &lt;older-version&gt;</code>, or disable that plugin and retry. Older updaters can refuse before the new code runs. In that case, use the manual method and then <code>openclaw update repair</code>."),
    "doctor-failed": (
        "The Doctor maintenance step found something it couldn't fix during the update.",
        "Run <code>openclaw doctor</code> on the Gateway host, resolve what it reports, then retry. Don't delete lock files to force it through."),
    "finalize:doctor": (
        "The update landed, but Doctor couldn't enter maintenance at the end, usually because a running Gateway still owns the state directory.",
        "Resolve the ownership problem it names, then run <code>openclaw update repair</code>. Check <code>openclaw update status --json</code> and <code>openclaw gateway status --deep</code> for pending migrations. Never delete lock files."),
    "managed-service-preflight": (
        "The updater refused before swapping packages because a check on the managed Gateway service failed.",
        "<b>2026.9.4 updaters</b> can refuse here before the target code ever runs. The fix is to use the "
        f"<a href=\"{MANUAL}\">manual procedure</a> with the same package manager and prefix. On macOS, if <code>/update</code> or <code>update.run</code> failed with \"running inside the gateway process tree\", run <code>openclaw update</code> once from a separate Terminal."),
    "database-schema-preflight": (
        "The updater refused because a database or config schema check failed before staging.",
        "Before you retry (a retry overwrites the history), run <code>openclaw update status --json</code> and read <code>lastRun.origin.nextAction</code>. Fix the configuration it names first, because a newer release can't repair an updater that refuses before staging."),
    "post-update-plugins": (
        "The core update succeeded, but plugin maintenance afterwards reported a problem.",
        "Your core version is new. Follow the guidance under <code>postUpdate.plugins.warnings</code> in <code>openclaw update status --json</code>, usually <code>openclaw plugins update &lt;id&gt;</code>."),
    "gateway-recovery-verification": (
        "After a failed step, the updater couldn't verify that the Gateway recovered.",
        "Run <code>openclaw gateway status --deep</code> to see what is serving and on which version before you retry anything."),
    "unexpected-error": (
        "An error with no specific reason code.",
        "Check the Gateway logs and the saved failure context under <code>logs/support/</code> in your state directory before retrying."),
}

HOP = ('<p class="rec"><b>Stuck on 2026.9.3 or 2026.9.4?</b> The OpenClaw maintainer\'s own recipe '
       '(<a href="https://github.com/openclaw/openclaw/issues/165706">#165706</a>) is one manual hop to the current release, then a Doctor pass: '
       '<code>npm install -g openclaw@2026.9.8 --allow-scripts=openclaw</code>, then <code>openclaw doctor --fix</code>, then <code>openclaw gateway restart</code>. '
       'From 2026.9.8 onward, <code>openclaw update</code> handles the rest. On npm 11.15 or older, drop <code>--allow-scripts=openclaw</code>. Back up first with <code>openclaw backup create --verify</code>.</p>')


def fetch():
    items = []
    for page in range(1, 11):
        res = get("search/issues", {"q": f'repo:{REPO} is:issue "Update failure:" in:title',
                                    "per_page": 100, "page": page, "sort": "created"})
        items += res["items"]
        time.sleep(2.2)
        if len(res["items"]) < 100:
            break
    return items


def main():
    items = fetch()
    groups = collections.defaultdict(list)
    per_day = collections.Counter()
    plat = collections.Counter()
    for it in items:
        m = re.match(r"Update failure: ([a-z][^\s(]*) \((\S+)\)", it["title"])
        if not m:
            continue
        pm = re.search(r"Platform: (\S+)", it.get("body") or "")
        groups[m.group(1)].append({"n": it["number"], "v": m.group(2), "state": it["state"],
                                   "reason": it.get("state_reason"), "created": it["created_at"][:10],
                                   "url": it["html_url"], "platform": pm.group(1) if pm else "?"})
        per_day[it["created_at"][:10]] += 1
        plat[pm.group(1) if pm else "?"] += 1
    total = sum(len(g) for g in groups.values())
    last7 = sum(c for d, c in per_day.items()
                if d >= (dt.date.today() - dt.timedelta(days=7)).isoformat())
    order = sorted(groups, key=lambda k: -len(groups[k]))
    e = html.escape
    toc, secs = [], []
    for code in order:
        g = groups[code]
        if len(g) < 3 and code not in GUIDE:
            continue
        open_n = sum(1 for x in g if x["state"] == "open")
        vers = collections.Counter(x["v"] for x in g).most_common(4)
        toc.append(f'<tr><td><a href="code/{re.sub(r"[^a-z0-9-]", "-", code.lower())}.html">{e(code)}</a></td><td>{len(g)}</td><td>{open_n}</td>'
                   f'<td>{e(", ".join(f"{v} ({c})" for v, c in vers))}</td></tr>')
        what, do = GUIDE.get(code, ("No plain-English summary yet.", f"See the <a href=\"{TROUBLE}\">update troubleshooting docs</a>."))
        recent = "".join(f'<li><a href="{e(x["url"])}">#{x["n"]}</a> {e(x["v"])} · {e(x["platform"])} · {x["created"]} · {x["state"]}'
                         f'{" (" + e(x["reason"]) + ")" if x["state"] == "closed" and x["reason"] else ""}</li>' for x in g[:6])
        secs.append(f'<section id="{e(code)}"><h3><code>{e(code)}</code>: {len(g)} reports, {open_n} still open</h3>'
                    f'<p><b>What it means:</b> {what}</p><p><b>What to do:</b> {do}</p>'
                    f'<details><summary>Latest reports</summary><ul>{recent}</ul></details></section>')
    data = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "total": total,
            "last7": last7, "first": min(per_day) if per_day else None, "platforms": plat.most_common(),
            "per_day": sorted(per_day.items()), "codes": {k: len(v) for k, v in groups.items()}}
    with open(os.path.join(OUT, "failures.json"), "w") as f:
        json.dump(data, f, indent=1)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures_template.html")) as f:
        tpl = f.read()
    out = (tpl.replace("{{UPDATED}}", data["generated_at"]).replace("{{TOTAL}}", str(total))
           .replace("{{LAST7}}", str(last7)).replace("{{FIRST}}", str(data["first"]))
           .replace("{{PLATFORMS}}", e(", ".join(f"{p} {c}" for p, c in plat.most_common(5))))
           .replace("{{TOC}}", "\n".join(toc)).replace("{{SECTIONS}}", "\n".join(secs)))
    with open(os.path.join(OUT, "failures.html"), "w") as f:
        f.write(out)
    head = tpl.split("<body>")[0] + "<body>"
    offer = '<div class="offer">' + tpl.split('<div class="offer">')[1].split("</div>")[0] + "</div>"
    tail = tpl[tpl.index("<script data-goatcounter"):] if "goatcounter" in tpl else "</body></html>"
    os.makedirs(os.path.join(OUT, "code"), exist_ok=True)
    pages = []
    for sec, code in zip(secs, [c for c in order if len(groups[c]) >= 3 or c in GUIDE]):
        slug = re.sub(r"[^a-z0-9-]", "-", code.lower())
        title = f"OpenClaw update failed with {code}: what it means and how to fix it | SafeBump"
        h = (head.replace(head[head.index("<title>"):head.index("</title>") + 8], f"<title>{e(title)}</title>")
             .replace('href="./"', 'href="../"'))
        page = (h + f'<p><a href="../">SafeBump</a> / <a href="../failures.html">update failures</a> / {e(code)}</p>'
                + f"<h1>OpenClaw update failure: <code>{e(code)}</code></h1>" + sec.replace("<details>", "<details open>")
                + (HOP if any(v in ("2026.9.3", "2026.9.4") for v, _ in collections.Counter(x["v"] for x in groups[code]).most_common(3)) else "")
                + '<p class="rec">Before you retry, <code>openclaw update status --json</code> shows the unredacted failing step on your machine, and <code>openclaw gateway status --deep</code> shows what is actually serving. A retry overwrites that history.</p>'
                + offer.replace('href="pay.html"', 'href="../pay.html"').replace('href="https://github.com/swarm-t3/safebump/issues/new?template=rescue.yml"', 'href="https://github.com/swarm-t3/safebump/issues/new?template=rescue.yml&title=%5BRescue%5D+' + e(code) + '"')
                + f'<p><a href="../failures.html">All reason codes</a> · <a href="../">Is it safe to update? Per-release verdicts</a></p>' + tail)
        with open(os.path.join(OUT, "code", slug + ".html"), "w") as f:
            f.write(page)
        pages.append(f"code/{slug}.html")
    base = "https://swarm-t3.github.io/safebump/"
    vdir = os.path.join(OUT, "v")
    vpages = sorted("v/" + n for n in os.listdir(vdir)) if os.path.isdir(vdir) else []
    urls = ["", "failures.html", "pay.html"] + vpages + pages
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "".join(f"<url><loc>{base}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    print(total, last7, order[:8])


if __name__ == "__main__":
    main()
