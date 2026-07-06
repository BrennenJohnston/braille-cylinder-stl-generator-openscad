# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **False-positive `TEXT TOO LONG` warning with indicators On.** The warning
  threshold subtracted 2 cells when indicators were enabled
  (`active_grid_columns - (indicator_on ? 2 : 0)`), implying a "Design B"
  capacity of `grid_columns - 2`. This contradicted the actual geometry, which
  widens the grid by 2 cells when indicators are on (`actual_grid_columns =
  grid_columns + 2`) and leaves the text capacity unchanged ("Design A"). A
  full-capacity line (e.g. 10–11 chars) with indicators On rendered correctly
  yet was wrongly flagged. The threshold is now `> active_grid_columns` in both
  `Braille_Cylinder_STL_Generator.scad` and the MakerWorld twin, and the
  adjacent comment was rewritten to describe the Design-A model. No reference
  fixtures changed (longest fixture line is 5 chars, so the warning never fired
  before or after the fix — zero geometry delta).

### Changed
- **Capacity documentation reconciled to Design A.** Standardized the wording
  across `README.md` (features list + "TEXT TOO LONG" troubleshooting),
  `docs/PARAMETER_MAPPING.md` (the "Indicator Shapes" prose now matches Note 2
  and the Default Values line), the `grid_columns` parameter description in both
  SCAD headers, `tests/parameter_mapping.json`, and the
  `cylinder_rounded_emboss_multiline` note in
  `tests/fixtures/cross_platform/test_cases.json`: text capacity is always
  `grid_columns`; enabling indicators adds 2 marker cells without reducing
  capacity.
- **Testing documentation corrected.** `README.md` now describes the suite as
  OpenSCAD self/regression validation against committed OpenSCAD-generated
  reference STLs (the web reference parity claim was stale; the web API is
  retired). Stale fixture counts were updated from 11 to the authoritative 14
  and the 3 missing cases (`cylinder_rounded_emboss_multiline`,
  `cylinder_rounded_emboss_03mm`, `cylinder_rounded_counter_03mm`) were added to
  the coverage matrices in `README.md`,
  `tests/fixtures/cross_platform/README_FIXTURE_GENERATION.md`, and
  `docs/QUICK_START_TESTING.md`.

### Removed
- **Dead variable `active_counter_base_diameter`.** Defined but never
  referenced; removed from both `Braille_Cylinder_STL_Generator.scad` and the
  MakerWorld twin (`active_counter_height`, which is used, is unaffected).

### Tests
- `tests/test_text_too_long.py` updated to the Design-A contract
  (`capacity = grid_columns`) and now renders an exact-capacity line
  (`grid_columns` chars with indicators On) asserting the warning does **not**
  fire — the regression guard for the bug fixed above.

## [2.3.0] - 2026-06-04

### Added
- **MakerWorld single-file build (alternative).** New
  `makerworld/Braille_Cylinder_STL_Generator_MakerWorld.scad` — a flattened,
  single-file copy of the generator for MakerWorld's Parametric Model Maker
  (which accepts only one `.scad` file and rejects local `include <...>`). It
  inlines `presets.scad` between `// ==== BEGIN/END inlined from presets.scad ====`
  sentinels and defaults `dot_shape` to `"Cone"` (the dropdown still offers
  `Rounded`). The dual-file desktop version remains the canonical source of
  truth.
- `makerworld/README.md` with upload steps, the Cone-default note, and the
  maintainer re-flatten procedure.
- `tests/test_makerworld_sync.py` guarding that the MakerWorld file's geometry
  body (from the `BACKWARD COMPATIBILITY` marker to EOF) is byte-identical to
  the canonical main file, that presets are inlined (no active `include`), and
  that the Cone default + sentinels are present.

### Fixed
- **Indicator triangle mirror (emboss/counter now form a true mirrored pair).**
  The counter plate previously built its indicators by negating angles while
  reusing the emboss triangle orientation and the rectangle's `+dot_spacing/2`
  local offset un-mirrored, so (1) the triangle pointed the wrong way relative
  to the emboss plate and (2) the triangle→rectangle center spacing differed
  between the two plates by ~`dot_spacing` (≈2.5 mm). The per-row indicator
  layout is now factored into a single `place_row_indicators` module; the
  emboss plate renders it directly and the counter plate renders the same
  module under `mirror([0, 1, 0])`, producing an exact mirrored pair with
  identical triangle→rectangle spacing and opposite triangle directions (emboss
  apex right, counter apex left, verified by render). In
  `Braille_Cylinder_STL_Generator.scad`.

### Changed
- **Default `dot_shape` is now `"Cone"`** (was `"Rounded"`) in
  `Braille_Cylinder_STL_Generator.scad`, so the OpenSCAD Customizer loads with
  Cone selected; the dropdown still offers `Rounded`. `paper_thickness_preset`
  remains `"0.4mm"` by default. This matches the MakerWorld single-file build,
  so both files now share the Cone default. Reference fixtures are unaffected
  (the test matrix passes `combined_shape` explicitly). README "Default
  Settings" updated accordingly.
- `tests/test_indicator_source_guards.py` now asserts the new shared-module +
  `mirror([0, 1, 0])` structure (`place_row_indicators`, the emboss/counter call
  sites, and `rotate_180 = true` in the shared module) while keeping the old
  anti-regression guards.
- Regenerated all 14 cross-platform reference fixtures for the indicator
  geometry change and bumped `fixture_version` `2.2.0` → `2.3.0` in
  `tests/fixtures/cross_platform/test_cases.json` (with a note). Indicator
  geometry changed on every `indicators_on` fixture; `verify_fixture_integrity`
  and the full `cross_platform_validation` suite pass against the new fixtures.

## [2.2.1] - 2026-05-30

### Added
- Wired the three new v2.2.0 cross-platform fixtures
  (`cylinder_rounded_emboss_multiline`,
  `cylinder_rounded_emboss_03mm`,
  `cylinder_rounded_counter_03mm`) into
  `tests/cross_platform_validation.py` so CI's `test-full` matrix
  exercises all 14 reference STLs instead of just the original 11.
- `INVALID_TEXT_STACK_GAP = 8` constant in
  `Braille_Cylinder_STL_Generator.scad`, replacing the literal `+ 8`
  used to stack the `TEXT TOO LONG` warning above
  `INVALID CHARACTERS`. The structural invariant in
  `tests/test_text_too_long.py` was updated to assert the named
  form.

### Fixed
- Doc/code drift around the preset surface area: corrected
  "24 parameters" → "23 parameters" in `README.md`,
  `docs/PARAMETER_MAPPING.md` (2 places), and
  `tests/parameter_mapping.json` after `braille_x_adjust` was removed
  in v2.2.0. Renamed the corresponding pytest method
  `test_preset_tables_share_24_parameters` →
  `test_preset_tables_share_23_parameters`. (The CHANGELOG's "24
  slider ranges" line under v2.2.0 is unchanged — that count
  includes `cone_segments`, which is a numeric slider but is not
  preset-controlled.)
- `README.md` "Positioning adjustments (X/Y offsets)" bullet was
  obsolete after `braille_x_adjust` removal; now reads "Vertical
  positioning adjustment (Y offset)".
- `tests/fixtures/cross_platform/test_cases.json` `fixture_version`
  bumped from `1.1.0` to `2.2.0` to match
  `FIXTURES_VERSION.json` / `.txt`.
- `Braille_Cylinder_STL_Generator.scad` `$fn` policy header
  corrected from "the four sources are intentionally segregated" to
  "the five sources" (the body already enumerated five cases).

## [2.2.0] - 2026-05-30

### Removed
- Plug Puller experiments (entire `Plug Puller Test/` tree, root
  `Plug_Puller_Parametric.scad`, root `Plug_Puller_v4_Parametric.scad`,
  `dxf_extracts/`, `obj_vertex_data.txt`,
  `artifacts/plug_puller_validation/`, and stray validation renders) —
  moved to
  [plug-puller-openscad](https://github.com/BrennenJohnston/plug-puller-openscad).
- DXF/SVG conversion scripts (`scripts/dxf_to_openscad_polygon.py`,
  `scripts/extract_svg_overlay_outline.py`) — moved to
  [cad-to-openscad-pipeline](https://github.com/BrennenJohnston/cad-to-openscad-pipeline).
- `braille_x_adjust` Customizer slider and the corresponding
  `active_braille_x_adjust` aggregator. On a cylinder the X axis is
  the angular wrap around the seam, so a linear "X adjust" had no
  useful meaning. Use `seam_offset_degrees` for angular pattern
  offset.
- Unused aggregators `active_emboss_base_diameter`,
  `active_emboss_top_diameter`, and `active_counter_top_diameter`
  (dead since the cylinder rewrite).
- Root `PARAMETER_MAPPING.md` duplicate. `docs/PARAMETER_MAPPING.md`
  is the single canonical copy; references in `CONTRIBUTING.md`,
  `docs/OPENSCAD_COORDINATE_SYSTEM_SPECIFICATIONS.md`, and
  `tests/parameter_mapping.json` updated.
- Dead `check_tool_version()` stub in `tests/conftest.py`. Real
  version enforcement lives in `OpenSCADRunner._enforce_version()`.
- `@pytest.mark.card` registration and the auto-tagging branch in
  `tests/conftest.py`. Card support was retired in v2.0; the marker
  served no purpose.

### Changed
- Renamed main file
  `Braille_Card_And_Cylinder_STL_Generator.scad` →
  `Braille_Cylinder_STL_Generator.scad`. Updated 26 reference sites
  (tests, scripts, README, archive docs, fixture metadata).
- Refactored preset routing: extracted constants and lookup helper
  into a new top-level `presets.scad` (`PRESET_04`, `PRESET_03`
  tables and `preset_value(preset, key, fallback)`). The main SCAD
  `include`s it inside `[Hidden]`. Critical OpenSCAD `search()`
  quirks documented inline.
- Hoisted shared cylinder grid math (`radius`, `grid_angle`,
  `start_angle`, `cell_spacing_angle`, `dot_spacing_angle`,
  `dot_col_angle_offsets`, `dot_row_offsets`, `dot_positions`) from
  `cylinder_emboss_plate` and `cylinder_counter_plate` to top-level
  scope. Names preserved so module bodies needed no internal edits.
- Pinned the backward-compat parameter block (`combined_shape`,
  `indicator_shapes`, `hemisphere_quality`, `shape_type`) under an
  explicit `/* [Hidden] */` marker so the Customizer no longer
  surfaces them as orphan uncategorized fields.
- README now links to the two spin-off repositories under a new
  "Spin-off Projects" section.
- Archived `CODEBASE_AUDIT_SUMMARY.md` →
  `docs/archive/CODEBASE_AUDIT_SUMMARY_2026-01-10.md`. It was a
  one-shot snapshot, not a living doc.

### Added
- Named geometry constants: `INDICATOR_OVERCUT` (0.05),
  `CYLINDER_SHELL_FN` (64), `INVALID_TEXT_Z_OFFSET` (5),
  `INVALID_TEXT_SIZE` (5), `INVALID_TEXT_DEPTH` (2). Replaces the
  prior magic numbers scattered through the geometry section.
- "TEXT TOO LONG" warning geometry: the cylinder emboss plate now
  renders a red `text("TEXT TOO LONG")` extrusion above the
  cylinder when any of `Line_1`–`Line_4` exceeds
  `active_grid_columns - (indicator_on ? 2 : 0)`. Stacks above the
  existing INVALID CHARACTERS warning when both fire.
- Documentation block at the top of the geometry section explaining
  the `$fn` tessellation policy. Five distinct `$fn` sources
  (`CYLINDER_SHELL_FN`, `cone_segments` slider, `quality_fn`-derived,
  `active_polygon_cutout_points` semantic, global `$fn = 32`
  default) are each documented with their intent.
- This `CHANGELOG.md` file.
- Spin-off sibling repository [plug-puller-openscad](https://github.com/BrennenJohnston/plug-puller-openscad)
  (private) — holds the Plug Puller v1/v2/v3/v4 design work
  previously living in `Plug Puller Test/`.
- Spin-off sibling repository
  [cad-to-openscad-pipeline](https://github.com/BrennenJohnston/cad-to-openscad-pipeline)
  (private) — packages the CAD-to-OpenSCAD methodology and the
  general-purpose `dxf-to-openscad-polygon` console script.

### Tests
- `tests/test_presets.py` (9 tests): asserts the `PRESET_04` and
  `PRESET_03` tables expose all 24 routed parameters, that
  `preset_value(...)` falls back to the slider for "Custom", and
  that every `active_*` aggregator in the main SCAD reads from
  `preset_value()` rather than a hand-rolled ternary chain.
- `tests/test_backward_compat.py` (6 tests): pins
  `combined_shape`, `indicator_shapes`, `hemisphere_quality`, and
  `shape_type` inside the explicit `/* [Hidden] */` block with an
  empty-string default so the OpenSCAD Customizer no longer
  surfaces them as orphan fields.
- `tests/test_text_too_long.py` (2 tests): verifies the source
  invariants of the new warning module and renders an oversized
  text case through the nightly OpenSCAD runner to confirm the
  warning geometry expands the cylinder's bounding box.
- `tests/validate_parameter_schema.py` now parses
  `// [min:step:max]` slider triples from the main SCAD and
  cross-checks them against the `range` field in
  `tests/parameter_mapping.json`. The validator's summary line
  reports "All 24 OpenSCAD slider ranges match
  parameter_mapping.json" and still exits 0.
- Three new cross-platform reference fixtures, all LFS-tracked,
  watertight, and byte-stable under OpenSCAD 2026.01.03 Manifold:
  - `cylinder_rounded_emboss_multiline` (3-line short text, 0.4mm
    preset, sha `8c70a0740e1c…`)
  - `cylinder_rounded_emboss_03mm` (0.3mm paper-thickness preset,
    rounded emboss, sha `da6336e72aa0…`)
  - `cylinder_rounded_counter_03mm` (0.3mm preset on the rounded
    counter path, sha `c07d653b6db3…`)
  Total cross-platform fixtures: 11 → 14. The original 11 sha256
  hashes are unchanged.
- CI wiring: `tests/test_cloudcompare_logic.py`,
  `tests/test_presets.py`, `tests/test_backward_compat.py`, and
  `tests/test_text_too_long.py` are now invoked by the `test-quick`
  job in `.github/workflows/stl-validation.yml`. Pinned OpenSCAD
  remains 2026.01.03.
- `tests/fixtures/cross_platform/FIXTURES_VERSION.{json,txt}` and
  `tests/fixtures/cross_platform/test_cases.json` metadata bumped
  to reflect the v2.2.0 release (no reference STL regeneration).

### Fixed
- `docs/PARAMETER_MAPPING.md` "Indicator Shapes" section described
  the card layout (rectangle at col 0, triangle at col N-1).
  Rewrote for cylinder-only reality (col 0 triangle, col 1
  rectangle).
- `docs/PARAMETER_MAPPING.md` OpenSCAD workflow step said "Choose
  `shape_type`". Replaced with `dot_shape` (the actual Customizer
  control); `shape_type` lives in `[Hidden]` as a backward-compat
  alias.
- `docs/PARAMETER_MAPPING.md` "Unified Shape Selection" documented
  `combined_shape` as primary control. Documented `dot_shape` as
  primary; `combined_shape` framed as the test-system alias.
- `CONTRIBUTING.md` line 53: "Cylinder shapes (card temporarily
  hidden)" → "Cylinder shape (card support permanently removed)".
- `docs/archive/README.md` index now lists the newly archived
  audit document.
- CI: `STL Validation (ubuntu-latest)` job had been failing since
  the v2.1.0 release (2026-01-11) with `libEGL.so.1: cannot open
  shared object file` because ubuntu-latest (now 24.04) no longer
  ships the OpenGL / EGL / xcb / font runtime that the OpenSCAD
  2026.01.03 nightly AppImage dynamically links against. The
  Ubuntu install step now `apt-get install`s the Qt6 headless-
  render runtime (libegl1, libgl1, libgles2, libopengl0, libxcb-*,
  libxkbcommon-*, libfontconfig1, libfreetype6, libharfbuzz0b, …)
  before extracting the AppImage. Both `comparison_profile=baseline`
  and `=strict` workflow_dispatch runs go fully green on
  `feature/v2.2-cleanup` (runs `26690377853` and `26690446255`).

## [2.1.0] - 2026-01-11

Last tagged release prior to the v2.2.0 cleanup. See git history for details.
