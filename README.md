# Braille Cylinder STL Generator (OpenSCAD)

Parametric OpenSCAD program for generating braille embossing plates and counter plates for cylindrical objects.

[![STL Validation](https://github.com/BrennenJohnston/braille-stl-generator-openscad/actions/workflows/stl-validation.yml/badge.svg)](https://github.com/BrennenJohnston/braille-stl-generator-openscad/actions/workflows/stl-validation.yml)

## 🔗 Related Project

This is the **offline OpenSCAD companion** to the web-based Braille STL Generator:

| Version | Link | Use Case |
|---------|------|----------|
| **Web App** | [braille-card-and-cylinder-stl-gener.vercel.app](https://braille-card-and-cylinder-stl-gener.vercel.app) | Browser-based with automatic translation |
| **OpenSCAD** (this repo) | [github.com/BrennenJohnston/braille-stl-generator-openscad](https://github.com/BrennenJohnston/braille-stl-generator-openscad) | Offline use, full parametric control |
| **Web App Source** | [github.com/BrennenJohnston/braille-card-and-cylinder-stl-generator](https://github.com/BrennenJohnston/braille-card-and-cylinder-stl-generator) | Web app source code |

### Spin-off Projects

The following repositories were extracted from earlier iterations of this project and are now developed separately:

| Repo | Description |
|------|-------------|
| [plug-puller-openscad](https://github.com/BrennenJohnston/plug-puller-openscad) | Parametric SCAD + CAD data for the Plug Puller experiments (v1.0–v4.0). |
| [cad-to-openscad-pipeline](https://github.com/BrennenJohnston/cad-to-openscad-pipeline) | Reusable methodology and tooling for converting CAD models into clean parametric OpenSCAD, including the `dxf_to_openscad_polygon` tool. |

## ⚠️ Key Difference

**This OpenSCAD version requires pre-translated Unicode braille text.** It does NOT include automatic translation.

---

## 📦 MakerWorld Single-File Build (Alternative)

Want to run this in MakerWorld's **Parametric Model Maker** instead of the
desktop app? A flattened, single-file build lives in
[`makerworld/`](makerworld/):

- [`makerworld/Braille_Cylinder_STL_Generator_MakerWorld.scad`](makerworld/Braille_Cylinder_STL_Generator_MakerWorld.scad) — one `.scad` file (presets inlined, no `include`), ready to upload. Defaults to the `Cone` dot shape.
- See [`makerworld/README.md`](makerworld/README.md) for upload steps and the maintainer re-flatten procedure.

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

### Indicator Shapes
- Optional start/end markers for each row (triangle and rectangle)
- Helps with plate alignment during embossing
- Adds 2 cells per row when enabled (text capacity stays at `grid_columns`)

### Paper Thickness Presets
- **0.4mm Preset** (default): Optimized for thicker paper, larger dots
- **0.3mm Preset**: Optimized for thinner paper, smaller dots
- **Custom**: Use manually-entered parameter values

The preset system controls 23 parameters at once (spacing, dot dimensions, cylinder settings) matching the web app's "Card Thickness" dropdown.

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
Preset** (applied on load). The default **dot shape is `Cone`** (the dropdown
still offers `Rounded`):

### Cylinder Settings
- Diameter: 30.8mm
- Height: 52mm
- Polygonal Cutout: 13mm radius, 12 points/sides
- Seam Offset: 0°

### Braille Grid
- Cells per row: 11 (available for text; 2 additional cells reserved when indicators are on)
- Number of rows: 4
- Cell spacing: 6.5mm
- Line spacing: 10.0mm
- Dot spacing: 2.5mm

### Dot Dimensions (Cone - 0.4mm Preset, default shape)
- Base diameter: 1.5mm
- Height: 0.8mm
- Flat hat diameter: 0.4mm

### Counter Plate (Cone recess - 0.4mm Preset, default shape)
- Base diameter: 1.9mm
- Height: 0.7mm
- Flat hat diameter: 1.0mm

### Dot Dimensions (Rounded - 0.4mm Preset, alternative shape)
- Base diameter: 1.5mm
- Base height: 0.5mm
- Dome diameter: 1.0mm
- Dome height: 0.5mm

### Counter Plate (Bowl - 0.4mm Preset, alternative shape)
- Base diameter: 1.8mm
- Depth: 0.8mm

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
- **Customizer validation tests**: Prevent dropdown duplicate issues

This adds up to **14** cross-platform fixtures (`total_test_cases: 14` in `tests/fixtures/cross_platform/test_cases.json`).

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
- Capacity = `grid_columns`, whether indicators are on or off. When
  indicators are on, the grid is widened by 2 cells for the alignment
  markers, so the text capacity is unchanged
- A red `TEXT TOO LONG` extrusion is rendered above the cylinder
  whenever the limit is exceeded
- Solution: shorten the line or increase `grid_columns`

### Dots Don't Align
- Check `braille_y_adjust` for vertical offset, or `seam_offset_degrees` for angular offset around the cylinder
- Ensure spacing settings match between emboss and counter plates

### Plates Don't Fit Together
- Verify both plates use same `dot_shape` setting
- Check that counter plate dimensions match emboss dimensions
- Ensure `indicators` setting is same for both plates

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
1. [Open an issue](https://github.com/BrennenJohnston/braille-stl-generator-openscad/issues) on this repository
2. Check parameter values in Customizer
3. Verify Unicode braille character validity
4. Ensure OpenSCAD version 2024.x or newer (2026.01.03+ recommended)

For general braille embossing questions, see the [web app](https://braille-card-and-cylinder-stl-gener.vercel.app).

---

**Version**: 2.3.0  
**Last Updated**: 2026-06-04
