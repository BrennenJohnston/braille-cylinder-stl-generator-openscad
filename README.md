# Braille Cylinder STL Generator (OpenSCAD)

Parametric OpenSCAD program for generating braille embossing plates and counter plates for cylindrical objects.

[![STL Validation](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad/actions/workflows/stl-validation.yml/badge.svg)](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad/actions/workflows/stl-validation.yml)

## 🔗 Related Project

This is the **offline OpenSCAD companion** to the web-based Braille STL Generator:

| Version | Link | Use Case |
|---------|------|----------|
| **Web App** | [braille-card-and-cylinder-stl-gener.vercel.app](https://braille-card-and-cylinder-stl-gener.vercel.app) | Browser-based with automatic translation |
| **OpenSCAD** (this repo) | [github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad) | Offline use, full parametric control |
| **Web App Source** | [github.com/BrennenJohnston/braille-cylinder-stl-generator](https://github.com/BrennenJohnston/braille-cylinder-stl-generator) | Web app source code |

### Spin-off Projects

The following repositories were extracted from earlier iterations of this project and are now developed separately:

| Repo | Description |
|------|-------------|
| [braille-wedge-card-openscad](https://github.com/BrennenJohnston/braille-wedge-card-openscad) | Directly readable 3D-printed braille cards, printed leaning at 75° (CHI 2024 optimal angle) with break-away support fins. Incubated here as `experimental/braille-business-card/`. |
| [openscad-plug-puller](https://github.com/BrennenJohnston/openscad-plug-puller) | Parametric OpenSCAD plug puller — an assistive device for gripping and removing electrical plugs (flat tool + heavy-duty clamshell). |
| `cad-to-openscad-pipeline` (private) | Reusable methodology and tooling for converting CAD models into clean parametric OpenSCAD, including the `dxf_to_openscad_polygon` tool. Not published yet. |

## ⚠️ Key Difference

**This OpenSCAD version requires pre-translated Unicode braille text.** It does NOT include automatic translation.

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
- **Crush-safe**: the 0.8 mm default raise sits below the 1.0 mm braille dot
  height, so the dots — not the indicator — carry the rolling pressure
- **No marker cells**, so up to 14 text cells fit the default cylinder. The
  Indicator Letters toggle is ignored in this mode
- Five sliders tune it: `tactile_indicator_width` / `_length` / `_raise`, plus
  `tactile_recess_clearance` and `tactile_recess_extra_depth` for the counter
  plate's fit

Text capacity always stays at `grid_columns` in every mode.

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
- Number of rows: 4
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
- Any of `Line_1`–`Line_4` is longer than the text capacity
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
  the arrow tip sits at radius 16.2 mm and the recess floor at 14.4 mm, leaving
  0.2 mm of radial slack plus a 0.2 mm outline margin
- If the plates bind, raise `tactile_recess_clearance` (outline) or
  `tactile_recess_extra_depth` (depth)
- If the indicator marks the paper too heavily, lower
  `tactile_indicator_raise` — it must stay below the braille dot height so the
  dots carry the rolling pressure
- Deep recesses thin the wall over the polygonal cutout. At defaults that wall
  is ~0.93 mm; increasing `tactile_recess_extra_depth` eats into it directly

---

## 📚 References

1. **Web Generator**: https://braille-card-and-cylinder-stl-gener.vercel.app
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

For general braille embossing questions, see the [web app](https://braille-card-and-cylinder-stl-gener.vercel.app).

---

**Version**: 2.4.0  
**Last Updated**: 2026-07-26
