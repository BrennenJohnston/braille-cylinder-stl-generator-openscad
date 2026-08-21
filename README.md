# Braille Cylinder STL Generator (OpenSCAD)

Parametric OpenSCAD program for generating braille embossing plates and counter plates for cylindrical objects.

[![STL Validation](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad/actions/workflows/stl-validation.yml/badge.svg)](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad/actions/workflows/stl-validation.yml)

## 🔗 Related Project

This is the **offline OpenSCAD companion** to the web-based Braille STL Generator:

| Version | Link | Use Case |
|---------|------|----------|
| **Web App** | [braille-cylinder-stl-generator.vercel.app](https://braille-cylinder-stl-generator.vercel.app) | Browser-based with automatic translation |
| **OpenSCAD** (this repo) | [github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad) | Offline use, full parametric control |
| **Web App Source** | [github.com/BrennenJohnston/braille-cylinder-stl-generator](https://github.com/BrennenJohnston/braille-cylinder-stl-generator) | Web app source code |

### The device these plates go into

The cylinders this generator produces are the interchangeable plates for the
**Custom Braille Embosser** — a hand-operated braille embosser built from ten
snap-fit 3D-printed parts, with no fasteners, springs, glue, or electronics.
Generate an embossing plate and its matching counter plate at the same card-stock
thickness, print both, and snap them into the holders.

Build files, print profiles, and documentation for the device are on
[Printables](https://www.printables.com/model/1742352-custom-braille-card-embosser-hand-operated),
[MakerWorld](https://makerworld.com/en/models/2881581-custom-braille-card-embosser-hand-operated),
and [Thingiverse](https://www.thingiverse.com/thing:7365273).

### Spin-off Projects

The following repositories were extracted from earlier iterations of this project and are now developed separately:

| Repo | Description |
|------|-------------|
| [braille-wedge-card-openscad](https://github.com/BrennenJohnston/braille-wedge-card-openscad) | Directly readable 3D-printed braille cards, printed leaning at 75° (CHI 2024 optimal angle) with break-away support fins. Incubated here as `experimental/braille-business-card/`. |
| [braille-sign-openscad](https://github.com/BrennenJohnston/braille-sign-openscad) | Two-part ADA-style tactile signs: a raised-letter plate above a braille plate. Split out of the wedge card repo. |
| [braille-charm-openscad](https://github.com/BrennenJohnston/braille-charm-openscad) | Braille charms, pendants, zipper pulls, and bracelet clips. Split out of the wedge card repo. |
| [openscad-plug-puller](https://github.com/BrennenJohnston/openscad-plug-puller) | Parametric OpenSCAD plug puller — an assistive device for gripping and removing electrical plugs (flat tool + heavy-duty clamshell). |
| `cad-to-openscad-pipeline` (private) | Reusable methodology and tooling for converting CAD models into clean parametric OpenSCAD, including the `dxf_to_openscad_polygon` tool. Not published yet. |

## ⚠️ Key Difference

**This OpenSCAD version requires pre-translated Unicode braille text.** It does NOT include automatic translation.

The gap runs one way only. The web app also accepts pre-translated braille — it
has a Braille (Unicode) field whose contents are used verbatim — so the
paste-braille workflow below works in both. Automatic translation is the single
thing you give up by working offline.

---

## 📦 MakerWorld Single-File Build (Alternative)

Want to run this in MakerWorld's **Parametric Model Maker** instead of the
desktop app? A flattened, single-file build lives in
[`makerworld/`](makerworld/):

- [`makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad`](makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad) — one `.scad` file (presets inlined, no `include`), ready to upload. Defaults to the `Rounded` dot shape.
- See [`makerworld/README.md`](makerworld/README.md) for upload steps and the maintainer re-flatten procedure.
- New to the workflow? Start with the [MakerWorld Quick Start Guide](docs/MAKERWORLD_QUICK_START.md) (also as a printable [PDF](docs/MakerWorld_Quick_Start_Guide.pdf)).

The dual-file desktop version in the repository root remains the canonical
source of truth; the MakerWorld file's geometry body is kept byte-identical to
it by `tests/test_makerworld_sync.py`.

---

## 🚀 Quick Start

1. **Translate your text**:
   - Go to https://www.branah.com/braille-translator
   - Select Grade 1 or Grade 2 braille
   - Ensure "Unicode Braille" is selected (NOT ASCII)
   - Type your text and copy the braille output (e.g., ⠓⠑⠇⠇⠕)

2. **Open in OpenSCAD**:
   - Open `Braille_Cylinder_STL_Generator.scad`
   - Open the Customizer panel (View → Customizer)

3. **Configure**:
   - Paste braille into `Line_1`, `Line_2`, etc.
   - Choose `plate_type`: Embossing Plate or Counter Plate
   - Choose `paper_thickness_preset`: 0.4mm, 0.3mm, or Custom
   - Choose `dot_shape`: Rounded or Cone

4. **Generate**:
   - Render: F6 (or Design → Render)
   - Export: File → Export → Export as STL

---

## 📋 What This Makes

- **Cylinder Emboss Plate**: Raised braille dots on cylindrical surface
- **Cylinder Counter Plate**: Recessed support for embossing cylindrical objects
- **Double-Sided Card (BETA)**: the same two plates, paired so that one pass
  embosses braille on **both** faces of a card — see
  [Double-Sided Cards (BETA)](#-double-sided-cards-beta)

## 🎯 Features

### Shape Options
- **Rounded**: Dome-shaped dots with spherical bowl recesses
- **Cone**: Traditional frustum cone dots with matching cone recesses

### Indicator Mode (Visual or Tactile)

`indicator_mode` chooses how each row is marked for alignment. Cylinder
diameter, height, and the polygonal cutout are identical either way — only the
surface features change.

**Visual (default)** — marker cells at the start of every row:
- The triangle alignment indicator is **always generated** — it is critical to
  the mechanical device the cylinder mounts into and has no user-facing toggle
- The `indicators` toggle ("Indicator Letters") controls only the square
  marker next to the triangle
- On: 2 marker cells per row (triangle + square); Off: 1 marker cell
  (triangle only), freeing 1 cell of physical space per row

**Tactile** — a blind-accessible indicator in the seam gap instead:
- A **raised arrow** on the embossing plate and a **matching recess** on the
  counter plate, one per braille row, centred in the gap between the last and
  first cell. That midpoint is always exactly 180°, which is invariant under
  the counter plate's mirroring, so the two self-align at any rotation of the
  paired cylinders
- The arrow **points at the cylinder top**, so you can feel which end is up on
  either plate; raised-vs-recessed tells you which cylinder is the embosser
- **Crush-safe**: the 0.5 mm default raise sits below the 1.0 mm braille dot
  height, so the dots — not the indicator — carry the rolling pressure
- **No marker cells**, so up to 14 text cells fit the default cylinder. The
  Indicator Letters toggle is ignored in this mode
- Five sliders tune it: `tactile_indicator_width` / `_length` / `_raise`, plus
  `tactile_recess_clearance` and `tactile_recess_extra_depth` for the counter
  plate's fit

Text capacity always stays at `grid_columns` in every mode.

### Double-Sided Card (BETA)

`double_sided` pairs the two plates so one pass embosses braille on **both**
faces of a card. Each plate then carries raised dots *and* recesses, every
recess is the 1:1 partner of an actual dot, and the row indicators are forced to
Tactile. Back-of-card text goes in `Back_Line_1` – `Back_Line_10`, still as
pre-translated Unicode braille. Full workflow:
[Double-Sided Cards (BETA)](#-double-sided-cards-beta).

### Paper Thickness Presets
- **0.4mm Preset** (default): Optimized for thicker paper, larger dots
- **0.3mm Preset**: Optimized for thinner paper, smaller dots
- **Custom**: Use manually-entered parameter values

The preset system controls 21 parameters at once (spacing, dot dimensions, cylinder settings) matching the web app's "Card Thickness" dropdown. `grid_columns` and `grid_rows` are deliberately **not** preset-driven: the sliders always govern text capacity, just like the web app's columns/rows dials.

### Parametric Control
All parameters match the web-based generator UI:
- Cylinder dimensions (diameter, height, cutout)
- Braille spacing (cell, line, dot spacing)
- Dot dimensions (separate controls for rounded and cone shapes)
- Counter plate recess dimensions
- Vertical positioning adjustment (Y offset)

---

## 📐 Default Settings

Spacing and dimension defaults match the web app's **0.4mm Paper Thickness
Preset** (applied on load). The default **dot shape is `Rounded`** (the
dropdown still offers `Cone`):

### Cylinder Settings
- Diameter: 30.8mm
- Height: 52mm
- Polygonal Cutout: 13mm radius, 12 points/sides
- Seam Offset: 0°

### Braille Grid
- Cells per row: 13 (available for text; in Visual indicator mode 2 additional cells are reserved when Indicator Letters is On — matches the web app default — or 1 for the triangle alone when Off. Tactile indicator mode reserves none. Either narrower layout fits up to 14 text cells on the default cylinder)
- Number of rows: 4 (`grid_rows`, adjustable up to 10; `Line_1`–`Line_8` are in
  the main Text Input tab and `Line_9`–`Line_10` under **More Braille Lines
  (Advanced)**, because the Customizer cannot add fields on demand)
- Cell spacing: 6.5mm
- Line spacing: 10.0mm
- Dot spacing: 2.5mm

### Dot Dimensions (Rounded - 0.4mm Preset, default shape)
- Base diameter: 1.5mm
- Base height: 0.5mm
- Dome diameter: 1.0mm
- Dome height: 0.5mm

### Counter Plate (Bowl - 0.4mm Preset, default shape)
- Base diameter: 1.8mm
- Depth: 0.8mm

### Dot Dimensions (Cone - 0.4mm Preset, alternative shape)
- Base diameter: 1.5mm
- Height: 0.8mm
- Flat hat diameter: 0.4mm

### Counter Plate (Cone recess - 0.4mm Preset, alternative shape)
- Base diameter: 1.9mm
- Height: 0.7mm
- Flat hat diameter: 1.0mm

---

## 🧩 Double-Sided Cards (BETA)

Set `double_sided` to `On` to emboss braille on **both** faces of one card in a
single pass between the two cylinders. The same two plates take on paired jobs,
and each one then carries raised dots **and** recesses:

- **Cylinder A** = the **Embossing Plate**. The front text as raised dots, plus
  one recessed seat for every back dot the other cylinder raises.
- **Cylinder B** = the **Counter Plate**. The back text as raised dots, plus one
  recessed seat for every front dot Cylinder A raises.

Two things change in this mode. There is **no universal recess grid** — every
recess is the 1:1 partner of an actual dot, so a seat can never sit under this
plate's own raised dot. And the row indicators are always **Tactile** (the
raised seam arrows), because the paired seats occupy the ground the Visual
marker columns would stand on, and a blind user needs the arrow to tell the two
cylinders apart. Choosing Visual while `double_sided` is On is overridden, and
the model says so on the console and in red text above the cylinder.

### Workflow

1. **Translate both sides** at
   [Branah](https://www.branah.com/braille-translator) — same site, same
   grade, **Unicode Braille** output (not ASCII). The back of the card is
   translated exactly like the front; this version still has no automatic
   translation.
2. Paste the front braille into `Line_1`, `Line_2`, … as usual.
3. Open the **`[Double-Sided Card (BETA)]`** tab, set `double_sided` to `On`,
   and paste the back braille into `Back_Line_1` – `Back_Line_10`. **All ten
   back-line fields are in that one tab** — there is no back-side counterpart to
   the front's `[More Braille Lines (Advanced)]` tab.
4. Check `paper_thickness_preset` matches the card stock you will emboss (see
   the footprint table below).
5. **Render each `plate_type` once.** Export the Embossing Plate as
   `Cylinder_A_<your name>.stl` and the Counter Plate as
   `Cylinder_B_<your name>.stl`; the console prints the suggested name for
   whichever plate you are rendering. Both plates must use identical settings —
   they are a matched pair.

Back lines obey the same rules as the front — pre-translated Unicode braille
only, same cell capacity per row, same row limit — and the same
`INVALID CHARACTERS`, `TEXT TOO LONG` and `TOO MANY LINES` warnings cover them,
naming the `Back_Line` that overflowed.

### Interpoint offsets

The two faces are offset from each other so a dot on one side never lands on a
dot on the other. `interpoint_offset_x_mm` and `interpoint_offset_y_mm` both
default to **1.25 mm** and are adjustable over **1.15–1.35 mm**.

Clearance between a raised dot and its neighbouring recess is **widest at
1.25 mm and falls off symmetrically toward both ends** of that range — so if a
guard complains, move both offsets *back toward 1.25 mm*. Increasing or
decreasing is not the fix; 1.15 and 1.35 are equally tight.

### Dot and recess footprints (fixed — no dials)

The double-sided dot and recess sizes are **not adjustable**, and there are no
Customizer dials for them. They are keyed to `paper_thickness_preset`, which is
the thickness of the card stock being embossed:

| `paper_thickness_preset` | raised dot | paired recess (nominal) | recess as printed |
|---|---|---|---|
| `0.3mm` | ⌀1.2 mm, 0.4 mm base + ⌀0.8 mm dome 0.4 mm high (total **0.8 mm**) | ⌀1.3 × 0.5 mm | ⌀1.345 × 0.6725 mm deep |
| `0.4mm` (default) | ⌀1.2 mm, 0.5 mm base + ⌀1.0 mm dome 0.5 mm high (total **1.0 mm**) | ⌀1.4 × 0.5 mm | ⌀1.480 × 0.740 mm deep |

Both packages were settled by physical embossing tests on a Bambu Lab X1C with
a 0.4 mm nozzle during 2026-08, not by calculation. Total dot height is capped
at 1.0 mm because taller dies scrape the embosser's cylinder-holder housing.

The recess is cut as a hemisphere **centred on the shell surface**, which is why
it prints wider and deeper than the nominal figures: `⌀1.4 × 0.5` describes the
shape input, not the hole. The printability guard measures that printed mouth.
On the `0.4mm` package this leaves a renderable offset band of **1.19–1.31 mm**
rather than the slider's full range; the `0.3mm` package accepts all of it.

### Beta status

Double-sided is a **beta**. It has been printed and embossed successfully, and
the geometry is cross-validated against the web app's generator, but it has far
less field use than the single-sided workflow. Report anything odd on the
[issue tracker](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad/issues).

---

## 🖨️ 3D Printing Tips

- **Material**: PLA works well; PETG is more durable
- **Layer Height**: 0.1-0.2mm for smooth dots
- **Infill**: 40%+ recommended for stiffness
- **Perimeters**: 3-4 for strength
- **Orientation**: Print upright as oriented in preview
- **Speed**: Slower outer walls (≤30mm/s) for smoother dots

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [docs/MAKERWORLD_QUICK_START.md](docs/MAKERWORLD_QUICK_START.md) | MakerWorld quick start guide (also as a [PDF](docs/MakerWorld_Quick_Start_Guide.pdf); regenerate with `scripts/generate_quick_start_pdf.py`) |
| [docs/WEB_TO_OPENSCAD_PORTING_GUIDE.md](docs/WEB_TO_OPENSCAD_PORTING_GUIDE.md) | Comprehensive guide for porting web generators to OpenSCAD |
| [docs/QUICK_START_TESTING.md](docs/QUICK_START_TESTING.md) | Quick start guide for the test framework |
| [docs/PARAMETER_MAPPING.md](docs/PARAMETER_MAPPING.md) | Parameter mapping between OpenSCAD and web UI |
| [docs/OPENSCAD_COORDINATE_SYSTEM_SPECIFICATIONS.md](docs/OPENSCAD_COORDINATE_SYSTEM_SPECIFICATIONS.md) | Technical coordinate system documentation |
| [tests/README.md](tests/README.md) | Test framework documentation |

---

## 🧪 Automated Testing

This project includes a comprehensive validation framework that performs OpenSCAD self/regression validation: the current SCAD output is compared against committed reference STLs generated by OpenSCAD (`"generation": { "method": "openscad" }`). True web-reference parity is not currently exercised (the web API is retired), so the references guard against regressions in the OpenSCAD geometry itself.

### Running Tests

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/cross_platform_validation.py -v

# Run with strict tolerances
pytest tests/cross_platform_validation.py --comparison-config=tests/compare_config_strict.json -v
```

### Test Coverage

- **8 core matrix tests**: All combinations of dot shape × plate type × indicators
- **2 indicator isolation tests**: Minimal fixtures for debugging
- **1 parametric variation test**: Custom cutout geometry
- **3 preset/multiline coverage tests**: multiline render, 0.3mm emboss preset, 0.3mm counter preset
- **2 tactile indicator mode tests**: emboss raised arrow, counter recess
- **Customizer validation tests**: Prevent dropdown duplicate issues

This adds up to **16** cross-platform fixtures (`total_test_cases: 16` in `tests/fixtures/cross_platform/test_cases.json`).

See [docs/QUICK_START_TESTING.md](docs/QUICK_START_TESTING.md) for detailed testing instructions.

---

## 🆚 Web App vs. OpenSCAD

### Use Web App When:
- ✅ You need automatic braille translation
- ✅ You want live 3D preview
- ✅ You prefer no software installation
- ✅ You need multi-language support (100+ tables)

### Use OpenSCAD When:
- ✅ You want to work offline
- ✅ You need full parametric control
- ✅ You want to modify/extend the code
- ✅ You have existing OpenSCAD workflows
- ✅ You need version control (plain text files)
- ✅ You want batch processing capability

---

## 🐛 Troubleshooting

### "INVALID CHARACTERS" Warning
- You pasted regular text instead of Unicode braille
- Solution: Translate at Branah.com and copy the braille output

### "TEXT TOO LONG" Warning
- Any of `Line_1`–`Line_10` is longer than the text capacity
- Capacity = `grid_columns` (default 13) in every indicator mode. Visual mode
  widens the grid by 2 cells when Indicator Letters is On (triangle + square)
  or by 1 cell when Off (triangle only), and Tactile mode widens it by none, so
  the text capacity is unchanged either way
- A red `TEXT TOO LONG: <longest line>/<capacity>` extrusion (e.g.
  `TEXT TOO LONG: 16/13`) is rendered above the cylinder whenever the limit
  is exceeded, and the console prints a per-line `echo()` warning such as
  `WARNING: Line_1 uses 16 cells; capacity is 13. Raise grid_columns, split
  across rows, or set text_limit_check = Off.`
- Solutions:
  - Shorten the line, split it across rows, or increase `grid_columns`
  - **Phone numbers:** a 10-digit number formatted per BANA guidance
    (`⠼⠃⠚⠋⠲⠋⠁⠋⠲⠛⠋⠛⠓` for `206.616.7678`) is exactly 13 cells and fits the
    default row. If a longer number will not fit, split it after a period
    and start the next row with a fresh number sign — e.g. `⠼⠃⠚⠋⠲⠋⠁⠋⠲` on
    one row and `⠼⠛⠋⠛⠓` on the next
  - Set `text_limit_check = "Off"` (Text Input section) to bypass the check
    entirely: every pasted cell renders and no warning appears, but rows
    longer than the capacity may crowd the seam gap

### "TOO MANY LINES" Warning
- You filled a `Line_N` past `grid_rows`, which renders only its first
  `grid_rows` rows. Without this warning that text would have gone missing from
  the exported STL with nothing to tell you
- A red `TOO MANY LINES: <deepest filled line>/<grid_rows>` extrusion (e.g.
  `TOO MANY LINES: 7/4`) renders above the cylinder, and the console names the
  value to raise `grid_rows` to
- Solution: raise `grid_rows` (Expert Mode - Braille Spacing) to at least the
  deepest line you filled, and check `cylinder_height_mm` is tall enough to hold
  them — roughly `grid_rows × line_spacing`, so 7 rows needs about 70 mm
- Unlike `TEXT TOO LONG`, this warning has no `text_limit_check` bypass: rows
  past the grid cannot be rendered at any setting

### "TACTILE GAP TOO SMALL" Warning
- Tactile indicator mode only: the seam gap between the last and first cell is
  no longer wide enough for the indicator plus a clear zone either side of it
  (the threshold is `tactile_indicator_width + 5 mm`)
- A red `TACTILE GAP TOO SMALL: <gap>mm` extrusion renders above the cylinder
  on **both** plates, and the console prints the measured gap and the required
  minimum
- At defaults the gap is 18.8 mm at 13 text cells and 12.3 mm at 14; 15 cells
  leaves only 5.8 mm, which trips the warning
- Solutions: lower `grid_columns`, raise `cylinder_diameter_mm`, or narrow
  `tactile_indicator_width`

### Dots Don't Align
- Check `braille_y_adjust` for vertical offset, or `seam_offset_degrees` for angular offset around the cylinder
- Ensure spacing settings match between emboss and counter plates

### Plates Don't Fit Together
- Verify both plates use same `dot_shape` setting
- Check that counter plate dimensions match emboss dimensions
- Ensure `indicator_mode` is the same for both plates — a Visual emboss plate
  and a Tactile counter plate have different row layouts and will not pair
- In Visual mode, ensure the `indicators` (Indicator Letters) setting is the
  same for both plates

### Tactile Indicator Binds or Gets Crushed
- The arrow should nest into the counter recess, never bottom out. At defaults
  the arrow tip sits at radius 15.9 mm and the recess floor at 14.7 mm, leaving
  0.2 mm of radial slack plus a 0.2 mm outline margin
- If the plates bind, raise `tactile_recess_clearance` (outline) or
  `tactile_recess_extra_depth` (depth)
- If the indicator marks the paper too heavily, lower
  `tactile_indicator_raise` — it must stay below the braille dot height so the
  dots carry the rolling pressure
- Deep recesses thin the wall over the polygonal cutout. At defaults that wall
  is 1.224 mm; increasing `tactile_recess_extra_depth` eats into it directly,
  and the `TACTILE WALL TOO THIN` warning below reports when it goes under spec

### "TACTILE WALL TOO THIN" Warning
- Tactile indicator mode with a polygonal cutout only: the wall left between the
  counter plate's arrow recess and the cutout has fallen below the **1.2 mm**
  FDM printable minimum
- A red `TACTILE WALL TOO THIN: <n> mm` extrusion renders above the cylinder,
  and the console prints the measured thickness and the minimum
- This one **warns without stopping the render** — an STL is still written, on
  the same reasoning as `TACTILE GAP TOO SMALL`: an informed user may have a
  reason to thin that wall. Print it and it may split along the cutout
- At defaults the wall is 1.224 mm and clear. It is `tactile_indicator_raise`,
  `tactile_recess_extra_depth` and `polygon_cutout_radius_mm` that eat into it
- Solutions: lower `tactile_indicator_raise` or `tactile_recess_extra_depth`,
  or reduce `polygon_cutout_radius_mm`

### "DOUBLE-SIDED REQUIRES TACTILE" / "DOTS TOO CLOSE" Warnings
- Double-sided only. The first says `indicator_mode` was left on Visual while
  `double_sided` is On; the mode is overridden to Tactile and the render
  continues, so this is a notice rather than a fault
- `DOTS TOO CLOSE: <n> mm` reports the ridge left between a raised dot and its
  neighbouring recess on the same surface. Move **both** interpoint offsets back
  toward **1.25 mm**, where the clearance is widest — 1.15 and 1.35 are equally
  tight, so raising or lowering is not in itself the fix
- If instead the render **stops** with a message about the printable minimum,
  the ridge is under 0.34 mm and no STL can be written. Same fix: back toward
  1.25 mm on both offsets

---

## 📚 References

1. **Web Generator**: https://braille-cylinder-stl-generator.vercel.app
2. **Branah Translator**: https://www.branah.com/braille-translator
3. **BANA Standards**: https://brailleauthority.org/size-and-spacing-braille-characters
4. **NLS Spec 800**: https://www.loc.gov/nls/
5. **ADA Standards**: https://archive.ada.gov/

---

## 🙏 Acknowledgments

- **Brennen Johnston**: Original web-based generator
- **Tobi Weinberg**: Project inception and development support
- **Liblouis**: Professional braille translation library (used in web app)

---

## 📄 License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

- ✅ Free for personal, educational, and non-commercial use
- ✅ Modification and remixing allowed
- ❌ **No commercial use permitted**

See the [LICENSE](LICENSE) file for full terms.

---

## 📞 Support

For issues specific to this OpenSCAD version:
1. [Open an issue](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad/issues) on this repository
2. Check parameter values in Customizer
3. Verify Unicode braille character validity
4. Ensure OpenSCAD version 2024.x or newer (2026.01.03+ recommended)

For general braille embossing questions, see the [web app](https://braille-cylinder-stl-generator.vercel.app).

---

**Version**: 2.6.0  
**Last Updated**: 2026-08-21
