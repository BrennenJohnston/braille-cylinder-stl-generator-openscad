# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-05

First public release, split out of
[braille-stl-generator-openscad](https://github.com/BrennenJohnston/braille-stl-generator-openscad)
(where it incubated as `experimental/braille-business-card/`).

### Added

- **20 text rows.** `Line_1`…`Line_20`, with `_all_lines` as the single source
  of truth for every loop, warning, and layout module, and a documented recipe
  for extending past 20. `grid_rows` slider now reaches 20; manual face size up
  to 300 × 250 mm.
- **Print-bed size warning.** The console warns when the effective card face
  exceeds 250 mm in either direction.
- **Curated Customizer presets** (`Default Card`,
  `Compact Card (manual 75x25)`, `Large 20-Line Card`) with generic sample
  braille. Personal preset files matching `*.local.json` are gitignored.
- **Test suite + CI.** Customizer dropdown hygiene tests, source-invariant
  guards (including a mission guard that keeps embossing-era concepts out),
  and OpenSCAD render smoke tests asserting watertight single-body STLs with
  expected bounding boxes. GitHub Actions workflow runs lint + quick tests +
  render smoke on Ubuntu.
- Project docs: README (quick start, print guidance, troubleshooting,
  MakerWorld upload steps), research notes under `docs/`, PolyForm
  Noncommercial LICENSE.

### Changed

- **First-run defaults are the print-tested "Try 4" configuration** (with
  warnings kept On): fins every 25 mm (1.0 mm offset, 1.2 mm thick), six
  0.5 × 0.5 mm bridges per fin at 0.3 mm contact, 2 mm brim, 1.5 mm card,
  7.0 mm cell spacing, 11 × 5 grid, Rounded dot 1.6/0.35 + 1.4/0.35
  (0.7 mm total height — inside the ADA envelope), render quality High.

### Removed (vs. the experimental prototype)

- **All embossing-era concepts.** This is now a pure directly-readable card:
  `plate_type` / Counter Plate path, counter recess modules and parameters,
  row start/end indicators, the `_preset_*` routing shims, and the parent
  repo's test-system compatibility parameters are gone. `braille_card()` is a
  plain union of card body, dots, and preview-only warnings.

### Fixed

- **Floating-shell STL exports.** Dots seated exactly on the face plane (and
  the rounded dot's dome seated exactly on its base) could export as separate
  disconnected shells. Dots now embed 0.02 mm into the face and the dome
  overlaps its base, so every export fuses into one watertight solid.
- **Bridges above short fins.** With a small `fin_height_frac` the bridge
  ladder could start above the fin top, leaving floating prongs; the bridge
  span is now clamped to the fin.
- **Brim/card tangency.** The fin brim stopped exactly at the card's
  bottom-back corner, exporting a non-manifold self-touching boundary; the
  brim now stops just short of the card.
