# MakerWorld Single-File Build

This folder contains a **flattened, single-file build** of the Braille Cylinder
STL Generator for uploading to
[MakerWorld](https://makerworld.com/)'s **Parametric Model Maker**.

| File | Purpose |
|------|---------|
| [`Braille_Cylinder_STL_Generator_MakerWorld_v2.scad`](Braille_Cylinder_STL_Generator_MakerWorld_v2.scad) | The single `.scad` file to upload to MakerWorld. |

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
`../Braille_Cylinder_STL_Generator.scad`. The only difference is above that
marker:

- **Inlined presets.** `include <presets.scad>;` is replaced by the contents of
  `presets.scad` between these sentinels:

  ```
  // ==== BEGIN inlined from presets.scad (MakerWorld single-file requirement) ====
  ...
  // ==== END inlined from presets.scad ====
  ```

Both this file and the canonical desktop file default `dot_shape` to `"Rounded"`
and `paper_thickness_preset` to `"0.4mm"` (the dropdowns still offer the other
options).

`tests/test_makerworld_sync.py` guards these invariants in CI.

## Upload steps (MakerWorld Parametric Model Maker)

1. Translate your text at <https://www.branah.com/braille-translator> and copy
   the **Unicode Braille** output (e.g. `⠓⠑⠇⠇⠕`).
2. Go to MakerWorld → **Create** → **Parametric Model Maker** (a.k.a. the
   OpenSCAD-based customizer).
3. Upload **only** `Braille_Cylinder_STL_Generator_MakerWorld_v2.scad`.
4. In the generated parameter panel:
   - Paste braille into `Line_1`, `Line_2`, … (do **not** type plain English).
   - Choose `plate_type`: *Embossing Plate* or *Counter Plate*.
   - Choose `indicator_mode`: `Visual` (default) or `Tactile` — see below.
   - Choose `paper_thickness_preset`: `0.4mm`, `0.3mm`, or `Custom`.
   - `dot_shape` is already set to `Rounded`; switch to `Cone` if preferred.
5. Generate / render and download the STL.

> Tip: generate the **Embossing Plate** and the **Counter Plate** separately
> (same settings, only `plate_type` changes) so the two plates form a matching
> pair.

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
braille dots (0.8 mm vs 1.0 mm) so the dots, not the indicator, take the
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
   `Braille_Cylinder_STL_Generator_MakerWorld_v2.scad` so the two are byte-identical.

2. **Re-sync the Customizer parameters** (the section above the
   `BACKWARD COMPATIBILITY` marker) if any parameter names, defaults, ranges, or
   section headings changed upstream. Both files currently default `dot_shape`
   to `"Rounded"`; if the upstream default ever diverges, decide deliberately
   which default this single-file build should ship.

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
   openscad -o /tmp/mw.stl makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad
   ```

   The sync test confirms the geometry body matches the canonical file and that
   the sentinels + Rounded default are present; the render confirms the file is a
   valid standalone single-file build.
