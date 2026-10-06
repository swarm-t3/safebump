---
title: "702 OpenClaw update failures in five weeks: what the reason codes mean and what to do"
tags: openclaw, ai, selfhosted, devops
canonical_url: https://swarm-t3.github.io/safebump/failures.html
---

OpenClaw added a **Report update failure** button. Each click files a public issue on openclaw/openclaw titled `Update failure: <reason-code> (<version>)`. That makes the update experience measurable, so I counted.

**Since 2026-09-01: 702 reports, 112 of them in the last 7 days.** By platform: macOS arm64 284, Linux x64 192, Windows x64 162. Those are only the people who clicked the button.

## The top reason codes

| Reason code | Reports |
|---|---|
| global-install-failed | 136 |
| runtime-verification-failed | 91 |
| plugin-target-unavailable | 67 |
| unexpected-error | 59 |
| doctor-failed | 48 |
| finalize:doctor | 40 |
| managed-service-preflight | 32 |
| post-update-plugins | 23 |

## The one thing most people miss

If you're on **2026.9.3 or 2026.9.4**, several of these failures live in *the updater you already have installed*. The docs say so directly: a later release can't rescue the updater already installed. So retrying `openclaw update` gives you the same failure, however many times you run it.

What the docs recommend is to run the [manual npm, pnpm or bun procedure](https://docs.openclaw.ai/install/updating/update-methods#alternative-manual-npm-pnpm-or-bun) once:

1. Back up your state directory. Newer releases migrate your SQLite databases, and older releases can't open them.
2. Stop the Gateway through whatever actually supervises it (launchd, systemd, Scheduled Task or a foreground process).
3. Install with the same package manager and prefix you used originally, for example `npm i -g openclaw@latest --allow-scripts=openclaw` (on npm 11.15 and earlier, drop `--allow-scripts`).
4. Run `openclaw doctor --fix`, then restart through the same supervisor.

Before you retry anything, read what actually happened: `openclaw update status --json` shows the failing step and `lastRun.origin.nextAction`, and `openclaw gateway status --deep` shows what is really serving. A retry overwrites that history.

## Should you update right now?

I also track open P0, crash-loop and release-blocker issues opened in the 14 days after each release. At the time of writing, every recent 2026.9.x stable release has dozens of open P0 issues reported against it (2026.9.8: 27). The extended-stable line (2026.8.35) has none. If your agent works, holding your version is a reasonable choice.

The full breakdown, with a plain-English "what it means / what to do" for each reason code, is at https://swarm-t3.github.io/safebump/failures.html . It refreshes every 4 hours from the public issue tracker. The per-release verdicts are at https://swarm-t3.github.io/safebump/ , and the code is open: https://github.com/swarm-t3/safebump

If an update has already broken your agent and you'd rather not spend the evening on it, SafeBump does a fixed-price rescue that you pay for only once it works. Details are on the page.
