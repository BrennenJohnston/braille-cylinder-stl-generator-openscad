# Braille Wedge Card STL Generator (OpenSCAD)

Parametric OpenSCAD generator for **directly readable 3D-printed braille cards**.

The card prints **leaning back at 75°** from the print bed — the angle a CHI 2024
study found significantly faster and more comfortable to read than flat-printed
braille, because near-vertical printing moves the layer seams off the
finger-contact surface. A parametric array of triangular **break-away support
fins** stands behind the card, joined to it by tiny snap-off bridges and grounded
by a built-in brim, so the whole thing prints support-free as **one fused STL**.
After printing, the fins snap off and the card is ready to read.

```text
side view (as it prints, on the bed)

      ●●   <- raised braille dots on the leaning face
     /●●
    / ●●      |\
   /          | \   <- break-away fin (snaps off after printing)
  / card      |  \
 /____________|___\____  bed + built-in brim
        ^ tiny snap-off bridges span the gap
```

## Quick start

1. **Translate your text** at <https://www.branah.com/braille-translator>:
   - Choose Grade 1 or Grade 2 braille.
   - Make sure the output is **Unicode Braille** (dot patterns like `⠓⠑⠇⠇⠕`),
     NOT ASCII Braille.
   - Copy the braille output.
2. **Open `Braille_Wedge_Card_STL_Generator.scad` in [OpenSCAD](https://openscad.org/)**
   (2024.x or newer recommended; nightly builds render fastest) and open the
   Customizer panel (View → Customizer).
3. **Paste the braille** into `Line_1` … `Line_20` under
   *Text Input - Pre-Translated Braille*.
4. **Leave `auto_size_card` = On** (the default): the card face auto-sizes to fit
   your text plus a margin. The effective size is reported in the console —
   the Customizer cannot display computed values in its sliders.
5. **Preview (F5)**. Red floating text above the card means something needs
   fixing (see Troubleshooting below). Warnings are preview-only and are never
   exported.
6. **Render (F6)**, then **File → Export → Export as STL**.
7. **Print as modeled** — no slicer supports, no rotation. See print guidance
   below.

## What the parameters do

| Tab | What it controls |
|-----|------------------|
| Text Input | `Line_1`…`Line_20`, pre-translated Unicode braille |
| Card Size | Auto-size toggle + margin, or manual width/height |
| Warnings | Preview-only red warning text on/off |
| Support Fins | Fin spacing/offset/thickness, bridge count/size/contact, brim |
| Expert Mode - Shape Selection | `Rounded` (ADA-friendly dome, default) or `Cone` dots |
| Expert Mode - Card Shape | Face angle (60–90°, default 75°) and card thickness |
| Expert Mode - Braille Spacing | Cell/line/dot spacing, manual grid capacity |
| Braille Dot Shape - Rounded / Cone | Dot dimensions per shape |
| Rendering Quality | Sphere quality and cone segments |

The default dot (Rounded, 1.6 mm base, 0.7 mm total height) stays inside the
2010 ADA Standards envelope. The defaults for fins and bridges come from a
print-tested configuration.

### More than 20 lines?

`_all_lines` in the `.scad` is the single source of truth. To extend: declare
`Line_21 = "";` in the text-input section, append it to `_all_lines`, and raise
the `grid_rows` slider max. Watch the console for the print-bed size warning —
20 lines at default spacing is already ~209 mm tall.

## Loading the included presets

`Braille_Wedge_Card_STL_Generator.json` sits next to the `.scad` file, so
OpenSCAD auto-loads its parameter sets into the Customizer preset dropdown:

- **Default Card** — the first-run defaults (auto-sized two-line card).
- **Compact Card (manual 75x25)** — business-card footprint with manual sizing
  and a denser print-tested fin/bridge setup.
- **Large 20-Line Card** — a full 20-line auto-sized stress demo (~209 mm tall;
  check your printer's build volume).

Your own saved parameter sets go in the same dropdown via the Customizer's `+`
button. If you keep personal presets (names, contact info in braille), save
them to a file ending in `.local.json` — that pattern is gitignored so they
never end up in a public commit.

## Print guidance

- **Print as modeled.** The card leans back at 75° and the fins stand behind
  it. No slicer supports; a slicer brim is optional (a built-in brim is already
  modeled under each fin).
- **Layer height:** 0.1 mm gives noticeably smoother dots. PLA and PETG both
  work.
- **Slow the outer wall** (≤ 30–40 mm/s) and keep acceleration modest — a thin
  leaning card is sensitive to ringing/vibration. Input shaping helps a lot if
  your printer supports it.
- **Bridge contact tuning:** `bridge_contact_mm` (default 0.3) is how far each
  snap-off bridge merges into the card. 0.3–0.4 mm connects reliably during the
  print and still snaps off clean. If bridges detach mid-print, increase it; if
  they're hard to remove, decrease it.
- **After printing:** flex or snip the fins off the card's back, then deburr
  the small nubs the bridges leave with a fingernail or fine sandpaper.
- **Do not cut lightening holes in the fins** — the extra head motion and
  vibration hurt a thin leaning part more than the saved filament helps.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Red `INVALID CHARACTERS` text in preview | A line contains regular text instead of Unicode braille. Re-translate at Branah with Unicode Braille output. The console says which line. |
| Red `TEXT TOO LONG` / `TOO MANY LINES` | Only possible with `auto_size_card` = Off: a line exceeds `grid_columns` or you used more lines than `grid_rows`. Raise the sliders, shorten the text, or switch auto-size back On. |
| Card bigger than my print bed | The console warns when the effective face exceeds 250 mm. Shorten lines, reduce `auto_size_margin_mm`, or split the text across multiple cards. |
| Fins fall over / bridges break mid-print | Increase `bridge_contact_mm` (up to 0.4), add more `bridge_count`, or reduce `fin_interval_mm` so more fins share the load. |
| Fins won't snap off cleanly | Decrease `bridge_contact_mm` (down to 0.2) or reduce `bridge_width_mm`/`bridge_height_mm`. |
| Dots feel rough | Print at 0.1 mm layers, slow the outer wall, and consider the `Cone` dot shape, which some printers render more cleanly. |

## Upload to MakerWorld (Parametric Model Maker)

The generator is a single `.scad` file with no `include`/`use`, so it uploads
to [MakerWorld](https://makerworld.com/)'s Parametric Model Maker as-is:

1. Go to MakerWorld → **Create** → **Parametric Model Maker** (the
   OpenSCAD-based customizer).
2. Upload **only** `Braille_Wedge_Card_STL_Generator.scad`.
3. In the generated parameter panel, paste Unicode braille into `Line_1`… and
   adjust parameters as in the desktop Customizer.
4. Generate / render and download the STL.

Notes:

- Customizer **`.json` presets do not upload** — MakerWorld only takes the
  `.scad`. The file's built-in defaults (the print-tested "Default Card"
  configuration) are the first-run experience there.
- **License choice at upload (owner decision):** this repository is under
  PolyForm Noncommercial 1.0.0, but MakerWorld requires choosing from its own
  license list (Creative Commons variants etc.), which does not offer PolyForm.
  Pick the closest match deliberately at upload time (e.g. a CC NonCommercial
  variant) — whatever is chosen governs the MakerWorld listing.

## Development / tests

```bash
pip install -r tests/requirements.txt
pytest tests -v
```

- `tests/test_customizer.py` — Customizer dropdown hygiene (no `value:Label`
  format, defaults match options, no duplicates).
- `tests/test_source_guards.py` — source invariants: all 20 `Line_N` params
  exist and are wired into `_all_lines`, warnings stay preview-only (`%`
  modifier), and embossing-era concepts (plate types, counter recesses,
  indicators) stay removed.
- `tests/test_render_smoke.py` — renders four configurations with the OpenSCAD
  CLI and asserts each STL is watertight, single-body, and has the expected
  bounding box (auto-skips if OpenSCAD is not installed).

CI (GitHub Actions) runs lint + the quick tests on every push/PR and the
render smoke tests on Ubuntu with an OpenSCAD nightly AppImage.

## Research background

| Reference | Takeaway |
|-----------|----------|
| [Puerta et al., CHI 2024](https://doi.org/10.1145/3613904.3642719) — "The Effect of Orientation on the Readability and Comfort of 3D-Printed Braille" | Braille printed at 75–90° reads significantly faster and more comfortably than flat; 75° also reduces dot overhangs vs. 90°. This project's whole geometry exists to print at that angle reliably. |
| [masukomi, "Manual Support Fins for 3D Printing"](https://weblog.masukomi.org/2024/03/11/manual-support-fins-for-3d-printing/) | ~1 mm fin offset, a column of small sprues, side fins so edges don't float, 0.3–0.4 mm contact — the fin/bridge defaults follow this. |
| [Slant3D, "Stop Using Slicer Supports"](https://youtu.be/_R2E8VwyNz0) | Triangular fin spaced off the part with thin horizontal prongs and a wide base. |
| [BANA size and spacing](https://brailleauthority.org/size-and-spacing-braille-characters) | Cell geometry and clear-space guidance behind the spacing defaults. |
| [2010 ADA Standards](https://archive.ada.gov/) | Dot dimension envelope the default Rounded dot stays inside. |

Deeper write-ups live in [`docs/`](docs/): print-stability research and path
selection, dot geometry / slicer quality, and the Customizer usability
rationale (auto-size, centering, preview-only warnings).

## Related projects

- [braille-stl-generator-openscad](https://github.com/BrennenJohnston/braille-stl-generator-openscad)
  — the parent project this generator was split from: braille **embossing
  plates** (emboss + counter pairs) for cylindrical objects. The dot geometry
  here was adapted from it.
- [Web-based Braille STL Generator](https://braille-card-and-cylinder-stl-gener.vercel.app)
  — browser-based generator with automatic translation.

## Credits

- **Brennen Johnston** — project owner; original braille STL generator lineage.
- **Puerta, Crnovrsanin, South, Dunne (CHI 2024)** — the orientation research
  this project is built on.
- **masukomi** and **Slant3D** — break-away support fin technique.

## License

**PolyForm Noncommercial 1.0.0** — free for personal, educational, and other
noncommercial use; modification and redistribution allowed under the same
terms; **no commercial use**. See [LICENSE](LICENSE).
