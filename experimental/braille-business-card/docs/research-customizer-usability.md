# Research Report: Customizer Usability for the Wedge Card Generator

Status: research / docs companion to the "Wedge Card Usability Overhaul". Documents the OpenSCAD Customizer constraints that shaped the redesign, the rationale behind the centering / auto-size / warning decisions, and the ideas that were deliberately deferred or rejected.

Scope: applies only to `Braille_Wedge_Card_STL_Generator.scad` (and its `.json` presets) in this folder. The parent `Braille_Cylinder_STL_Generator.scad` is untouched.

---

## TL;DR

- The OpenSCAD Customizer can **read** parameters from sliders/dropdowns but **cannot write computed values back** into them. Auto-sizing is therefore feasible (all text metrics are statically computable at compile time) but the resulting card size is surfaced via `echo()` to the console, not shown in the width/height sliders.
- Customizer **tab order follows the declaration order** of the `/* [Tab] */` groups in the file, so reordering tabs = reordering the parameter blocks.
- The `%` (background) modifier renders geometry in the **F5 preview only** and **excludes it from F6 render / STL export**. This is exactly the right tool for preview-only warning text, and it fixes a real bug: the old `color("red") ... text(...)` warnings were fused into the exported solid.
- Centering is done from the **rendered content extent**, not the grid capacity, with a fallback to capacity when the text is empty. Both plates share the same layout functions, which is the invariant that keeps the emboss/counter pair mating.

---

## 1. Customizer constraints discovered

### 1.1 Tab order = declaration order
The Customizer groups parameters by `/* [Tab Name] */` markers and lists the tabs in the order the markers appear in the file. To put novice-relevant controls first (text, plate, card size, warnings) we physically moved the parameter blocks; there is no separate ordering directive. Parameters declared before the first marker, or under `/* [Hidden] */`, are not shown in the normal Customizer view.

### 1.2 Sliders cannot display computed values
A Customizer control is bound to a top-level variable assignment with a `// [min:step:max]` (or `// [a, b, c]`) annotation. The control is a one-way input: editing it sets the variable, but assigning the variable elsewhere in the script does **not** update the control. Consequently:

- `card_face_width_mm` / `card_face_height_mm` remain plain sliders.
- The auto-sized result is computed into separate variables (`effective_card_face_width_mm` / `effective_card_face_height_mm`) and **reported via `echo()`** so the user can read the actual printed size in the console. Example output:
  `ECHO: "Card face (effective): 55.4 x 28.9 mm [auto-sized - manual sliders ignored]"`

This is the single accepted limitation of the auto-size feature: you cannot see the size in a slider, only in the console.

### 1.3 The `%` background modifier excludes geometry from render/export
Per the OpenSCAD modifier-characters documentation, prefixing an object with `%` makes it a **background** object: drawn (transparent/gray) in the preview, but ignored by the CGAL/Manifold render and therefore absent from the exported STL. (See OpenSCAD User Manual, "Modifier Characters".) We verified this with the CLI: rendering with `show_warnings="On"` and `show_warnings="Off"` while a warning condition was active produced **byte-identical STL files**, proving the warning geometry never reaches the export.

> Note: some OpenSCAD builds render `%`-modified geometry as transparent gray rather than honoring `color("red")`. That is acceptable — the goal is preview visibility plus guaranteed export-exclusion, not a specific color.

---

## 2. Why the old warnings were dangerous, and the fix

The previous `invalid_chars_warning()` emitted `color("red") linear_extrude() text(...)` as **real solid geometry** unioned into the plate. In F5 it looked like a helpful red label, but in F6/export that text became part of the manifold and was written into the STL — a silent way to ship a ruined print.

Fix: every warning slot is now wrapped in `%` inside `warnings_3d()`, and the whole system is gated by the `show_warnings` toggle (`[Warnings]` tab). Warnings are visible in preview, never exported, and can be turned off entirely. A new `TOO MANY LINES` slot was added alongside the existing `INVALID CHARACTERS` and `TEXT TOO LONG`. Console `echo()` diagnostics fire independently of the 3D toggle with actionable wording (which line, by how much, and the exact remedy).

---

## 3. Centering rationale

### 3.1 Left-aligned block, centered by the longest line
Braille is read left-to-right and benefits from a **stable left margin / indicator column** across lines. So lines are left-aligned within the text block, and the *block as a whole* is centered on the face using the **longest line** as the reference width (`content_width`). Per-line centering was rejected (see §6) because it would make the start-of-line indicator column ragged and harder to track by touch.

### 3.2 Rendered extent, with an empty-text fallback
Centering uses the **rendered** content extent (`rendered_cols` / `rendered_rows`, after capacity truncation), not the full grid capacity. This keeps short text visually centered instead of being pushed up/left by empty capacity cells. When all lines are empty, the extents fall back to the capacity-based `grid_width` / `grid_height`, so a blank counter plate still receives a centered, full recess grid (preserving prior behavior).

`braille_x_adjust` / `braille_y_adjust` remain **additive** offsets on top of centering (defaults 0), satisfying "centered unless the offset has been adjusted." The old presets' `braille_y_adjust = 4.47` nudge — which manually compensated for grid-based centering — is no longer needed and is reset to 0.

### 3.3 Shared layout functions = the plate-mating invariant
`face_col_x()` and `face_row_y()` are the **single source of positioning** for both plates. The emboss plate is `mirror([1,0,0])` of the same layout; the counter plate uses it un-mirrored. Because both consume the same centering offset, any shift applies identically to both, so recesses always sit under dots when the plates mate. The emboss indicator loop is limited to `indicator_rows_rendered` (only rows with text); the counter plate intentionally recesses the full capacity grid (extra recesses are negative features and can't impede mating).

---

## 4. Auto-size formula and margin guidance

Auto mode sets grid capacity equal to content (`effective_grid_columns = max(content_max_len, 1)`, `effective_grid_rows = max(content_rows, 1)`), so `TEXT TOO LONG` / `TOO MANY LINES` cannot occur. The face is then sized from the rendered block plus the dot overhang and a margin:

```
block_w = content_width  + dot_spacing     + max_dot_diameter
block_h = content_height + 2 * dot_spacing  + max_dot_diameter
effective_width  = max(block_w + 2*margin, 30 mm floor)
effective_height = max(block_h + 2*margin, 20 mm floor)
```

The `+ dot_spacing/+2*dot_spacing + max_dot_diameter` terms account for the outermost dots, which sit half a dot-pitch beyond the cell centers plus their own radius. The 30 mm / 20 mm floors keep tiny inputs printable.

**Margin default (`auto_size_margin_mm = 6`):** BANA's size-and-spacing guidance (reference [H] in the file header) calls for generous clear space around braille so the reader's finger isn't crowded by edges. A full document margin is too large at business-card scale, so 6 mm was chosen as a card-scale compromise — comfortably clear of the dots while keeping the card compact. It is adjustable from 2–20 mm.

---

## 5. Range-widening rationale

The support-fin and bridge ranges were widened substantially (defaults unchanged) to let the card scale from a couple of edge fins up to hundreds:

- `fin_interval_mm = [1:0.5:200]`: at the maximum only the **two always-present edge fins** remain — the minimum is 2 by design, following masukomi's "add side fins so the edges don't float" lesson (reference [F]). At the minimum a fin lands every millimeter.
- Wider `fin_offset_mm`, `fin_thickness_mm`, `bridge_*`, `brim_*`, and `fin_height_frac` down to 0.05 give room for very different printers/materials.

**Robustness fix for short fins:** a small `fin_height_frac` can drive `fin_top_z()` below the bridge start height, which would invert the bridge span. `bridges()` now clamps `z_hi = max(z_lo, fin_top_z() - bridge_height_mm/2)` so bridges degrade gracefully (verified at `fin_height_frac = 0.05`).

---

## 6. Deferred / rejected ideas

- **Per-line centering** — rejected. It destabilizes the left indicator column and the touch-reading start position; block-centering by the longest line is the braille-friendly choice.
- **Writing the auto-size back into the width/height sliders** — impossible (the Customizer is one-way; §1.2). Reporting via `echo()` is the accepted substitute.
- **Fin-count override (set N fins directly)** — deferred. `fin_interval_mm` over its new wide range already spans 2 → hundreds; a second redundant control adds confusion.
- **`assert()`-based validation that aborts the render** on bad input — rejected. A hard abort is hostile in a Customizer workflow; non-blocking `echo()` diagnostics plus preview-only `%` warnings inform without preventing experimentation.

---

## References

Reuses the file-header reference list; the most relevant here:

- [F] masukomi, "Manual Support Fins for 3D Printing" — side fins so edges don't float; ~1 mm offset; small sprues.
- [H] BANA, "Size and Spacing of Braille Characters" — generous clear space / margins around braille.
- OpenSCAD User Manual, "Modifier Characters" — the `%` background modifier (preview-only, excluded from render/export).
- OpenSCAD User Manual, "Customizer" — tab grouping by `/* [Tab] */` markers and one-way parameter binding.
