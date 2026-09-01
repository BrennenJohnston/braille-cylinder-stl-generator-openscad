# MakerWorld Single-File Build

This folder contains a **flattened, single-file build** of the Braille Cylinder
STL Generator for uploading to
[MakerWorld](https://makerworld.com/)'s **Parametric Model Maker**.

| File | Purpose |
|------|---------|
| [`Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad`](Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad) | The single `.scad` file to upload to the **Version 1** MakerWorld listing. |

## Embosser Version 2 (prototype)

`../Braille_Cylinder_STL_Generator_EmbosserV2.scad` needs **no flattening**: it
was written self-contained, with the preset tables already inlined between the
same `BEGIN`/`END` sentinels and no `include` directive, so the file at the
repository root IS the MakerWorld upload. There is no copy of it in this folder,
and nothing to keep in sync.

**Listing label (S-V12) — signed off by Brennen 2026-08-28; reword only with
his sign-off:**

> Braille Cylinder STL Generator — Embosser Version 2 (keyed gear pegs, prototype)

A note on the version number: this is the **Version 1 model's** MakerWorld
build, labeled **v1.5**. Until 2026-09-01 the file was named `_v2`, where the
suffix meant the second generation of the MakerWorld FILE — a label that
collided confusingly with Embosser **Version 2**, which is different hardware.
The rename ends the collision: `v1.x` suffixes belong to this Version 1 file,
and the Embosser Version 2 upload is the repository root's `_EmbosserV2` file
(above), which keeps no copy in this folder. The listing text for the Version 2
posting lives at [`../docs/MAKERWORLD_V2_LISTING_DRAFT.md`](../docs/MAKERWORLD_V2_LISTING_DRAFT.md).

## Why a separate single-file build?

The canonical desktop generator is a **dual-file** program:

- [`../Braille_Cylinder_STL_Generator.scad`](../Braille_Cylinder_STL_Generator.scad) — main file
- [`../presets.scad`](../presets.scad) — paper-thickness preset tables + lookup helpers, pulled in with `include <presets.scad>;`

MakerWorld's Parametric Model Maker accepts **exactly one** `.scad` file and does
**not** support local `include <...>` directives. The file in this folder is
therefore the main file with the `include <presets.scad>;` line replaced inline
by the body of `presets.scad`, wrapped in `BEGIN`/`END` sentinel comments.

The dual-file split is the canonical, test-covered source of truth; this single
file is an **alternative** build, not the default.

## How this file differs from the canonical desktop file

Everything from the `// BACKWARD COMPATIBILITY` marker to the end of the file
(the entire geometry body) is **byte-identical** to
`../Braille_Cylinder_STL_Generator.scad`, and every parameter default and slider
range above that marker matches it too. The differences are all **presentation**,
all above the marker, and there are four of them:

- **Inlined presets.** `include <presets.scad>;` is replaced by the contents of
  `presets.scad` between these sentinels:

  ```
  // ==== BEGIN inlined from presets.scad (MakerWorld single-file requirement) ====
  ...
  // ==== END inlined from presets.scad ====
  ```

- **A MakerWorld-specific header block** in place of the desktop header.
- **A three-line `dot_shape` comment** explaining this build's Rounded default.
- **`integrated_gears` sits in a `[Hidden]` tab** here instead of a visible one,
  so the Customizer never offers it. The parameter itself is identical in both
  files — only which tab it appears under differs, which is invisible to the
  sync test. See "Integrated gears (BETA) are not in this build" below.

With identical settings the two builds produce byte-identical STLs, single-sided
and double-sided alike. The one exception is integrated gears: the desktop build
can render them and this one cannot, because it has no `assets/` folder and
MakerWorld has no way to supply one. Both files default `dot_shape` to
`"Rounded"` and `paper_thickness_preset` to `"0.4mm"` (the dropdowns still offer
the other options).

`tests/test_makerworld_sync.py` guards these invariants in CI — the geometry
body, all 93 top-level declarations above the marker with their slider ranges,
and the inlined presets block against `../presets.scad`. (That count is what the
test itself reports; if you change the parameter set, take the new number from a
test run rather than by counting lines.)

## Upload steps (MakerWorld Parametric Model Maker)

1. Translate your text at <https://www.branah.com/braille-translator> and copy
   the **Unicode Braille** output (e.g. `⠓⠑⠇⠇⠕`).
2. Go to MakerWorld → **Create** → **Parametric Model Maker** (a.k.a. the
   OpenSCAD-based customizer).
3. Upload **only** `Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad`.
4. In the generated parameter panel:
   - Paste braille into `Line_1`, `Line_2`, … (do **not** type plain English).
   - Choose `plate_type`: *Embossing Plate* or *Counter Plate*.
   - Choose `indicator_mode`: `Visual` (default) or `Tactile` — see below.
   - Choose `paper_thickness_preset`: `0.4mm`, `0.3mm`, or `Custom`.
   - `dot_shape` is already set to `Rounded`; switch to `Cone` if preferred.
   - To get **both** cylinders from one render, set `render_both_plates` to `On`
     (see below) instead of rendering twice.
5. Generate / render and download the STL.

> Tip: you can get the matching pair either way. Set `render_both_plates` to
> `On` and one render gives you both cylinders side by side; or leave it `Off`
> and render the **Embossing Plate** and the **Counter Plate** separately with
> the same settings, changing only `plate_type`. Either way the two plates only
> work as the pair you made from one set of settings.

## Both plates in one render

`render_both_plates` (in **[Plate Selection]**, default `Off`) builds Cylinder A,
the embossing plate, on the left and Cylinder B, the counter plate, on the right
in a single render. `plate_type` is ignored while it is `On`.

`pair_spacing_mm` (default 10) sets the gap between the two barrel **surfaces**,
for laying them out on one print plate. It is not how far apart they sit when
they are working — a meshed pair runs closer than that.

Rendering both plates is roughly twice the work of rendering one, so expect the
preview to take longer.

## Integrated gears (BETA) are not in this build

<!-- Wording signed off by Brennen 2026-08-25; reword only with his sign-off.
     The hardware sentence is his signed S9 text, reused verbatim. -->

The desktop generator can build a cylinder as one piece with its drive gears
already attached. **This MakerWorld build cannot**, and it is not an oversight or
a setting you are missing — the gears are a separate mesh file, and MakerWorld's
Parametric Model Maker has no way to accept one (checked 2026-08-25: its editor
offers no place to attach a model file, and its file picker will not select an
STL at all).

If you want geared cylinders, use either:

- the **desktop OpenSCAD build** — [`../Braille_Cylinder_STL_Generator.scad`](../Braille_Cylinder_STL_Generator.scad),
  which reads its gear meshes from the `assets/` folder beside it, or
- the **web app**, which generates them in the browser.

Everything else on this page — braille, both plates, double-sided cards, the
tactile indicators — works here exactly as it does on the desktop.

> **Before you print geared cylinders anywhere:** they fit only **version 2** of
> the braille embosser hardware. They do not fit version 1 — do not use geared
> cylinders with a version 1 embosser body.

## Double-sided cards (BETA)

The `[Double-Sided Card (BETA)]` tab embosses braille on **both** faces of one
card in a single pass. Set `double_sided` to `On`, translate the back of the
card the same way as the front, and paste it into `Back_Line_1` –
`Back_Line_10` — all ten are in that one tab. Then render each `plate_type`
once: the Embossing Plate is Cylinder A, the Counter Plate is Cylinder B, and
they only work as the pair you rendered from one set of settings.

Row indicators are forced to **Tactile** in this mode, and the double-sided dot
and recess sizes are fixed — they follow `paper_thickness_preset` and there are
deliberately no dials for them. The two interpoint offset sliders default to
1.25 mm each; clearance is widest there and falls off toward both ends of the
1.15–1.35 mm range, so if `DOTS TOO CLOSE` appears, move both back toward
1.25 mm rather than up or down.

One thing to know before you move those sliders here: on the `0.4mm` preset the
offsets that actually render are **1.19–1.31 mm**. Outside that band the ridge
between a dot and its neighbouring recess is too thin to print, and the render
**stops without producing an STL**. MakerWorld's preview has no console, so the
reason is not shown — if a double-sided render produces nothing, put both
offsets back to 1.25 mm. The `0.3mm` preset renders across the whole range.

See the [double-sided section of the main README](../README.md#-double-sided-cards-beta)
for the full workflow and the footprint table.

## Indicator mode: Visual or Tactile

`indicator_mode` decides how each row is marked for alignment. The cylinder's
diameter, height, and cutout are the same either way — only the surface
features change, so **both plates must use the same mode**.

| | Visual (default) | Tactile |
|---|---|---|
| Where | Marker cells at the start of every row | One indicator per row, centred in the seam gap |
| Emboss plate | Recessed triangle (+ square when `indicators` is On) | Raised arrow pointing at the cylinder top |
| Counter plate | Mirrored recesses | Matching arrow recess the arrow nests into |
| Cells used for markers | 2 (On) or 1 (Off) | 0 |
| `indicators` toggle | Controls the square marker | Ignored |

Choose **Tactile** when a blind user needs to align the cylinders unaided: the
arrow is felt as a single continuous wedge, nothing like a braille dot, and its
point tells you which end is up on either plate. Raised-vs-recessed tells you
which cylinder you are holding. The arrow is deliberately lower than the
braille dots (0.5 mm vs 1.0 mm) so the dots, not the indicator, take the
rolling pressure.

Five Tactile-only sliders are available if you need to tune the fit:
`tactile_indicator_width`, `tactile_indicator_length`,
`tactile_indicator_raise`, `tactile_recess_clearance`, and
`tactile_recess_extra_depth`. The defaults are validated; raise the two recess
values if the plates bind.

If a line is long enough to squeeze the seam gap, red 3D text reading
`TACTILE GAP TOO SMALL: <gap>mm` renders above the cylinder on both plates.
Lower `grid_columns` or raise `cylinder_diameter_mm` to clear it.

## Text capacity and the TEXT TOO LONG warning

- Each row holds **13 braille cells of text** by default (`grid_columns = 13`,
  matching the web app). In Visual indicator mode, 2 extra marker cells
  (triangle + square) are added automatically when `indicators` is On, or just
  the always-present triangle cell when Off. Tactile indicator mode adds no
  marker cells at all. Text capacity is unchanged in every case, and either of
  the narrower layouts fits up to 14 text cells on the default 30.8 mm
  cylinder.
- The `grid_columns` / `grid_rows` sliders always govern capacity; the paper
  thickness presets deliberately do **not** override them.
- If any line exceeds the capacity, red 3D text appears above the cylinder
  with counts, e.g. `TEXT TOO LONG: 16/13` (longest line / capacity). The
  MakerWorld preview cannot show console output, so the counts are rendered
  into the warning itself.
- Fixes: shorten or split the line across rows, raise `grid_columns`, or set
  `text_limit_check` to `Off` to bypass the check — every pasted cell then
  renders, but overlong rows may crowd the seam gap.
- **Phone numbers:** formatted per BANA guidance (periods, no parentheses),
  a 10-digit number such as `206.616.7678` is exactly 13 cells
  (`⠼⠃⠚⠋⠲⠋⠁⠋⠲⠛⠋⠛⠓`) and fits one row. For longer numbers, split after a
  period and start the next row with a fresh number sign: `⠼⠃⠚⠋⠲⠋⠁⠋⠲` then
  `⠼⠛⠋⠛⠓`.

See also: [MakerWorld Quick Start Guide](../docs/MAKERWORLD_QUICK_START.md)
([PDF](../docs/MakerWorld_Quick_Start_Guide.pdf)).

## Maintainer: re-flatten procedure

The MakerWorld file must be re-flattened whenever the canonical desktop files
change. Do it manually (no codegen step is committed) and let
`tests/test_makerworld_sync.py` verify the result:

1. **Copy the geometry body.** Open `../Braille_Cylinder_STL_Generator.scad` and
   copy everything **from** the line

   ```
   // =============================================================================
   // BACKWARD COMPATIBILITY - Test System Parameters
   ```

   **to the end of the file**. Paste it over the corresponding region in
   `Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad` so the two are byte-identical.

2. **Re-sync everything else above the marker.** Two parts, both required:

   a. **The Customizer parameters** — if any parameter names, defaults, ranges,
      or section headings changed upstream, copy them across. Both files
      currently default `dot_shape` to `"Rounded"`; if the upstream default ever
      diverges, decide deliberately which default this single-file build should
      ship.

   b. **The `DOUBLE-SIDED (INTERPOINT) MATH` section** — copy it **verbatim**
      from `../Braille_Cylinder_STL_Generator.scad`. Every `DS_*` constant,
      `ds_on`, `_all_back_lines`, the three pure functions, the self-check echo
      block and the three guards. The geometry body you pasted in step 1
      references all of it, so a variant missing this section does not parse.

      **It belongs AFTER the inlined-presets `END` sentinel** (see step 3), not
      before it: `ds_use_03_package` reads `paper_thickness_preset` and
      `ds_printed_ridge_mm` reads both interpoint offset sliders, and OpenSCAD
      evaluates top-level assignments in source order. Put it above them and
      those reads are `undef`.

3. **Re-inline presets if `../presets.scad` changed.** Replace everything between

   ```
   // ==== BEGIN inlined from presets.scad (MakerWorld single-file requirement) ====
   ```

   and

   ```
   // ==== END inlined from presets.scad ====
   ```

   with the body of `../presets.scad` — i.e. its `/* [Hidden] */` directive line,
   both `PRESET_04` / `PRESET_03` tables, and both `preset_lookup` /
   `preset_value` helper functions (skip the file's header comment block).

4. **Verify**:

   ```bash
   pytest tests/test_makerworld_sync.py -v
   openscad -o /tmp/mw.stl makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad
   ```

   The sync test now checks four things, not just the geometry body: the body is
   byte-identical to the canonical file; **every top-level parameter default and
   slider range above the marker matches it** (93 declarations, including all the
   `DS_*` constants from step 2b); the inlined presets block matches
   `../presets.scad`; and the sentinels plus the Rounded default are present. The
   render confirms the file is a valid standalone single-file build.

   Render the double-sided path too — it exercises step 2b, which the body-only
   check cannot see:

   ```bash
   openscad -o /tmp/mw_ds.stl -D 'double_sided="On"' -D 'Back_Line_1="⠙⠑⠋"' \
     makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad
   ```
