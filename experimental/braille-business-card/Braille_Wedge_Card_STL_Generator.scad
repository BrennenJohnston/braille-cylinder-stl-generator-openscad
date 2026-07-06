// Braille Leaning Card STL Generator (OpenSCAD) — EXPERIMENTAL "Path 2"
// Generates a FLAT braille card that leans back at face_angle_deg from the bed
// (default 75°), held stable during printing by a parametric array of
// triangular BREAK-AWAY SUPPORT FINS: triangular fins on a fixed interval,
// offset from the card back, joined to it by tiny break-away bridges, with a
// built-in brim for bed adhesion. The whole thing exports as ONE fused STL and
// the fins snap/flex off after printing.
//
// =============================================================================
// STATUS
// =============================================================================
//  • Self-contained experimental prototype. Lives entirely under
//    experimental/braille-business-card/ so the folder can be
//    `git subtree split` into its own repo later without touching the parent
//    cylinder generator's tests (the main repo's
//    tests/test_openscad_customizer.py::test_card_support_removed guards
//    against re-introducing card geometry into the main .scad).
//  • Reuses the proven dot, recess, and indicator modules from the parent
//    Braille_Cylinder_STL_Generator.scad, de-globalized (no preset routing,
//    no include/use) so this file stands alone. If/when this prototype
//    graduates, the duplicated modules should be extracted into a shared
//    braille_common.scad.
//
// =============================================================================
// WHAT THIS MAKES
// =============================================================================
//  • Embossing Plate — a flat leaning card with raised braille dots on the
//    angled reading face, plus a break-away support-fin structure behind it.
//  • Counter Plate — the same flat leaning card body, but the braille pattern
//    is recessed into the face (and indicators are mirrored left/right) so the
//    two plates form a matching emboss/counter pair, mirroring the cylinder
//    generator's emboss/counter relationship.
//  • Support Fins (toggle) — a row of triangular fins, on fin_interval_mm
//    spacing (always including both outer edges, so the minimum is 2 edge fins
//    and the maximum is hundreds), standing fin_offset_mm behind the card's
//    overhanging back face, each joined to the card by bridge_count tiny
//    break-away bridges and grounded by a flat brim. Fully fused with the card
//    so it slices as a single print-ready object.
//
// =============================================================================
// HOW TO USE
// =============================================================================
//  1. Translate your text at https://www.branah.com/braille-translator
//     (Grade 1 or Grade 2, Unicode Braille output — NOT ASCII Braille).
//  2. Paste pre-translated braille into Line_1..Line_4 in the Customizer.
//  3. Pick plate_type (Embossing Plate or Counter Plate) and dot_shape.
//  4. Leave auto_size_card = On (the default) and the card face auto-sizes to
//     fit your text plus a margin — the effective size is reported in the
//     console (the Customizer sliders can't show computed values). Switch it
//     Off to drive the manual width/height sliders instead.
//  5. Warnings (invalid characters, text too long, too many lines) appear as
//     red 3D text in the F5 preview only — they are NEVER exported to the STL,
//     and can be turned off under the [Warnings] tab.
//  6. Tune support fins under [Support Fins] (anywhere from 2 edge fins up to
//     hundreds), or set support_fins = Off to export the bare card.
//  7. Render (F6) → File → Export → STL.
//
// =============================================================================
// PRINT / SLICER GUIDANCE
// =============================================================================
//  • Print AS MODELED — the card leans back and the fins stand behind it on the
//    bed. No slicer supports are needed; a slicer brim on top is optional.
//  • The bridges are single-/few-layer horizontal prongs. Tune bridge_contact_mm
//    (0.3–0.4 mm) so they connect during the print but snap off cleanly after.
//  • After printing, flex/snip the fins off the back and deburr the small nubs
//    left by the bridges.
//  • Do NOT cut lightening holes in the fins — per masukomi, the extra motion /
//    vibration hurts a thin leaning part more than the saved filament helps.
//
// =============================================================================
// REFERENCES
// =============================================================================
//  [A] Parent cylinder generator (source of the dot / recess / indicator
//      modules adapted below):
//      ../../Braille_Cylinder_STL_Generator.scad on this repo's main branch.
//  [B] Path recommendation + print-stability research:
//      ./research-print-stability-and-path-recommendation.md
//  [C] Dot geometry and slicer-quality research:
//      ./research-dot-geometry-and-slicer-quality.md
//  [D] Reference model (leaning card with CAD support fins):
//      ../Leaning Braille Research Folder/Leaning card example (support fins).obj
//  [E] Slant3D, "Stop Using Slicer Supports" — triangular fin spaced off the
//      part, thin horizontal prongs, wide base, chamfer to snap off:
//      https://youtu.be/_R2E8VwyNz0
//  [F] masukomi, "Manual Support Fins for 3D Printing" — ~1 mm offset, column of
//      small sprues, add side fins so edges don't float, avoid holes in fins,
//      prefer 0.3–0.4 mm contact:
//      https://weblog.masukomi.org/2024/03/11/manual-support-fins-for-3d-printing/
//  [G] Break-away support guidance (0.2–0.5 mm contact, wide base, chamfer):
//      https://www.wevolver.com/article/3d-print-supports-a-guide-for-engineers
//  [H] BANA size and spacing: https://brailleauthority.org/size-and-spacing-braille-characters
//  [I] 2010 ADA Standards: https://archive.ada.gov/
// =============================================================================

/* [Text Input - Pre-Translated Braille] */
// Paste Unicode braille characters from https://www.branah.com/braille-translator
// First line of braille text
Line_1 = "⠓⠑⠇⠇⠕";
// Second line of braille text
Line_2 = "⠺⠕⠗⠇⠙";
// Third line of braille text
Line_3 = "";
// Fourth line of braille text
Line_4 = "";

/* [Plate Selection] */
// Choose which plate to generate
plate_type = "Embossing Plate"; // [Embossing Plate, Counter Plate]

/* [Card Size] */
// Auto-size the card face to fit the braille text plus margins. Turn Off to use the manual width/height below.
auto_size_card = "On"; // [On, Off]
// Margin between the braille block and the card edges when auto-sizing (mm)
auto_size_margin_mm = 6;     // [2:0.5:20]
// Manual face width (mm) - only used when auto_size_card = Off
card_face_width_mm = 85;     // [40:1:200]
// Manual face height (mm) - only used when auto_size_card = Off
card_face_height_mm = 55;    // [25:1:150]

/* [Warnings] */
// Show red 3D warning text above the card when input has problems. Warnings are preview-only and are NEVER exported to the STL.
show_warnings = "On"; // [On, Off]

/* [Support Fins] */
// Master toggle for the entire break-away support-fin structure. When Off the
// bare leaning card is exported (you must then add slicer supports yourself).
support_fins = "On";         // [On, Off]
// Spacing between fins across the card width (mm). End fins at both outer edges
// are always added on top of this interval (per masukomi's "side fins" lesson).
// At the max interval only the two edge fins remain (2 minimum); at the min a
// fin lands every millimetre (hundreds across a wide card).
fin_interval_mm = 10;        // [1:0.5:200]
// Horizontal gap between the card's back face and the fin (mm) — the break-away
// gap that the bridges span. ~1 mm per masukomi.
fin_offset_mm = 1.5;         // [0.2:0.05:10]
// Fin prism thickness along X (mm). Keep a multiple of nozzle width (e.g. 0.4/0.8).
fin_thickness_mm = 0.8;      // [0.2:0.05:10]
// Fin height as a fraction of the card height (1.0 = full height; auto-matches
// the card height/angle).
fin_height_frac = 1.0;       // [0.05:0.01:1]
// Number of break-away bridges up each fin (the "contact points" dial).
bridge_count = 4;            // [1:1:60]
// Bridge size along X (mm).
bridge_width_mm = 1.5;       // [0.2:0.05:8]
// Bridge size along Z (mm).
bridge_height_mm = 1.5;      // [0.2:0.05:8]
// How far each bridge actually merges into the card face (mm) — the true
// break-off contact. Research says 0.3-0.4 mm: connects during print, snaps off clean.
bridge_contact_mm = 0.4;     // [0.1:0.05:3]
// Built-in brim flange width around each fin base (mm; 0 = no brim).
brim_width_mm = 3;           // [0:0.25:25]
// Brim layer thickness (mm, ~1-2 layers).
brim_thickness_mm = 0.3;     // [0.1:0.05:3]

/* [Expert Mode - Shape Selection] */
// Braille Dot Shape (Emboss and Counter) - affects both plate types
dot_shape = "Rounded"; // [Rounded, Cone]
// Indicator Shapes (Emboss and Counter) - Row start/end markers (always recessed)
indicators = "On"; // [On, Off]

/* [Expert Mode - Card Shape] */
// Face angle from horizontal bed (deg). 75 = 15 deg lean back from vertical =
// CHI sweet spot. The base footprint is derived from this angle + height.
face_angle_deg = 75;         // [60:1:90]
// Flat card thickness (mm). Must be greater than the counter-plate recess depth
// so recesses don't break through (default recess depth is 0.7-0.8 mm, so keep
// >= ~1.5 mm).
card_thickness_mm = 2.0;     // [1:0.1:5]

/* [Expert Mode - Braille Spacing] */
// Text capacity in braille cells per row (ignored when auto_size_card = On). When indicators On, 2 extra cells are added for markers; text capacity is unchanged.
grid_columns = 11;           // [1:1:30]
// Number of lines of braille (ignored when auto_size_card = On)
grid_rows = 3;               // [1:1:10]
// Horizontal spacing between cells (mm)
cell_spacing = 6.5;          // [2:0.01:15]
// Vertical spacing between lines (mm)
line_spacing = 10.0;         // [5:0.01:25]
// Spacing between dots within a cell (mm)
dot_spacing = 2.5;           // [1:0.01:5]

// --- Braille Positioning ---
// Both axes are meaningful on a flat face (unlike the cylinder, which only
// exposes Y because X = angular wrap around the seam).
// Horizontal adjustment of braille pattern (mm)
braille_x_adjust = 0.0;      // [-20:0.01:20]
// Vertical (down-the-slope) adjustment of braille pattern (mm)
braille_y_adjust = 0.0;      // [-20:0.01:20]

/* [Expert Mode - Braille Dot Adjustments] */
// --- Embossing Braille Dot Dimensions (Rounded Shape) ---
// Defaults chosen to stay ADA-legal: base_height + dome_height <= 0.9 mm.
// Rounded dot base diameter / cone base (mm)
rounded_dot_base_diameter = 1.5; // [0.5:0.01:3]
// Rounded dot base height / cone height (mm)
rounded_dot_base_height   = 0.4; // [0:0.01:2]
// Rounded dome diameter, linked to cone flat top (mm)
rounded_dot_dome_diameter = 1.0; // [0.5:0.01:3]
// Rounded dot dome height (mm)
rounded_dot_dome_height   = 0.5; // [0.1:0.01:2]

// --- Embossing Braille Dot Dimensions (Cone Shape) ---
// Cone dot base diameter (mm)
emboss_dot_base_diameter = 1.5; // [0.5:0.01:3]
// Cone dot height (mm)
emboss_dot_height        = 0.8; // [0.3:0.01:2]
// Cone dot flat hat diameter (mm)
emboss_dot_flat_hat      = 0.4; // [0.1:0.01:2]

// --- Counter Braille Recessed Dot Dimensions (Rounded Shape / Bowl) ---
// Bowl recess base diameter (mm)
bowl_counter_dot_base_diameter = 1.8; // [0.5:0.01:5]
// Bowl recess depth (mm)
counter_dot_depth              = 0.8; // [0.1:0.01:2]

// --- Counter Braille Recessed Dot Dimensions (Cone Shape) ---
// Cone recess base diameter (mm)
cone_counter_dot_base_diameter = 1.9; // [0.5:0.01:3]
// Cone recess height (mm)
cone_counter_dot_height        = 0.7; // [0.3:0.01:2]
// Cone recess flat hat diameter (mm)
cone_counter_dot_flat_hat      = 1.0; // [0.1:0.01:2]

/* [Rendering Quality] */
// Sphere quality for rounded shapes
render_quality = "Medium"; // [Low, Medium, High]
// Number of segments for cone shapes (8-32 recommended)
cone_segments = 16; // [8:1:64]

/* [Hidden] */
$fn = 32;
PI = 3.14159265359;

// Backward-compatibility shim for the parent cylinder generator's test
// system (it passes parameters via -D flags using these names). Kept hidden
// and only consumed by the normalization expressions below.
combined_shape    = ""; // "rounded" or "cone"
indicator_shapes  = ""; // "on" or "off"
hemisphere_quality = ""; // "low", "medium", "high"

// =============================================================================
// CALCULATED VALUES (Do not modify)
// =============================================================================

// Normalize dropdown selections to internal values (UI + test-system parity)
is_emboss_plate = (plate_type == "positive") ? true :
                  (plate_type == "negative") ? false :
                  (plate_type == "Embossing Plate");

use_rounded_dots = (combined_shape == "rounded") ? true :
                   (combined_shape == "cone") ? false :
                   (dot_shape == "Rounded");

indicator_on = (indicator_shapes == "on") ? true :
               (indicator_shapes == "off") ? false :
               (indicators == "On");

fins_on = (support_fins == "On") || (support_fins == true);

warnings_on = (show_warnings == "On") || (show_warnings == true);

quality_fn = (hemisphere_quality == "low"    || render_quality == "Low")    ? 24 :
             (hemisphere_quality == "medium" || render_quality == "Medium") ? 32 :
             (hemisphere_quality == "high"   || render_quality == "High")   ? 64 : 32;

// --- Content metrics (actual typed text, not grid capacity) ---
_all_lines = [Line_1, Line_2, Line_3, Line_4];
// Longest line in braille cells (0 when all lines are empty)
content_max_len = max([for (l = _all_lines) len(l)]);
// Rows spanned by content = index of last non-empty line + 1
// (preserves intentional blank lines between non-empty lines)
_nonempty_idx = [for (i = [0:3]) if (len(_all_lines[i]) > 0) i];
content_rows = len(_nonempty_idx) == 0 ? 0 : _nonempty_idx[len(_nonempty_idx) - 1] + 1;

auto_size_on = (auto_size_card == "On");
// In auto mode, grid capacity == content (so TEXT TOO LONG / TOO MANY LINES cannot occur)
effective_grid_columns = auto_size_on ? max(content_max_len, 1) : grid_columns;
effective_grid_rows    = auto_size_on ? max(content_rows, 1)    : grid_rows;

// -----------------------------------------------------------------------------
// _preset_* shim
// -----------------------------------------------------------------------------
// The dot, recess, and indicator modules copied from the cylinder generator
// read globals named `_preset_*` (a routing layer between the Customizer
// values and an optional paper-thickness preset table). This file has no
// preset table, so the shim just passes Customizer values through. This
// keeps the copied modules byte-identical to their cylinder counterparts,
// minimising drift risk if we ever extract a shared braille_common.scad.
_preset_rounded_dot_base_diameter      = rounded_dot_base_diameter;
_preset_rounded_dot_base_height        = rounded_dot_base_height;
_preset_rounded_dot_dome_diameter      = rounded_dot_dome_diameter;
_preset_rounded_dot_dome_height        = rounded_dot_dome_height;

_preset_emboss_dot_base_diameter       = emboss_dot_base_diameter;
_preset_emboss_dot_height              = emboss_dot_height;
_preset_emboss_dot_flat_hat            = emboss_dot_flat_hat;

_preset_bowl_counter_dot_base_diameter = bowl_counter_dot_base_diameter;
_preset_counter_dot_depth              = counter_dot_depth;

_preset_cone_counter_dot_base_diameter = cone_counter_dot_base_diameter;
_preset_cone_counter_dot_height        = cone_counter_dot_height;
_preset_cone_counter_dot_flat_hat      = cone_counter_dot_flat_hat;

// Active height (used for placing emboss dots on the face surface).
active_emboss_height = use_rounded_dots
    ? (_preset_rounded_dot_base_height + _preset_rounded_dot_dome_height)
    : _preset_emboss_dot_height;

// Active counter recess depth (used for indicator recess depth on counter plate).
active_counter_height = use_rounded_dots
    ? _preset_counter_dot_depth
    : _preset_cone_counter_dot_height;

// Spacing pass-through aliases (mirrors the cylinder generator's
// `active_*` naming so the copied modules stay readable).
active_grid_columns  = effective_grid_columns;
active_grid_rows     = effective_grid_rows;
active_cell_spacing  = cell_spacing;
active_line_spacing  = line_spacing;
active_dot_spacing   = dot_spacing;

// Grid dimensions (accounting for indicator columns)
actual_grid_columns = indicator_on ? (active_grid_columns + 2) : active_grid_columns;
grid_width  = (actual_grid_columns - 1) * active_cell_spacing;
grid_height = (active_grid_rows - 1) * active_line_spacing;

// Rendered content extent (what is actually drawn after capacity truncation)
rendered_cols = min(content_max_len, active_grid_columns);
rendered_rows = min(content_rows, active_grid_rows);
content_cols_with_ind = rendered_cols + (indicator_on ? 2 : 0);
// Center-to-center extents of the rendered block; empty text falls back to capacity
content_width  = (rendered_cols == 0) ? grid_width  : (content_cols_with_ind - 1) * active_cell_spacing;
content_height = (rendered_rows == 0) ? grid_height : (rendered_rows - 1) * active_line_spacing;
// Indicator rows actually rendered (emboss plate); empty text falls back to capacity
indicator_rows_rendered = (rendered_rows == 0) ? active_grid_rows : rendered_rows;

// Per-cell dot offsets — planar (X/Y) instead of the cylinder's angular form.
// `dot_positions[i]` is `[row, col]` where row 0/1/2 = top/middle/bottom of the
// braille cell and col 0/1 = left/right column. In our face-local frame, +Y is
// down-the-slope (see face_transform()), so row 0 must get a NEGATIVE Y offset
// to sit at the TOP of the cell. This is the only sign flip vs. the cylinder
// generator's `dot_row_offsets = [+ds, 0, -ds]`.
dot_col_x_offsets = [-active_dot_spacing / 2, +active_dot_spacing / 2];
dot_row_y_offsets = [-active_dot_spacing,      0,                     +active_dot_spacing];
dot_positions     = [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]];

// Counter plate recess radii (spherical cap, identical formula to cylinder)
_bowl_a = _preset_bowl_counter_dot_base_diameter / 2;
_bowl_h = _preset_counter_dot_depth;
bowl_recess_radius = (_bowl_a * _bowl_a + _bowl_h * _bowl_h) / (2 * _bowl_h);
bowl_center_offset = bowl_recess_radius - _bowl_h;

// -----------------------------------------------------------------------------
// Leaning-card geometry (calculated) — flat sheared slab on the bed
// -----------------------------------------------------------------------------
// The card is a thin flat slab leaning back at face_angle_deg, sitting on the bed
// exactly as it sits on a desk = as it prints. Global axes: +X = card width,
// +Y = forward (toward the reader / outward face normal direction), +Z = up. The
// card leans back as z rises (its top tips toward -Y); the reading (braille) face
// is the +Y/up face, and the back face is the down-facing OVERHANG that the fins
// support.
//
//   C (0, card_height)            <- face TOP (origin of face_transform())
//    |\
//    | \   reading/braille face (+Y normal), leans back
//    |  \
//    |   \
//    |    B (base_run, 0)         = face BOTTOM, on the bed
//    +-------------------> Y
//
// With the reading face as the leaning edge of length effective_card_face_height_mm:
//   card_height = effective_card_face_height_mm * sin(face_angle_deg)  (vertical height H)
//   base_run    = effective_card_face_height_mm * cos(face_angle_deg)  (horizontal run R)
// The slab has thickness card_thickness_mm measured horizontally (along Y) — i.e.
// the cross-section is a parallelogram sheared in Y, with flat top/bottom edges
// resting parallel to the bed. For 75 deg, base_run / card_height = 1/tan(75) =
// ~0.27. Fins (not the body) provide all print stability.
//
// Effective card face dimensions: auto-sized from the braille block (content
// extent + dot overhang + margins) when auto_size_card = On, otherwise the
// manual sliders. The Customizer can't write computed values back into the
// sliders, so the effective size is reported via echo() instead.
// Outermost dot extent beyond cell centers: half a dot column/row pitch + largest dot radius
_max_dot_dia = max([rounded_dot_base_diameter, emboss_dot_base_diameter,
                    bowl_counter_dot_base_diameter, cone_counter_dot_base_diameter]);
_block_w = content_width  + active_dot_spacing     + _max_dot_dia; // dot columns at +/- dot_spacing/2
_block_h = content_height + 2 * active_dot_spacing + _max_dot_dia; // dot rows at +/- dot_spacing

effective_card_face_width_mm  = auto_size_on
    ? max(_block_w + 2 * auto_size_margin_mm, 30)   // 30 mm floor keeps the card printable
    : card_face_width_mm;
effective_card_face_height_mm = auto_size_on
    ? max(_block_h + 2 * auto_size_margin_mm, 20)   // 20 mm floor
    : card_face_height_mm;

card_height = effective_card_face_height_mm * sin(face_angle_deg);
base_run    = effective_card_face_height_mm * cos(face_angle_deg);

// Y of the card's BACK face at height z, used to place break-away bridges. The
// front (reading) face runs from B=(base_run,0) up to C=(0,card_height); the back
// face is that line shifted -card_thickness_mm in Y.
function back_y(z) = base_run * (1 - z / card_height) - card_thickness_mm;

// =============================================================================
// HELPER FUNCTIONS  (copied verbatim from the cylinder generator)
// =============================================================================
function is_braille_char(c) = (c >= 10240 && c <= 10495);
function has_invalid_chars(str) =
    len(str) == 0 ? false :
    len([for (i = [0:len(str)-1]) if (!is_braille_char(ord(str[i]))) i]) > 0;
function get_dot_pattern(char) =
    let(code = ord(char))
    (code >= 10240 && code <= 10495) ?
        let(pattern = code - 10240)
        [
            (pattern % 2) >= 1 ? 1 : 0,
            floor(pattern / 2)  % 2 >= 1 ? 1 : 0,
            floor(pattern / 4)  % 2 >= 1 ? 1 : 0,
            floor(pattern / 8)  % 2 >= 1 ? 1 : 0,
            floor(pattern / 16) % 2 >= 1 ? 1 : 0,
            floor(pattern / 32) % 2 >= 1 ? 1 : 0
        ]
    : [0, 0, 0, 0, 0, 0];

// =============================================================================
// INDICATOR SHAPE MODULES  (adapted from the cylinder generator)
// =============================================================================
INDICATOR_TRIANGLE_DEPTH_EMBOSS = 0.6;
INDICATOR_RECT_DEPTH_EMBOSS     = 0.5;

// "INVALID CHARACTERS" warning text placement (above the card top)
INVALID_TEXT_Z_OFFSET   = 5;
INVALID_TEXT_SIZE       = 5;
INVALID_TEXT_DEPTH      = 2;
INVALID_TEXT_STACK_GAP  = 8;

module indicator_triangle_2d(rotate_180 = false) {
    polygon(points = rotate_180 ?
        [
            [+active_dot_spacing/2, +active_dot_spacing],
            [+active_dot_spacing/2, -active_dot_spacing],
            [-active_dot_spacing/2, 0]
        ] :
        [
            [-active_dot_spacing/2, -active_dot_spacing],
            [-active_dot_spacing/2, +active_dot_spacing],
            [+active_dot_spacing/2, 0]
        ]
    );
}

module indicator_rectangle_2d() {
    translate([active_dot_spacing/2, 0])
        square([active_dot_spacing, 2 * active_dot_spacing], center = true);
}

module indicator_triangle_prism_centered(depth, rotate_180 = false) {
    translate([0, 0, -depth/2])
        linear_extrude(height = depth)
            indicator_triangle_2d(rotate_180 = rotate_180);
}

module indicator_rectangle_prism_centered(depth) {
    translate([0, 0, -depth/2])
        linear_extrude(height = depth)
            indicator_rectangle_2d();
}

// =============================================================================
// DOT CREATION MODULES  (copied verbatim from the cylinder generator)
// =============================================================================
// `braille_dot_centered()` builds the dot at the origin with its central
// axis on +Z and total height centred at z = 0. To sit on a surface, the
// caller translates by +totalHeight/2. Used unchanged on the flat face.
module braille_dot_centered() {
    _total_height = use_rounded_dots ?
                    (_preset_rounded_dot_base_height + _preset_rounded_dot_dome_height) :
                    _preset_emboss_dot_height;
    if (use_rounded_dots) {
        _dome_r = _preset_rounded_dot_dome_diameter / 2;
        _R_sphere = (_dome_r * _dome_r + _preset_rounded_dot_dome_height * _preset_rounded_dot_dome_height) / (2 * _preset_rounded_dot_dome_height);
        _center_z = _preset_rounded_dot_base_height + _preset_rounded_dot_dome_height - _R_sphere;
        translate([0, 0, -_total_height / 2]) {
            union() {
                translate([0, 0, _preset_rounded_dot_base_height / 2])
                cylinder(
                    h  = _preset_rounded_dot_base_height,
                    r1 = _preset_rounded_dot_base_diameter / 2,
                    r2 = _preset_rounded_dot_dome_diameter / 2,
                    center = true,
                    $fn = cone_segments
                );
                intersection() {
                    translate([0, 0, _center_z])
                    sphere(r = _R_sphere, $fn = quality_fn);
                    translate([0, 0, _preset_rounded_dot_base_height + _R_sphere])
                    cube([_R_sphere * 4, _R_sphere * 4, _R_sphere * 2], center = true);
                }
            }
        }
    } else {
        cylinder(
            h  = _preset_emboss_dot_height,
            r1 = _preset_emboss_dot_base_diameter / 2,
            r2 = _preset_emboss_dot_flat_hat / 2,
            center = true,
            $fn = cone_segments
        );
    }
}

// Counter recess. Built so the opening sits at z = 0 and the recess extends
// into z < 0 — exactly what we need to difference() out of the face panel's
// front (z = 0) surface.
module counter_recess() {
    if (use_rounded_dots) {
        translate([0, 0, bowl_center_offset])
            sphere(r = bowl_recess_radius, $fn = quality_fn);
    } else {
        translate([0, 0, -_preset_cone_counter_dot_height / 2])
            cylinder(
                h  = _preset_cone_counter_dot_height,
                r1 = _preset_cone_counter_dot_flat_hat / 2,
                r2 = _preset_cone_counter_dot_base_diameter / 2,
                center = true,
                $fn = cone_segments
            );
    }
}

// =============================================================================
// FACE-LOCAL COORDINATE FRAME
// =============================================================================
// face_transform() places its children in a face-local frame whose +X axis is
// the face width direction, +Y axis is DOWN-THE-SLOPE (so row 0 of the braille
// grid sits at the TOP of the face — same convention as the cylinder
// generator's row indexing), and +Z axis is the OUTWARD face normal.
//
// The origin is the centre of the reading face's TOP edge, the top-front corner
// C of the leaning slab. In global coordinates that point is (0, 0, card_height).
//
// A rotation of -face_angle_deg about +X is the unique single-axis rotation
// that maps local +Z to the outward face normal (0, sin(face), cos(face))
// while keeping the frame right-handed. Local +Y then necessarily points
// down-the-slope (this is the reason `dot_row_y_offsets` has the row 0/2
// signs flipped relative to the cylinder generator).
module face_transform() {
    translate([0, 0, card_height])
        rotate([-face_angle_deg, 0, 0])
            children();
}

// =============================================================================
// CARD BODY + SUPPORT FIN MODULES
// =============================================================================

// Extrude a Y-Z profile across global X. linear_extrude builds in local XY and
// grows along local +Z; rotate([90,0,90]) maps local (x,y,z) -> global (z,x,y),
// so the 2D profile (drawn as [y_global, z_global]) lands in the global Y-Z plane
// and the extrusion thickness runs along global +X.
module yz_prism(profile, x_start, width) {
    translate([x_start, 0, 0])
        rotate([90, 0, 90])
            linear_extrude(height = width)
                polygon(profile);
}

// --- Flat leaning card body --------------------------------------------------
//
// Side profile in the Y-Z plane (constant X) is a parallelogram sheared in Y, so
// the slab leans back at face_angle_deg while resting flat on the bed. Vertices
// CCW, with t = card_thickness_mm:
//   B' (base_run - t, 0)        — back-bottom (on the bed)
//   B  (base_run,     0)        — front-bottom (face bottom, on the bed)
//   C  (0,            card_height) — front-top (face top = face_transform origin)
//   C' (-t,           card_height) — back-top
// Edge B->C is the reading face at face_angle_deg; edge C'->B' is the back/under
// overhang the fins support. Both top and bottom edges are flat (parallel to bed).
CARD_TRAP = [
    [base_run - card_thickness_mm, 0],
    [base_run,                     0],
    [0,                            card_height],
    [-card_thickness_mm,           card_height]
];

module card_body() {
    yz_prism(CARD_TRAP, -effective_card_face_width_mm / 2, effective_card_face_width_mm);
}

// --- Break-away support fins -------------------------------------------------
//
// Each fin is a right-triangle prism standing fin_offset_mm behind the card's
// back face, with the right angle at the (vertical) back spine. Side profile
// (Y-Z), CCW, with t = card_thickness_mm, g = fin_offset_mm,
// fh = fin_height_frac * card_height:
//   back-bottom  (-t - g,            0)
//   inner-bottom (base_run - t - g,  0)   — toward the card, on the bed
//   top          (-t - g,            fh)  — meets the back spine at the top
// Base run = base_run, height = fh, so the hypotenuse runs parallel to the card
// back at the offset g (auto-matching the card's height/angle).
function fin_top_z() = fin_height_frac * card_height;

module support_fin_2d() {
    polygon([
        [-card_thickness_mm - fin_offset_mm,            0],
        [base_run - card_thickness_mm - fin_offset_mm,  0],
        [-card_thickness_mm - fin_offset_mm,            fin_top_z()]
    ]);
}

// One fin prism centred on column x (thickness fin_thickness_mm along X).
module support_fin(x) {
    translate([x - fin_thickness_mm / 2, 0, 0])
        rotate([90, 0, 90])
            linear_extrude(height = fin_thickness_mm)
                support_fin_2d();
}

// Flat brim flange under one fin: a thin slab covering the fin's bed footprint in
// Y, expanded by brim_width_mm on each side in X and Y, from z=0 up brim_thickness.
module fin_brim(x) {
    if (brim_width_mm > 0 && brim_thickness_mm > 0) {
        // Fin footprint in Y at the bed: from the back spine to the inner-bottom.
        y_back  = -card_thickness_mm - fin_offset_mm;
        y_front = base_run - card_thickness_mm - fin_offset_mm;
        y_lo = min(y_back, y_front) - brim_width_mm;
        y_hi = max(y_back, y_front) + brim_width_mm;
        translate([x - fin_thickness_mm / 2 - brim_width_mm, y_lo, 0])
            cube([fin_thickness_mm + 2 * brim_width_mm, y_hi - y_lo, brim_thickness_mm]);
    }
}

// Break-away bridges for the fin at column x: bridge_count small boxes climbing
// the gap, each merging bridge_contact_mm into the card back face and overlapping
// the fin so the union is one manifold solid. Bridge heights are spread evenly
// over [z_lo, fin top], starting clear of the bed.
module bridges(x) {
    eps   = 0.01;
    z_lo  = max(bridge_height_mm, 2);          // start clear of the bed/brim
    // Clamp so small fin_height_frac (short fins) can't invert the bridge span.
    z_hi  = max(z_lo, fin_top_z() - bridge_height_mm / 2);
    for (k = [0 : bridge_count - 1]) {
        z_k = (bridge_count == 1)
            ? (z_lo + z_hi) / 2
            : z_lo + (z_hi - z_lo) * k / (bridge_count - 1);
        // Span from inside the card face (back_y(z) + contact) all the way back to
        // the fin's vertical back spine, so the box always overlaps the fin solid
        // (true for any fin_height_frac) and the union stays one manifold piece.
        y_far  = -card_thickness_mm - fin_offset_mm - eps;  // through/into the fin
        y_near = back_y(z_k) + bridge_contact_mm;           // merged into the card
        translate([x - bridge_width_mm / 2, y_far, z_k - bridge_height_mm / 2])
            cube([bridge_width_mm, y_near - y_far, bridge_height_mm]);
    }
}

// Fin X column positions across the width: stepped by fin_interval_mm and forced
// to include both outer edges (masukomi's "side fins" so the edges don't float).
function fin_x_positions() =
    let(
        half  = effective_card_face_width_mm / 2,
        n     = max(1, floor(effective_card_face_width_mm / fin_interval_mm)),
        inner = [for (i = [0 : n]) -half + i * fin_interval_mm]
    )
    // Always include the two edges; de-dup any inner column within eps of an edge.
    concat(
        [-half],
        [for (xi = inner) if (xi > -half + 1e-3 && xi < half - 1e-3) xi],
        [half]
    );

// Full fin structure: fins + brims + bridges at every column.
module support_fins_all() {
    for (x = fin_x_positions()) {
        support_fin(x);
        fin_brim(x);
        bridges(x);
    }
}

// =============================================================================
// FACE-LOCAL BRAILLE LAYOUT
// =============================================================================
// All of the modules below run inside face_transform(): local +X = width
// (centred at 0), local +Y = down-the-slope (0 = face top, +grid_height = face
// bottom), local +Z = outward. y_pos = vertical centre of a row in this frame.

// Vertical centre of a braille row in face-local Y. row 0 = top. Centers the
// rendered content block on the (effective) face; braille_y_adjust is an
// additive nudge on top (default 0 = centered).
function face_row_y(row) =
    (effective_card_face_height_mm - content_height) / 2
    + row * active_line_spacing
    + braille_y_adjust;

// Horizontal centre of a grid column (actual column index, including indicator
// columns when enabled) in face-local X. Lines are left-aligned within the
// block; the block is centered by the longest line. braille_x_adjust is an
// additive nudge on top (default 0 = centered).
function face_col_x(actual_col) =
    -content_width/2 + actual_col * active_cell_spacing + braille_x_adjust;

module place_face_dots_for_text() {
    lines = [Line_1, Line_2, Line_3, Line_4];
    for (row = [0 : min(active_grid_rows - 1, len(lines) - 1)]) {
        if (len(lines[row]) > 0) {
            y_pos = face_row_y(row);
            for (col = [0 : min(active_grid_columns - 1, len(lines[row]) - 1)]) {
                actual_col = indicator_on ? (col + 2) : col;
                x_cell = face_col_x(actual_col);
                dots = get_dot_pattern(lines[row][col]);
                for (i = [0:5]) {
                    if (dots[i] == 1) {
                        dot_pos = dot_positions[i];
                        dot_x = x_cell + dot_col_x_offsets[dot_pos[1]];
                        dot_y = y_pos  + dot_row_y_offsets[dot_pos[0]];
                        translate([dot_x, dot_y, active_emboss_height / 2])
                            braille_dot_centered();
                    }
                }
            }
        }
    }
}

module place_face_recesses_all_cells() {
    // Counter plate: a recess at EVERY possible dot position in the grid,
    // matching how cylinder_counter_plate() recesses all cells regardless of
    // the typed text.
    for (row = [0 : active_grid_rows - 1]) {
        y_pos = face_row_y(row);
        for (col = [0 : active_grid_columns - 1]) {
            actual_col = indicator_on ? (col + 2) : col;
            x_cell = face_col_x(actual_col);
            for (i = [0:5]) {
                dot_pos = dot_positions[i];
                dot_x = x_cell + dot_col_x_offsets[dot_pos[1]];
                dot_y = y_pos  + dot_row_y_offsets[dot_pos[0]];
                translate([dot_x, dot_y, 0])
                    counter_recess();
            }
        }
    }
}

// One row's indicator recesses (triangle at column 0, rectangle at column 1)
// in the raw face-local layout. The emboss plate renders this (and the dots)
// under mirror([1,0,0]) so it reads correctly; the counter plate renders it
// un-mirrored, making the two plates a true left-right mirrored pair.
module place_face_row_indicators(y_pos, tri_depth, rect_depth) {
    tri_x  = face_col_x(0);
    rect_x = face_col_x(1);
    translate([tri_x, y_pos, 0])
        indicator_triangle_prism_centered(tri_depth, rotate_180 = true);
    translate([rect_x, y_pos, 0])
        indicator_rectangle_prism_centered(rect_depth);
}

// =============================================================================
// WARNING MODULES  (adapted from the cylinder generator)
// =============================================================================
// Each warning is wrapped in the `%` background modifier so it is visible in
// the F5 preview but EXCLUDED from the F6 render / STL export (fixing the old
// bug where warning text fused into the exported solid). Stacked into fixed
// slots; the whole system is gated by warnings_on (the [Warnings] tab).
//
// NOTE: the `%` modifier may render the text transparent gray instead of red in
// some OpenSCAD builds — acceptable; visibility plus export-exclusion is the goal.
module warning_slot(k, msg) {
    translate([0, base_run/2, card_height + INVALID_TEXT_Z_OFFSET + k * INVALID_TEXT_STACK_GAP])
        %color("red")
            linear_extrude(height = INVALID_TEXT_DEPTH)
                text(msg, size = INVALID_TEXT_SIZE, halign = "center", valign = "center");
}

module warnings_3d() {
    _invalid = has_invalid_chars(Line_1) || has_invalid_chars(Line_2) ||
               has_invalid_chars(Line_3) || has_invalid_chars(Line_4);
    _too_long = content_max_len > active_grid_columns;
    _too_many = content_rows > active_grid_rows;
    if (warnings_on && _invalid) warning_slot(0, "INVALID CHARACTERS");
    if (warnings_on && _too_long) warning_slot(1, "TEXT TOO LONG");
    if (warnings_on && _too_many) warning_slot(2, "TOO MANY LINES");
}

// =============================================================================
// TOP-LEVEL PLATES
// =============================================================================

// READING ORIENTATION / EMBOSS-vs-COUNTER MIRRORING
// -------------------------------------------------
// On the parent cylinder generator the emboss plate reads correctly (left to
// right, indicators on the left) with NO mirror, because increasing column ->
// increasing wrap angle -> the reader's right. On this back-leaning planar
// face the same local +X maps to the reader's LEFT, so the raw layout would
// read right-to-left. We therefore mirror the EMBOSS content in face-local X
// so the directly-read emboss plate reads correctly. The COUNTER plate is then
// produced by the UN-mirrored layout, making it the exact left-right mirror of
// the emboss plate (so recesses sit under dots when the plates mate) — the
// same emboss/counter relationship the cylinder achieves via angle negation.
module card_emboss_plate() {
    difference() {
        union() {
            card_body();
            // Raised dots on the outer face surface (mirrored to read L->R).
            face_transform()
                mirror([1, 0, 0])
                    place_face_dots_for_text();
            warnings_3d();
        }
        // Indicators are ALWAYS recessed (emboss + counter both subtract them).
        // Only stamp indicators on rendered content rows (not empty capacity rows).
        if (indicator_on) {
            face_transform()
                mirror([1, 0, 0])
                    for (row = [0 : indicator_rows_rendered - 1]) {
                        place_face_row_indicators(
                            face_row_y(row),
                            INDICATOR_TRIANGLE_DEPTH_EMBOSS,
                            INDICATOR_RECT_DEPTH_EMBOSS
                        );
                    }
        }
    }
}

module card_counter_plate() {
    difference() {
        union() {
            card_body();
            warnings_3d();
        }
        // Un-mirrored layout = exact left-right mirror image of the emboss
        // plate. Recess every possible dot position into the face.
        face_transform()
            place_face_recesses_all_cells();
        if (indicator_on) {
            face_transform()
                for (row = [0 : active_grid_rows - 1]) {
                    place_face_row_indicators(
                        face_row_y(row),
                        active_counter_height,
                        active_counter_height
                    );
                }
        }
    }
}

// =============================================================================
// CONSOLE DIAGNOSTICS  (always printed; independent of the 3D warning toggle)
// =============================================================================
echo(str("Content: ", content_rows, " lines, longest ", content_max_len, " cells"));
echo(str("Card face (effective): ", effective_card_face_width_mm, " x ",
         effective_card_face_height_mm, " mm",
         auto_size_on ? " [auto-sized - manual sliders ignored]" : " [manual]"));

// Per-line invalid characters (actionable: where to re-translate)
for (i = [0:3])
    if (has_invalid_chars(_all_lines[i]))
        echo(str("WARNING: Line ", i + 1, " contains non-braille characters. ",
                 "Re-translate at branah.com with Unicode Braille output."));

// Per-line over capacity (only meaningful in manual mode; auto mode can't overflow)
for (i = [0:3])
    if (!auto_size_on && len(_all_lines[i]) > active_grid_columns)
        echo(str("WARNING: Line ", i + 1, " is ", len(_all_lines[i]),
                 " cells but capacity is ", active_grid_columns,
                 ". Increase grid_columns, shorten the line, or set auto_size_card = On."));

// Too many lines (manual mode)
if (!auto_size_on && content_rows > active_grid_rows)
    echo(str("WARNING: text uses ", content_rows, " lines but grid_rows is ",
             active_grid_rows, ". Increase grid_rows or set auto_size_card = On."));

// Support fin count feedback
if (fins_on)
    echo(str("Support fins: ", len(fin_x_positions()), " at ", fin_interval_mm, " mm interval"));

// Cheap, high-confidence sanity checks
if (!is_emboss_plate && card_thickness_mm < active_counter_height + 0.7)
    echo(str("WARNING: card_thickness_mm (", card_thickness_mm,
             ") is near the recess depth (", active_counter_height,
             "); counter-plate recesses may break through. Increase card_thickness_mm."));
if (cell_spacing < dot_spacing * 2)
    echo(str("WARNING: cell_spacing (", cell_spacing, ") < dot_spacing*2 (",
             dot_spacing * 2, "); braille cells will overlap."));
if (line_spacing < dot_spacing * 2 + _max_dot_dia)
    echo(str("WARNING: line_spacing (", line_spacing, ") < dot_spacing*2 + dot diameter (",
             dot_spacing * 2 + _max_dot_dia, "); braille rows will collide."));

// =============================================================================
// MAIN RENDERING
// =============================================================================
// The active plate (card + braille) is fused with the break-away support-fin
// structure into a single solid so it slices as one print-ready object.
union() {
    if (is_emboss_plate) {
        card_emboss_plate();
    } else {
        card_counter_plate();
    }
    if (fins_on) {
        support_fins_all();
    }
}

// End of file
