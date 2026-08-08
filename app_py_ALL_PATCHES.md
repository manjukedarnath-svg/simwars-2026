# app.py — all pending changes, consolidated (apply once, in order)

Nothing was actually broken by the last deploy — confirmed: the "no scores" issue
was just an empty database (no judge has entered scores yet), not data loss and not
a bug in the patch. But it did surface a real risk worth fixing **before** the event
starts, so that's folded in here too. This replaces the earlier two separate patch
files — apply everything in this one document instead, in this order.

---

## 1. Replace `get_results()`

Matches the actual keys `scoring.html` writes (`score_pals_<team>`, `score_bls_<team>`,
already verified against the live file — confirmed correct in the last investigation).

```python
@app.route('/api/results')
def get_results():
    with get_db() as conn:
        rows = conn.execute('SELECT key, value FROM scores').fetchall()
    sc = {row['key']: row['value'] for row in rows}
    def flt(val, default=0):
        try: return float(val) if val not in (None, '') else default
        except: return default
    ALL_TEAMS = ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12','T13','T14','T15','T16']
    teams = []
    for team in ALL_TEAMS:
        name = (sc.get(f'team_name_{team}') or '').strip() or team
        pals = min(100, flt(sc.get(f'score_pals_{team}')))
        bls  = min(100, flt(sc.get(f'score_bls_{team}')))
        pals_case = sc.get(f'team_pals_case_{team}') or ''
        bls_case  = sc.get(f'team_bls_case_{team}')  or ''
        pals_d3 = flt(sc.get(f'd3_{pals_case}_{team}')) if pals_case else 0
        bls_d3  = flt(sc.get(f'd3_{bls_case}_{team}'))  if bls_case  else 0
        combined = round(pals + bls, 1)
        teams.append({
            'team': team, 'name': name,
            'pals': pals, 'bls': bls, 'combined': combined,
            'pals_d3': pals_d3, 'bls_d3': bls_d3,
        })
    teams.sort(key=lambda t: (-t['combined'], -t['pals'], -(t['pals_d3'] + t['bls_d3'])))
    active = [t for t in teams if t['pals'] > 0 or t['bls'] > 0]
    sf = {t: (sc.get(f'sfName_{t}') or '').strip() or t.upper() for t in ['sf1','sf2','sf3','sf4']}
    fn_names = {t: (sc.get(f'fnName_{t}') or '').strip() or t.upper() for t in ['fin1','fin2']}
    FN_STAGES = {
        'F1': {'stages': [
            [('s1i0',3),('s1i1',4),('s1i2',2),('s1i3',3)],
            [('s2i0',6),('s2i1',5),('s2i2',4)],
            [('s3i0',4),('s3i1',4),('s3i2',2),('s3i3',2)],
            [('s4i0',6)],
        ], 'penalties': [('p0',-8),('p1',-5),('p2',-5),('p3',-4),('p4',-10)],
           'tw': [('tw0',6),('tw1',8),('tw2',8),('tw3',6),('tw4',5),('tw5',7)]},
        'F2': {'stages': [
            [('s1i0',3),('s1i1',3),('s1i2',4),('s1i3',2)],
            [('s2i0',6),('s2i1',5),('s2i2',4)],
            [('s3i0',4),('s3i1',3),('s3i2',2),('s3i3',3)],
            [('s4i0',6)],
        ], 'penalties': [('p0',-8),('p1',-5),('p2',-5),('p3',-4),('p4',-3),('p5',-10)],
           'tw': [('tw0',6),('tw1',8),('tw2',8),('tw3',6),('tw4',5),('tw5',7)]},
    }
    fn_scores = {}
    for t in ['fin1','fin2']:
        fn_scores[t] = {}
        for cid, cd in FN_STAGES.items():
            clin = 0
            for stage in cd['stages']:
                for k, mx in stage:
                    clin += min(mx, max(0, flt(sc.get(f'fn_{cid}_{t}_clin_{k}'))))
            for pk, pts in cd['penalties']:
                if sc.get(f'fn_{cid}_{t}_{pk}') in ('1', 1, True):
                    clin += pts
            clin = max(0, clin)
            tw = sum(min(mx, max(0, flt(sc.get(f'fn_{cid}_{t}_tw_{k}')))) for k, mx in cd['tw'])
            shared = min(15, max(0, flt(sc.get(f'fn_{cid}_{t}_shared'))))
            fn_scores[t][cid] = {'clin': clin, 'tw': tw, 'shared': shared, 'total': clin + tw + shared}
    fn_totals = {t: sum(fn_scores[t][c]['total'] for c in ['F1','F2']) for t in ['fin1','fin2']}
    return jsonify({
        'prelim': active,
        'all_teams': teams,
        'sf': sf,
        'finals': {t: {'name': fn_names[t], 'scores': fn_scores[t], 'total': fn_totals[t]} for t in ['fin1','fin2']},
        'weights': {'policy': 'BLS Domain I x1.25 / Domain II x0.8; PALS unweighted. Fixed — see scoring.html.'},
    })
```

## 2. Fix the homepage widget footer text

In `INDEX_TEMPLATE`'s `rcRender()` JS, find:

```js
h += `<div style="font-size:0.68rem;color:#475569;margin-top:8px;">PALS ×${w.pals} · BLS ×${w.bls} · ${teams.length} of 16 teams scored</div>`;
```

Replace with:

```js
h += `<div style="font-size:0.68rem;color:#475569;margin-top:8px;">Domain-weighted (BLS ×1.25/×0.8, PALS unweighted) · ${teams.length} of 16 teams scored</div>`;
```

## 3. Serve the landing page at `/register`

Put `simwars-2026-landing-page.html` in the repo root, next to `app.py` and
`scoring.html`. Find:

```python
@app.route('/scoring')
def scoring():
    return send_file(os.path.join(os.path.dirname(__file__), 'scoring.html'))
```

Add right after it:

```python
@app.route('/register')
def register():
    return send_file(os.path.join(os.path.dirname(__file__), 'simwars-2026-landing-page.html'))
```

## 4. Fix score persistence before the event (important)

Right now `DB_PATH` is hardcoded next to `app.py`:

```python
DB_PATH = os.path.join(os.path.dirname(__file__), 'scores.db')
```

On Railway, unless a **persistent volume** is attached, the filesystem resets on
every redeploy — meaning every future code push (even a one-line fix) wipes all
scores entered so far. Nothing was lost this time only because no scores had been
entered yet. This WILL bite you mid-event if it's not fixed first.

**Code change** — make the path configurable so a volume can be pointed at it
without touching code again:

```python
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'scores.db'))
```

**Infrastructure step (Railway dashboard — not code, someone with Railway access
has to click this, ~2 minutes):**
1. Railway project → the service running this app → **Settings → Volumes**.
2. Add a volume, mount path e.g. `/data`.
3. Set an environment variable `DB_PATH=/data/scores.db`.
4. Redeploy once. From then on, `scores.db` lives on the volume and survives
   every future deploy.

Do this **before** the event starts — after judges begin entering scores, any
deploy without this fix will erase them.

---

## Apply order
Do all four in one commit if possible, then redeploy once. That avoids doing this
piecemeal across multiple deploys (which is what caused the confusion last time).
