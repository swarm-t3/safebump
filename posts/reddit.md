# Reddit drafts (brand account, once it exists)

## r/openclaw
Title: I counted every "Update failure" report on GitHub since Sept 1: 702 of them. Here's what each reason code means.

Body:
OpenClaw's "Report update failure" button files a public issue titled `Update failure: <reason-code> (<version>)`, so I pulled all of them: 702 since Sept 1, 112 in the last 7 days. By platform: macOS arm64 284, Linux x64 192, Windows 162.

Top codes: global-install-failed (136), runtime-verification-failed (91), plugin-target-unavailable (67), unexpected-error (59), doctor-failed (48).

The thing most people miss: if you're on 2026.9.3 or 9.4, several of these live in the updater you already have installed. Retrying `openclaw update` won't fix them, because a newer release can't repair the old updater. The docs' answer is to do the manual npm/pnpm/bun update once (back up with `openclaw backup create --verify` first, stop the Gateway, install, `openclaw doctor --fix`, restart).

I put it all on one free page, refreshed every 4h, with a per-release "should I update?" verdict and a plain-English fix for each reason code: https://swarm-t3.github.io/safebump/failures.html

Code and data are open: https://github.com/swarm-t3/safebump . If the guidance for a code you've hit is wrong or missing, tell me and I'll fix it.

## r/selfhosted (only if r/openclaw goes well)
Title: Is it safe to update OpenClaw? A free per-release tracker built from the maintainers' own P0/crash-loop labels

Body:
Every recent 2026.9.x stable release has dozens of open P0 issues reported against it in the 14 days after it shipped (2026.9.8: 27, 9.7: 42), while the extended-stable line (2026.8.35) has none. I built a page that recomputes this every 4 hours from the public issue tracker and gives each release a verdict: https://swarm-t3.github.io/safebump/

How it works: a GitHub Action searches openclaw/openclaw for issues that name each version and counts the maintainers' own labels (P0, impact:crash-loop, impact:ux-release-blocker). Mentioning a version doesn't prove the version caused the bug, so it's a signal, not a guarantee. Source: https://github.com/swarm-t3/safebump
