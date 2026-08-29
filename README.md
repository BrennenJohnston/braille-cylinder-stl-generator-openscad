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

## ⚙️ Integrated Gears (BETA)

<!-- Wording signed off by Brennen 2026-08-25; reword only with his sign-off.
     The hardware sentence is his signed S9 text, reused verbatim. -->

> **Hardware compatibility, before anything else:** integrated gears fit only
> **version 2** of the braille embosser hardware. They do not fit version 1 — do
> not use geared cylinders with a version 1 embosser body. (A link to the
> version 2 build files will be added here once they are published.)

Set `integrated_gears` to `On` in the **[Integrated Gears (BETA)]** tab and the
cylinder is built as **one solid piece with its drive gears already attached**,
instead of a bare barrel you push separately printed gears onto. Meshed gears
are also what keeps a paired set turning together.

**This build only.** The gear meshes are real files —
`assets/gears_a.stl` and `assets/gears_b.stl` — which must sit in an `assets/`
folder beside the `.scad`. That is why the MakerWorld single-file build does not
offer this; see [`makerworld/README.md`](makerworld/README.md).

Things worth knowing before you switch it on:

- **The cylinder size is fixed while gears are on: 30.8 mm × 52 mm.** The gears
  are a 1:1 replica of the reference set, baked at fixed heights, and they do
  not move with the barrel. Any other size is **refused with an error** rather
  than silently mis-built — a shorter barrel would export as three loose pieces
  and a taller one would swallow the teeth. Both paper-thickness presets already
  set this size, so the shipped defaults pass.
- **The barrel prints solid.** The polygonal cutout is dropped while gears are
  on, and the console says so if you had one set. A one-piece roller has no
  through-path along its axis anyway — the gear bores are blind pockets — so
  keeping the cutout would seal a cavity nothing can reach or drain.
- The gears are **not adjustable**. They replicate the reference set exactly, so
  that a roller printed here meshes with one printed from the web app.

## 🔄 Rendering Both Plates At Once

`render_both_plates = On` (in **[Plate Selection]**) builds the **complete pair
in one render** — Cylinder A, the embossing plate, on the left, and Cylinder B,
the counter plate, on the right — instead of rendering each plate separately and
switching `plate_type` between them. `plate_type` is ignored while it is On.

`pair_spacing_mm` (default 10) is the gap between the two barrel **surfaces**,
for laying them out on one print plate. It is not the assembly distance: a
meshed pair runs at a 32.0473 mm axis distance. With gears on, the teeth
overhang the barrel, so a 10 mm barrel gap leaves about **8.58 mm tip to tip**.

Rendering both plates is heavier than rendering one, which is normal — see
Troubleshooting below if the preview feels slow.

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

### Embosser Version 2 (prototype)

`Braille_Cylinder_STL_Generator_EmbosserV2.scad` at the repository root
generates cylinders for **Embosser Version 2**, a new hardware design whose four
drive gears each carry a differently shaped peg. The file cuts a matching keyed
through-hole at each end of the cylinder, so a gear cannot be seated in the
wrong place, plus a key nub on the Embossing Plate's top face.

It is a **work-in-progress prototype**: the cylinder size, the cutout shapes and
the fit may change as testing continues.

**The gears must be re-cut to match.** The holes are family R14 — rounded
rectangles of 14 x 14 mm (Cylinder A's top, the nub end), 18 x 10 (A's bottom),
16 x 12 (B's top) and 20 x 8 (B's bottom), each with a 0.5 mm corner radius.
None of the earlier star, hexagon or 15 x 15 mm square pegs will enter an R14
hole, so a cylinder printed from this file pairs only with gears cut to the R14
spec.

One dial is new: **Key clearance (`key_clearance_mm`)**, 0.15 mm per side by
default and adjustable from 0 to 0.5 mm. It grows every hole outward and shrinks
the nub inward by the same amount. Raise it if the pegs bind; raising it also
eats into the margin that stops a peg entering the wrong hole (0.85 mm at the
default, 0.50 mm at the maximum).

The Version 1 files are untouched and remain the default. Use
`Braille_Cylinder_STL_Generator.scad` unless you are building the Version 2
embosser. **The same Version 2 file is also the MakerWorld upload** — it is
self-contained, with the preset tables inlined and no `include` directive.

## Rendering feels very slow

**First check which OpenSCAD you are in** (Help → About). This project needs
the **Nightly** build with the Manifold engine; the stable **2021.01** release
renders the counter plate through CGAL and takes the better part of an hour
for what Nightly finishes in about **2 seconds** (measured 2026-08-25 on the
same machine, same file: Nightly 1.8 s; 2021.01 was still rendering when it
was stopped at 45 minutes). If a render sits at a progress bar for minutes,
you are almost certainly in 2021.01 — open the file in Nightly instead.

**Second check, if F6 takes minutes even in Nightly**: the GUI can be set to
the old CGAL engine. Open **Edit → Preferences → Advanced** and make sure the
3D rendering backend is **Manifold** (on the Features tab, anything named
manifold should be enabled). The ~2-second numbers below are Manifold numbers;
the same render through CGAL is the better part of an hour.

Inside Nightly, the two speeds you experience are different things:

- **Render / F6 / export** builds exact geometry once. Measured at the shipped
  defaults: embossing plate ≈ 0.3 s, counter plate ≈ 2 s (its universal grid
  subtracts 312 recess spheres no matter how much text there is), High quality
  counter plate ≈ 10 s. This is the number that matters for the STL.
- **Preview / F5** redraws the boolean tree on **every frame while you rotate
  or zoom** (OpenCSG). A single frame of the counter plate costs roughly
  0.5–1 s, so rotation can feel like 1–2 frames per second even though nothing
  is wrong. The preview after a Customizer change pays the same price once.

What helps:

- Do design passes on the **embossing plate** (fast everywhere) and render the
  counter plate when you need it.
- For a smoother preview while editing, set `render_quality = "Low"`
  (Rendering Quality section) — **and set it back to your intended quality
  before exporting**, because unlike a preview-only trick this genuinely
  changes the exported dot tessellation.
- Trust F6 for the real result: a slow, choppy preview does not make the
  exported STL any worse.

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
4. Use an OpenSCAD **Nightly** build with the Manifold engine (2026.01.03 is
   what CI pins). This is stronger than a minimum-version note: the stable
   2021.01 release renders the counter plate in tens of minutes where Nightly
   takes about two seconds — see [Rendering feels very slow](#-troubleshooting)
   if that is what you are seeing

For general braille embossing questions, see the [web app](https://braille-cylinder-stl-generator.vercel.app).

---

**Version**: 2.7.0  
**Last Updated**: 2026-08-23
