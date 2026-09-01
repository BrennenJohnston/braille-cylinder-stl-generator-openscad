# MakerWorld Listing — Embosser Version 2 (ROUGH DRAFT)

> **ROUGH DRAFT — DO NOT PUBLISH YET.** Every block below is either quoted
> verbatim from wording Brennen has already signed off (marked **SIGNED**) or
> is new draft text awaiting his review (marked **DRAFT**). Accessibility
> rule: user-facing text is never finalized without his sign-off. The
> pre-publish checklist is at the bottom.

**Upload file:** `Braille_Cylinder_STL_Generator_EmbosserV2.scad` (repository
root — self-contained, no copy needed; see `makerworld/README.md`).

---

## Listing title — SIGNED (S-V12, 2026-08-28)

> Braille Cylinder STL Generator — Embosser Version 2 (keyed gear pegs, prototype)

---

## Short description — DRAFT

Parametric braille embossing cylinders for the Embosser Version 2 machine.
Type nothing here that isn't braille: paste pre-translated Unicode braille,
pick your card stock, and render both cylinders of a matched pair. Keyed
holes at both ends mean the drive gears cannot be seated in the wrong place.
Double-sided (interpoint) embossing included. Work-in-progress prototype.

---

## Full description — DRAFT (signed passages inset and marked)

This model generates the two rolling cylinders — an Embossing Plate and a
Counter Plate — that press braille dots into business-card stock in the
Embosser Version 2 machine.

**SIGNED (from the Version 2 status note, 2026-08-28):**

> Version 2 is a new embosser design: its drive gears are separate prints
> again, each carrying a differently shaped peg, and each end of each
> cylinder gets a matching keyed hole — so a gear cannot be seated in the
> wrong place.
>
> **It is a work-in-progress prototype.** The cylinder size, the cutout
> shapes and the fit may all change as testing continues. Nothing about it
> is final.

**What each cylinder has** — DRAFT:

- A 30.8 × 54 mm barrel. The extra height is a 1 mm shelf past each edge of
  the 52 mm card, so a card that rolls in slightly off-axis rides the shelf
  instead of ruffling over the cylinder ends.
- A keyed through-hole at each end (family R14: rounded rectangles,
  14 × 14 and 18 × 10 mm on Cylinder A, 16 × 12 and 20 × 8 mm on
  Cylinder B), each mouth countersunk 2 mm at 45°.
- An anti-rotation nub above the top face and a matching socket in the
  bottom face, so all four cylinder ends key against their own gear.
- Up to 4 rows of braille per face, at standard braille spacing
  (2.5 mm dot / 6.5 mm cell / 10 mm line).

**Compatibility warning — DRAFT (facts from the signed status note):**
The holes fit **only gears with R14 pegs** (the v7.2 gear set). None of the
earlier v7 pegs — the six-scallop star, the hexagon, or the 15 × 15 mm
squares — will enter an R14 hole.

**How to use it** — DRAFT:

1. Translate your text at branah.com/braille-translator (Grade 2
   recommended; select **Unicode Braille**, not ASCII). Or use the web app,
   which translates automatically: braille-cylinder-stl-generator.vercel.app
2. Paste the braille into `Line_1`–`Line_4`.
3. Pick `paper_thickness_preset` for your card stock: `0.4mm` (default) or
   `0.3mm`.
4. Render the **Embossing Plate**, then the **Counter Plate** — or set
   `render_both_plates` to `On` and get the pair in one render.
5. For double-sided cards, set `double_sided` to `On` and fill
   `Back_Line_1`–`Back_Line_4`. Each cylinder then carries its own face's
   raised dots plus one recessed seat for every dot the other cylinder
   raises.
6. If a printed gear peg binds in its hole, raise `key_clearance_mm`
   (default 0.110 mm, steps of 0.005) and reprint the cylinder — the nub
   and sockets deliberately do not move with it.

**Print notes — DRAFT, CONFIRM BEFORE PUBLISHING:**

- Print each cylinder standing on end (the keyed sockets are shaped for a
  vertically printed barrel).
- The pair works only as a pair made from one set of settings.
- ⚠ The 54 mm barrel height is not yet print-tested — remove this warning
  only after the first successful 54 mm pair.

---

## Media / images shot list — DRAFT (alt text drafts included, all await review)

| # | Shot | Draft alt text |
|---|------|----------------|
| 1 | Hero: both cylinders side by side, braille dots facing camera | "Two yellow 3D-printed cylinders standing upright, each covered in rows of raised braille dots." |
| 2 | Top face close-up of Cylinder A: keyed hole, countersink, triangle nub | "Close-up of a cylinder's top face showing a square keyed hole with a chamfered mouth and a small triangular nub near the rim." |
| 3 | Gear seated on a cylinder end (requires printed v7.2 gear) | "A printed gear seated flush on the end of a cylinder, its peg inside the keyed hole." |
| 4 | Customizer screenshot: the four Line fields and the preset dropdown | "MakerWorld parameter panel with four braille text fields, a card-stock preset dropdown, and a plate-type choice." |
| 5 | An embossed business card produced by the pair (double-sided if possible) | "A business card held up to raking light, showing crisp embossed braille dots across four rows." |

---

## Suggested tags — DRAFT

braille, accessibility, assistive-technology, embosser, tactile,
business-card, parametric, openscad

---

## Pre-publish checklist (for Brennen)

- [ ] Review and sign every **DRAFT** block above (a11y rule: no
      user-facing text ships unsigned).
- [ ] Print-test a 30.8 × 54 pair; then delete the 54 mm warning.
- [ ] Confirm the print-orientation advice.
- [ ] Take the five photos/screenshots; approve or rewrite the alt text.
- [ ] Decide the listing's license and profile settings on MakerWorld.
- [ ] After posting, update `docs/specifications/EMBOSSER_VERSION_2_KEYED_CUTOUTS_SPECIFICATIONS.md`
      §12 in the web repo ("there is no MakerWorld listing" becomes a link)
      and the status footnote in the web repo's `docs/KNOWN_ISSUES.md`
      (its aside still reads "30.5 × 52" — stale since 2026-08-30).
