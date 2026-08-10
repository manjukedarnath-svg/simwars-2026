# Case investigation images (CXR / Echo / CT)

Drop real CXR, echo/POCUS, and CT images into the matching case folder here
(`B1`–`B4`, `P1`–`P4`, `SF1`, `SF2`, `F1`, `F2`). Nothing else needs to change —
the case page auto-detects any image file in a case's folder and shows it as
a "Push to Display" card.

**ECG rhythm is not included here** — that stays on the physical patient
monitor/simulator during the scenario, not pushed to the projector.

## Naming convention

`<order>_<label>.jpg` (or `.png` / `.jpeg` / `.webp` / `.gif`)

- The leading number controls the order the images appear in (01, 02, 03…).
- Everything after the number becomes the on-screen label — underscores/dashes
  become spaces, and it's title-cased automatically.

Examples for case `P1`:

```
static/investigations/P1/01_cxr-admission.jpg      -> "Cxr Admission"
static/investigations/P1/02_echo-stage2.jpg         -> "Echo Stage2"
static/investigations/P1/03_ct-head-stage3.jpg      -> "Ct Head Stage3"
```

If a folder has no images yet, the case page just shows a small note —
everything else (handover, stages, text-based labs console) works exactly
as before. Add images whenever they're ready; no redeploy logic changes
needed, just upload the files to the matching case folder in this repo
(or via the GitHub web upload flow, same as any other file).
