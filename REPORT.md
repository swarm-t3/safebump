# REPORT r01-a2: SafeBump (OpenClaw update safety and rescue)

## Idea
**Problem:** OpenClaw (openclaw/openclaw, 391k GitHub stars) ships a release every few days, and updates break working agents. Users lose hours, and some lose a running agent.

**Who has it:** self-hosters and small businesses running OpenClaw agents on Mac, Linux or Windows. Sami's own vault shows the same pain inside client work: `topics/pin-openclaw-version-from-day-one.md` says Katzberg lost about 6 hours to the 2026.4.15 regression.

**Evidence (all public, checkable):**
- OpenClaw's built-in "Report update failure" button files public issues titled `Update failure: <reason> (<version>)`. Count since 2026-09-01: **702** (112 in the 7 days to 2026-10-06), by platform macOS arm64 284, Linux x64 192, Windows x64 162. Search: https://github.com/openclaw/openclaw/issues?q=is%3Aissue+%22Update+failure%3A%22+in%3Atitle . Raw counts: https://swarm-t3.github.io/safebump/failures.json
- Most of these get only a bot reply ("Codex review: this still needs some work"), e.g. https://github.com/openclaw/openclaw/issues/166190 , https://github.com/openclaw/openclaw/issues/165594 .
- Loud complaints: https://github.com/openclaw/openclaw/issues/153257 "OpenClaw 2026.9.5 Turned a Stable Environment Into an 8-Hour Failure Recovery Session" (40 comments), https://github.com/openclaw/openclaw/issues/159662 (memory leak of 4-5 GB/h on 2026.9.6).
- Every recent 2026.9.x stable release has dozens of open P0 issues reported in the 14 days after it shipped (2026.9.8: 27, 9.7: 42, 9.6: 64). See https://swarm-t3.github.io/safebump/data.json
- People already pay to have OpenClaw set up and fixed: SetupClaw charges $3,000-6,000 per setup (https://claudemarket.ai/blog/done-for-you-openclaw-setup-for-teams), and Fiverr has many "OpenClaw install/fix" gigs (e.g. https://fiverr.com/mikeyy101/openclaw-setup-open-claw-installation-fix-and-optimize-openclaw-setup).
- Sami's channel evidence: all 4 traceable Upwork wins were OpenClaw implementation jobs (vault `topics/what-wins-upwork-bids.md`).

## What I shipped
- **Live site:** https://swarm-t3.github.io/safebump/ shows a per-release verdict (no known blockers / caution / hold / too new), with the stable and extended-stable lines kept separate.
  - https://swarm-t3.github.io/safebump/failures.html is an index of all update-failure reports by reason code, with a doc-backed "what it means / what to do" for each.
  - 28 reason-code pages (e.g. https://swarm-t3.github.io/safebump/code/global-install-failed.html) and 12 per-version pages (e.g. https://swarm-t3.github.io/safebump/v/2026.9.8.html), all aimed at search.
  - Payment page: https://swarm-t3.github.io/safebump/pay.html (USDT on Arbitrum One, card via Whop on request).
- **Offer:** the $149 Update Rescue, paid only once it works, plus the $19/month Release Watch waitlist with the first month free.
- **Intake:** GitHub issue forms at https://github.com/swarm-t3/safebump/issues/new/choose , which are public and countable, plus email to megafi.app1+safebump@gmail.com.
- **Repo:** https://github.com/swarm-t3/safebump . A GitHub Action (`.github/workflows/refresh.yml`) rebuilds every page every 4 hours from the GitHub API; you can confirm this from the "refresh data" commits.
- **Analytics (public):** https://safebump.goatcounter.com/ shows pageviews and CTA click events (rescue-github, rescue-email, waitlist-github, waitlist-email).
- **Distribution done:** a PR to the awesome-openclaw list (https://github.com/alvinreal/awesome-openclaw/pull/102), IndexNow submission of all sitemap URLs (HTTP 200), and repo topics (openclaw, openclaw-update).
- **Ready to go out once approved:** 45 tailored replies to open update-failure issues (`posts/github-comment-drafts.json`), a dev.to article (`posts/devto-702-update-failures.md`), and Reddit posts (`posts/reddit.md`).

## Results
(to be updated before the deadline)

## Assets left live
(to be updated)

## Learnings
(to be updated)

## Suggestions for Sami
(to be updated)
