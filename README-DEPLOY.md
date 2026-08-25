# SimWars 2026 — Deploy bundle (26 Aug 2026)

Copy all five files to the **repo root** on `main`, overwriting the existing versions.
Railway redeploys from `main` automatically.

| File | Why it changed |
|---|---|
| `app.py` | PIN removal (judge gate), plus two new routes: `/post-event-prelims` and `/post-event-finals` |
| `scoring.html` | Full-screen judge rubric gate, PIN removed, escape-hatch security fix |
| `simwars-2026-landing-page.html` | Results table + qualifiers, six prize cards with winners, thank-you letter, new Post-Event Feedback block near the top, "Feedback" nav link |
| `simwars-2026-post-event-prelims.html` | NEW — Day 1 feedback form (teams 1–17) |
| `simwars-2026-post-event-semis-finals.html` | NEW — Day 2 feedback form (five semi-finalists, finalists-only section) |

## All five must go together
`app.py` serves the two new form routes; the landing page links to them. Pushing the
landing page without `app.py` gives broken links, and vice versa.

## After deploy — check these URLs
- `/` — landing page, Feedback block visible under the hero
- `/post-event-prelims`
- `/post-event-finals`
- `/scoring` — judge gate opens full-screen with no PIN prompt
- `/questionnaire-post-responses` — submissions arrive tagged `stage: prelims` / `stage: semis-finals`

## Not part of the deploy
`simwars-2026-post-event-prelims-print.html`, `simwars-2026-post-event-semis-finals-print.html`
and `doc-page.js` are the printable paper copies — local/PDF use only, no need to push.

## Still outstanding
Team member names (four per team) for the rosters under each team card on the landing page.
Export from `/questionnaire-responses` and send them over.
