#!/usr/bin/env python3
"""Draft tailored replies for open 'Update failure:' issues. Output: posts/github-comment-drafts.json (posting needs an approved identity)."""
import json, re, datetime as dt
from generate import get

MANUAL = "https://docs.openclaw.ai/install/updating/update-methods#alternative-manual-npm-pnpm-or-bun"
ROLLBACK = "https://docs.openclaw.ai/install/updating/rollback-and-recovery"
TROUBLE = "https://docs.openclaw.ai/install/update-troubleshooting"
OLD_UPDATER = ("You're updating *from* {v}. The docs say several failures live in the 2026.9.3/9.4 updater itself, and a newer release can't fix an updater that's already installed, so retrying `openclaw update` tends to fail the same way. "
               f"The documented way out is to do the [manual package-manager update]({MANUAL}) once. Run `openclaw backup create --verify` first, then stop the Gateway through whatever supervises it, install with the same package manager and prefix, run `openclaw doctor --fix`, and restart.")
CODE = {
    "global-install-failed": "`global-install-failed` means the package-manager install, staging, verification or launcher swap exited nonzero, and the updater rolled back. The bounded stderr tail is saved under `logs/support/` in your state directory. That file usually names the real cause (permissions, `--allow-scripts`, a busy disk timeout).",
    "runtime-verification-failed": "`runtime-verification-failed` means the new build installed but its runtime check didn't pass before the deadline. From 2026.9.4, a failure near 300s at `candidate gateway canary` is a known shared-deadline limit (#144858, #154381). A larger `--timeout` doesn't help.",
    "managed-service-preflight": "`managed-service-preflight` means the updater refused before swapping packages because a check on the managed service failed. If this came from `/update` or `update.run` on macOS with \"running inside the gateway process tree\", run `openclaw update` once from a separate Terminal instead.",
    "gateway-recovery-verification": "`gateway-recovery-verification` means that after the failed step, the updater couldn't prove the Gateway recovered.",
    "doctor-failed": "`doctor-failed`: run `openclaw doctor` on the Gateway host, fix what it reports, then retry. Don't delete lock files to force it.",
    "database-schema-preflight": "`database-schema-preflight`: before any retry (a retry overwrites the history), read `lastRun.origin.nextAction` in `openclaw update status --json` and fix the config it names. A newer release can't repair an updater that refuses before staging.",
    "plugin-target-unavailable": "`plugin-target-unavailable`: an enabled npm plugin has no version for the new core. Retry later, pin with `openclaw update --tag <older-version>`, or disable that plugin and retry.",
}
NOT_SERVING = ("Your report says the Gateway is **not serving** after recovery, so the first job is getting it back, not retrying the update:\n"
               "1. `openclaw gateway status --deep` and `openclaw health` show what's actually installed and running.\n"
               "2. Set `OPENCLAW_NO_AUTO_UPDATE=1` in the Gateway environment so the auto-updater doesn't reapply the release while you recover.\n"
               "3. Keep every recovery location named in the update report, and don't run `openclaw update cleanup` yet. The previous package and pre-migration snapshots are retained for exactly this.\n"
               f"4. If the older release refuses the migrated state, the supported path is restoring the pre-update backup with its matching release ([rollback and recovery]({ROLLBACK})).")
SAFE = "Your report says rollback was **verified safe**, so your previous install should still be intact while you sort this out."
FOOTER = ("\n\nFor context: every 2026.9.x stable release currently has open P0 update issues, so holding your current version is reasonable. Per-release counts and a reason-code index: https://swarm-t3.github.io/safebump/failures.html\n\n"
          "If you'd rather have someone do this with you, SafeBump does a fixed-price rescue that you pay for only once it works (details on that page). Either way, I hope the above gets you there.")


def draft(it):
    m = re.match(r"Update failure: (\S+) \((\S+)\)", it["title"])
    code, v = m.group(1), m.group(2)
    body = it.get("body") or ""
    rb = re.search(r"(?:Rollback|Recovery) outcome: (.+)", body)
    rb = rb.group(1) if rb else ""
    parts = []
    if "not serving" in rb:
        parts.append(NOT_SERVING)
    elif "safe to restart" in rb or "verified serving" in rb:
        parts.append(SAFE)
    parts.append(CODE.get(code, f"`{code}` isn't covered in detail by the docs yet. Check the Gateway logs and the saved failure context under `logs/support/` before retrying ([troubleshooting]({TROUBLE}))."))
    if v in ("2026.9.3", "2026.9.4"):
        parts.append(OLD_UPDATER.format(v=v))
    parts.append("Before you retry, `openclaw update status --json` shows the unredacted failing step on your machine. That's the line that tells you which of the above applies.")
    return "\n\n".join(parts) + FOOTER, code, v, rb


def main():
    since = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    res = get("search/issues", {"q": f'repo:openclaw/openclaw is:issue is:open "Update failure:" in:title created:>={since}', "per_page": 100, "sort": "created"})
    out = []
    for it in res["items"]:
        if not re.match(r"Update failure: (\S+) \((\S+)\)", it["title"]):
            continue
        text, code, v, rb = draft(it)
        out.append({"number": it["number"], "url": it["html_url"], "user": it["user"]["login"], "code": code, "version": v,
                    "outcome": rb, "comments": it["comments"], "urgent": "not serving" in rb, "draft": text})
    out.sort(key=lambda x: (not x["urgent"], -x["number"]))
    json.dump(out, open("posts/github-comment-drafts.json", "w"), indent=1)
    print(len(out), sum(x["urgent"] for x in out))
    print(out[0]["url"]); print(out[0]["draft"])


if __name__ == "__main__":
    main()
