# SIM WARS 2026 — Deploy Bundle (push all of this together, in one commit)

Last deploy only applied the `app.py` edits and left the old `scoring.html` running.
That's why the site still shows "Clinical Assessment 120 + Non-Technical Skills 80,"
"Debriefer Tiebreaker," and "PALS/BLS Weight" sliders at `/scoring` — none of the
Domain I/II/III rework ever actually went live. This bundle fixes that by shipping
everything that depends on each other in one place.

## What's in this folder
1. **`scoring.html`** → replace the existing file of the same name in the repo.
2. **`simwars-2026-landing-page.html`** → new file, add to the repo (same folder as `app.py`).
3. **`app_py_ALL_PATCHES.md`** → 4 small edits to make inside `app.py` itself (not a
   file to copy in — open it and apply each numbered change).

## Why order matters
`app.py`'s `/api/results` endpoint (patch #1 in `app_py_ALL_PATCHES.md`) reads score
keys (`score_pals_T1`, `score_bls_T1`, `d3_<case>_<team>`) that only the **new**
`scoring.html` in this folder actually writes. If the `app.py` patch goes out without
this `scoring.html`, the results widget breaks against the still-old scoring page.
Ship them in the same push.

## Deploy steps
1. Copy `scoring.html` into the repo, overwriting the current one.
2. Copy `simwars-2026-landing-page.html` into the repo (new file).
3. Open `app.py` and apply all 4 changes from `app_py_ALL_PATCHES.md`:
   - Replace `get_results()`
   - Fix the `rcRender()` footer line in `INDEX_TEMPLATE`
   - Add the `/register` route
   - Make `DB_PATH` read from an env var (persistence fix)
4. Commit all of it together, push, let Railway redeploy once.
5. **Before the event**: attach a Railway Volume and set `DB_PATH` per section 4 of
   `app_py_ALL_PATCHES.md`, so future deploys stop wiping scores.

## How to verify it worked
After redeploy, open `https://merry-intuition-production-1788.up.railway.app/scoring`
and confirm you see **"Domain I — Clinical Judgement," "Domain II — Crisis Resource
Management," "Domain III — Global Entrustment"** and a **"Combined-Score Tie-Break
Policy"** card — not "Clinical Assessment 120" or "Debriefer Tiebreaker." If you still
see the old wording, the new `scoring.html` didn't actually get picked up.
