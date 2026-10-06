# SafeBump: is it safe to update OpenClaw?

Live page: https://swarm-t3.github.io/safebump/

Every 4 hours a GitHub Action reads the open issues on [openclaw/openclaw](https://github.com/openclaw/openclaw) and gives each recent release a verdict: **no known blockers**, **caution**, **hold** or **too new**. The verdicts come from the maintainers' own labels (P0, `impact:crash-loop`, `impact:ux-release-blocker`, `bug:crash`) on issues opened in the 14 days after each release that name the version.

- Data: [`docs/data.json`](docs/data.json)
- Generator: [`generate.py`](generate.py) (standard library only; run `python3 generate.py` with `GITHUB_TOKEN` set or `gh` logged in)

## An update broke your agent?

**Update Rescue: $149 fixed, and you pay only once it works.** We get you back to a stable, pinned version with your sessions, memory and channels intact. [Open a rescue request](https://github.com/swarm-t3/safebump/issues/new?template=rescue.yml) or email megafi.app1+safebump@gmail.com.

**Release Watch: $19/month (waitlist).** A per-release verdict for your exact setup before you update. [Join the waitlist](https://github.com/swarm-t3/safebump/issues/new?template=waitlist.yml).

Independent project, not affiliated with OpenClaw.
