// =============================================================================
// presets.scad — Paper-thickness preset value tables and lookup helper
// =============================================================================
//
// This file is `include`d by Braille_Cylinder_STL_Generator.scad. It defines:
//
//   - PRESET_04 / PRESET_03  : per-preset [key, value] lookup tables.
//   - preset_lookup(...)     : low-level table lookup; returns undef on miss.
//   - preset_value(preset, key, fallback)
//                            : public helper used by the main SCAD. Returns
//                              the table value if `preset` matches "0.4mm" or
//                              "0.3mm"; otherwise returns `fallback`
//                              (typically the user's slider value).
//
// Why a separate file
// -------------------
// The main SCAD previously had ~100 lines of nearly identical ternary chains,
// one per parameter, all routing between presets and the user's slider value.
// Storing the data as plain lookup tables here makes preset edits a one-line
// change and reduces the routing block in the main file to one line per
// parameter.
//
// Customizer behaviour
// --------------------
// OpenSCAD's Customizer reads parameters from the *main* file only, so the
// PRESET_* lists declared below are never rendered as orphan sliders. A
// `/* [Hidden] */` marker is included at the top as a defence-in-depth
// guarantee in case future OpenSCAD versions change that behaviour.
//
// Source of preset values
// -----------------------
// Mirrors the web app's THICKNESS_PRESETS in public/index.html. When updating
// presets, change both this file and the web app in lockstep so the OpenSCAD
// renders match the web preview exactly.
//
// License: PolyForm Noncommercial 1.0.0

/* [Hidden] */

// --------- 0.4mm Preset (Thicker Paper, Larger Dots) ---------
// NOTE: grid_columns and grid_rows are deliberately ABSENT from the preset
// tables. preset_value() falls back to the user's slider when a key is
// missing, so the sliders always govern text capacity — matching the web
// app, where thickness presets never override the columns/rows dials.
PRESET_04 = [
    // Spacing
    ["cell_spacing",                    6.5],
    ["line_spacing",                    10.0],
    ["dot_spacing",                     2.5],
    ["braille_y_adjust",                0.0],

    // Emboss Rounded
    ["rounded_dot_base_diameter",       1.5],
    ["rounded_dot_base_height",         0.5],
    ["rounded_dot_dome_diameter",       1.0],
    ["rounded_dot_dome_height",         0.5],

    // Emboss Cone
    ["emboss_dot_base_diameter",        1.5],
    ["emboss_dot_height",               0.8],
    ["emboss_dot_flat_hat",             0.4],

    // Counter Bowl
    ["bowl_counter_dot_base_diameter",  1.8],
    ["counter_dot_depth",               0.8],

    // Counter Cone
    ["cone_counter_dot_base_diameter",  1.9],
    ["cone_counter_dot_height",         0.7],
    ["cone_counter_dot_flat_hat",       1.0],

    // Cylinder
    ["cylinder_diameter_mm",            30.8],
    ["cylinder_height_mm",              52],
    ["polygon_cutout_radius_mm",        13],
    ["polygon_cutout_points",           12],
    ["seam_offset_degrees",             0.0],
];

// --------- 0.3mm Preset (Thinner Paper, Smaller Dots) ---------
PRESET_03 = [
    // Spacing (same as 0.4mm; grid_columns/grid_rows intentionally absent —
    // the sliders always govern text capacity)
    ["cell_spacing",                    6.5],
    ["line_spacing",                    10.0],
    ["dot_spacing",                     2.5],
    ["braille_y_adjust",                0.0],

    // Emboss Rounded (smaller)
    ["rounded_dot_base_diameter",       1.2],
    ["rounded_dot_base_height",         0.4],
    ["rounded_dot_dome_diameter",       0.8],
    ["rounded_dot_dome_height",         0.4],

    // Emboss Cone (smaller)
    ["emboss_dot_base_diameter",        1.2],
    ["emboss_dot_height",               0.6],
    ["emboss_dot_flat_hat",             0.2],

    // Counter Bowl (smaller)
    ["bowl_counter_dot_base_diameter",  1.5],
    ["counter_dot_depth",               0.5],

    // Counter Cone (smaller)
    ["cone_counter_dot_base_diameter",  1.5],
    ["cone_counter_dot_height",         0.5],
    ["cone_counter_dot_flat_hat",       0.8],

    // Cylinder (same as 0.4mm)
    ["cylinder_diameter_mm",            30.8],
    ["cylinder_height_mm",              52],
    ["polygon_cutout_radius_mm",        13],
    ["polygon_cutout_points",           12],
    ["seam_offset_degrees",             0.0],
];

// Low-level table lookup. Returns the value for `key` in `preset_list`, or
// `undef` if not found. Uses OpenSCAD's built-in `search()` against the
// first column of the `[key, value]` pair list.
//
// IMPORTANT OpenSCAD quirks (verified on OpenSCAD 2026.01.03):
//   - `search(key, list)`     — treats `key` as a SEQUENCE OF CHARACTERS
//                                and matches each char individually. Useless
//                                for multi-character keys like our preset
//                                names; produces wrong matches silently.
//   - `search([key], list)`   — treats `[key]` as a one-element vector of
//                                needles and does whole-string matching.
//                                Returns `[idx]` on a hit but `[[]]` on a
//                                miss — the return shape is INCONSISTENT
//                                between hit and miss.
//
// We use the wrapped form for whole-string matching and discriminate
// hit-vs-miss with `is_num(m[0])`: a hit means `m[0]` is the integer row
// index; a miss means `m[0]` is the empty list `[]`.
function preset_lookup(preset_list, key) =
    let (m = search([key], preset_list))
    is_num(m[0]) ? preset_list[m[0]][1] : undef;

// Public helper. Selects between the 0.4mm/0.3mm preset tables and the user's
// fallback value (typically a slider variable) based on `preset`. Returns
// `fallback` for "Custom", unrecognized preset names, or keys not present in
// the matched table.
function preset_value(preset, key, fallback) =
    let (val =
        preset == "0.4mm" ? preset_lookup(PRESET_04, key) :
        preset == "0.3mm" ? preset_lookup(PRESET_03, key) :
        undef)
    val == undef ? fallback : val;
