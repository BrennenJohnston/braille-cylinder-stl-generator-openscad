# Research Report: Combined Dome + Tapered-Frustum Braille Dots, and Slicer Techniques for FDM Dot Quality

Status: research / docs-only. No `.scad` changes. Companion to the `braille-business-card` plan's `01-research-synthesis.md` and `02-design-proposal.md`.

Scope of this report (the two things you asked):

1. Is the **combined dome + tapered-frustum** dot (the repo's "Rounded" shape: `braille_dot_centered()`) a genuine fix for the long-standing quality problem of FDM braille dots on a **0.4 mm nozzle** home printer? Did it "accidentally solve" the horizontal/flat-print dot problem?
2. What **slicer settings / techniques** (including recent ones) can improve braille-dome quality on a standard 0.4 mm-nozzle FDM printer?

---

## TL;DR (the honest verdict)

- **Your intuition is partly right, and one part of it is more right than you think — but for a different reason than "more layers."**
- The single most important and **genuinely correct** insight hiding in your design: **a pure spherical-cap dome on a 1.5 mm base physically cannot be taller than 0.75 mm (a full hemisphere).** To reach the upper end of the legal dot-height range (0.6–0.9 mm) **while keeping the legal 1.5 mm base**, you *must* add a base section. Your **tapered frustum is exactly the mechanism that unlocks the 0.75–0.9 mm height band** — and it does so with a stable, wide footprint and a gentler base transition than a straight cylinder would. That is a real, defensible design advantage.
- **It does NOT, by itself, overcome the fundamental limit.** Surface smoothness is set by **layer count = dot_height / layer_height**, and the dot height is capped at ~0.9 mm by braille standards. The frustum redistributes and evens out the layer "steps"; it does not add layers beyond the height budget. The dominant levers remain **(1) print orientation and (2) layer height**, not dot profile.
- **The biggest payoff of the frustum is in the orientation the research already recommends (near-vertical, 75–90°), not flat printing.** When a dot is printed sticking *sideways* out of a near-vertical face, its underside is an **overhang**. A hemisphere's underside is a near-90° overhang at the wall; a **tapered frustum base turns that into a gentle cone-shaped overhang that prints far more cleanly without supports.** So the shape is best read as *"well-matched to vertical printing,"* rather than *"a fix for flat printing."*
- **It is not wholly novel.** "Cylinder/frustum base + rounded cap" is established prior art (e.g., `crowellhouse/BrailleMaker` uses a cylinder + hemisphere fillet with the rule `dotHeight ≤ dotDia/2`; `sav-iqbal/ML-OpenScad-Braille-Generator` switched from spheres to fillets precisely because *"prints are too pointy with a sphere… this also leads to unwanted strings"*). Your **parametric, independently-tunable taper + dome** is a sensible, better-engineered variant — not a brand-new principle.
- **"Sharp on top" is partly a feature, not only a bug.** ADA/BANA want **domed, not pointed** dots, and the landmark orientation study deliberately used **hemispheres with truncated (flat) tops**. The real enemy is *uncontrolled* sharpness — stringing, nibs, and a collapsing apex — not a deliberate, smooth truncation. Your combined shape lets you *design* a controlled small flat/round top instead of fighting an accidental one.

Bottom line: keep the combined dome+frustum shape — it is a good design — but position it as **the right dot for the vertically-printed card** and as a **modest, well-controlled improvement for the flat/fast mode**, layered on top of the two changes that matter most (orientation and a 0.1 mm braille layer height).

---

## 1. Your hypothesis, restated precisely

So we test the right claim, here is your idea in explicit terms:

> The common quality problem with FDM braille is the ~0.4 mm nozzle. Legal dots are only 1.5–1.6 mm wide and 0.6–0.9 mm tall, so a dome built up in +Z has very few layers (a coarse staircase), and its apex narrows below what a 0.4 mm nozzle can print, so the top ends up too large/flat/sharp. By using a **combined spherical-cap dome on top of a tapered frustum** (the repo's `Rounded` dot), the frustum can add a little height under the dome, giving **more, finer layer steps** and therefore a **smoother gradient** — possibly solving the flat-print quality problem.

The repo geometry that implements this is `braille_dot_centered()` — a frustum (`r1 = base/2 → r2 = dome/2`, height `base_height`) unioned with a true spherical cap of radius `R = (r² + h²) / (2h)`:

```468:510:Braille_Cylinder_STL_Generator.scad
module braille_dot_centered() {
    _total_height = use_rounded_dots ?
                    (_preset_rounded_dot_base_height + _preset_rounded_dot_dome_height) :
                    _preset_emboss_dot_height;

    if (use_rounded_dots) {
        // Spherical cap formula: R = (r² + h²) / (2h)
        _dome_r = _preset_rounded_dot_dome_diameter / 2;
        _R_sphere = (_dome_r * _dome_r + _preset_rounded_dot_dome_height * _preset_rounded_dot_dome_height) / (2 * _preset_rounded_dot_dome_height);
        _center_z = _preset_rounded_dot_base_height + _preset_rounded_dot_dome_height - _R_sphere;
```

Repo defaults: `rounded_dot_base_diameter = 1.5`, `rounded_dot_base_height = 0.5`, `rounded_dot_dome_diameter = 1.0`, `rounded_dot_dome_height = 0.5`. That is **frustum 1.5 → 1.0 mm over 0.5 mm**, topped by a **1.0 mm-diameter hemisphere 0.5 mm tall** (since `h = r = 0.5`, the cap is a perfect hemisphere). **Total height = 1.0 mm**, max width 1.5 mm.

> Flag for the card use-case: total height 1.0 mm **exceeds** the BANA/ADA signage maximum of 0.9 mm. Fine for the cylinder/medication context, but for an ADA business card keep `base_height + dome_height ≤ 0.9`.

---

## 2. Why FDM braille dots are hard (the two failure modes)

There are **two different** geometry problems, and they swap places depending on orientation. Conflating them is the source of most confusion.

```text
   FLAT / "horizontal" print (0°)            NEAR-VERTICAL print (75–90°)
   dot grows in +Z, apex up                  dot sticks out sideways from a wall

            __                                     wall │
          .'  '.   <- apex narrows below            face │   ___
         /      \     nozzle width -> truncates,    layers│  /   )  <- underside is an
        /        \    nubs/strings, "sharp top"     run   │ |    )     OVERHANG (worst
       /__________\                                 across│  \___)     at the wall)
      ===== bed =====                               dot   │_____
      steps are WORST near the flat apex            steps run with the finger sweep;
      (shallow slope); finger rubs the staircase    contact face is smooth; seams hide
```

- **Staircase error** at any point on a curved surface is roughly `step_width ≈ layer_height / tan(θ)`, where `θ` is the surface angle from horizontal. Near a dome's **apex** (θ → 0, nearly flat) the steps blow up; near the **base** (θ → 90°, steep) they vanish. So on a **flat-printed** dot the worst roughness and the apex truncation both sit **right where the finger reads** — the dome top. *(Corroborated by every adaptive-layer-height vendor: the feature exists specifically to fix the "staircase feeling" on spherical/sloped tops. [16])*
- **Start/stop seams**: the nozzle leaves a small nub each time it starts/stops a perimeter. On flat dots these nubs sit on top of the dot. The orientation study attributes much of the felt roughness to these per-layer seams. [1][7]
- **Footprint shrinkage**: independent FDM measurements show small dots come out **under** nominal — designed 0.5 mm height / 1.3 mm dia measured as **0.38 mm / 1.0 mm**, and center spacing also shrank. FDM systematically under-builds tiny rounded features. [3]
- **The orientation finding (the linchpin).** Puerta et al. (CHI 2024) tested 0–90° in 15° steps on Prusa MK3S+ / PLA, dots = **hemispheres with truncated flat tops** at BANA minima (base 1.5, height 0.6, in-cell 2.3, adjacent-cell 6.1, line 10.0 mm). Readers were **significantly faster and more comfortable at 75° and 90°**; flat (0°) was the worst. The mechanism: near-vertical printing moves the staircase/seams **off** the finger-contact surface (and onto the back/sides). They explicitly note that a **90° dot has overhangs for its first several layers** ("printed partially above the air"), and that **75° is a good compromise because it reduces those overhangs.** [1] Practitioner and standards bodies agree: tactiles.eu says vertical printing avoids "sharp-edged peaks" because the head can "pull through in one go"; the DIAGRAM Center and `Whosawhatsis`'s blind-reader survey both found side-printed dots smoother and more durable. [7][8]

**Takeaway:** orientation is the dominant lever, and it changes *which* geometry problem your dot shape needs to solve. That reframes your hypothesis (Section 3).

---

## 3. Does the combined dome + frustum actually help? (point-by-point)

### 3a. The strongest, genuinely-correct part: the frustum unlocks the legal height band

A spherical cap of base radius `r` has a **maximum height of `r`** (a full hemisphere). For the legal **1.5 mm base (r = 0.75 mm)**, a pure dome **tops out at 0.75 mm tall**. But the ADA/BANA height range runs **0.6–0.9 mm**. So:

- A **pure dome** can only occupy **0.6–0.75 mm** of the legal height range on a 1.5 mm base. To get taller you would have to either narrow the base (illegal/less stable) or stretch the cap past a hemisphere (impossible for a cap).
- Your **frustum + dome** can reach **any** height in 0.6–0.9 mm while keeping the full 1.5 mm base: put the extra height into the straight, steep frustum wall and keep a well-proportioned dome on top.

Why taller-within-legal helps: **more layers.** At a 0.1 mm braille layer height, a 0.6 mm dot is 6 layers; a 0.9 mm dot is 9 layers — **50% more steps describing the same curve = a visibly/tactually finer gradient.** This is the kernel of truth in "the frustum adds height for a smoother gradient," and it is real. The catch is only that the gain is **bounded by the 0.9 mm legal ceiling** — you cannot keep adding height indefinitely.

### 3b. The frustum evens out the steps (but does not remove the apex truncation)

A constant-slope frustum wall produces **uniform** small steps; a spherical cap's steps **grow toward the apex.** Worked example — both dots base 1.5 mm, total height 0.8 mm, layer height **0.1 mm** (8 layers). Radius (mm) at each layer top, and the per-layer step Δr:

| Layer top z (mm) | Pure cap r | Δr (cap) | Frustum+dome r | Δr (combined) |
|---|---|---|---|---|
| 0.1 | 0.750 | 0.000 | 0.667 | 0.083 |
| 0.2 | 0.736 | 0.014 | 0.583 | 0.083 |
| 0.3 | 0.708 | 0.028 | 0.500 (top of frustum) | 0.083 |
| 0.4 | 0.664 | 0.044 | 0.490 | 0.010 |
| 0.5 | 0.601 | 0.063 | 0.458 | 0.032 |
| 0.6 | 0.510 | 0.090 | 0.400 | 0.058 |
| 0.7 | 0.375 | 0.136 | 0.300 | 0.100 |
| 0.8 | ~0 (apex) | ~0.37 collapse | ~0 (apex) | ~0.30 collapse |

*(Combined dot here = frustum 1.5 → 1.0 mm over 0.3 mm + hemisphere d1.0 mm, h0.5 mm.)*

Read this honestly:

- **Both** shapes collapse to a point at the apex, so **both truncate** at the top to ~one extrusion width (~0.4 mm). The frustum does **not** eliminate the truncated top.
- The **pure cap's** steps are tiny at the base and **worst at the top** (0.136 mm then a collapse) — i.e., the roughness piles up exactly where the finger reads on a flat print.
- The **combined dot** spreads the change more evenly (uniform 0.083 mm frustum steps, a smooth mid-dome, then the same apex collapse). Subjectively smoother sidewall, same top.

So: the combined shape gives a **more uniform, better-controlled profile** and lets you **choose** the proportions, but it is a *redistribution*, not extra resolution. **Resolution comes from layer height, not profile.**

### 3c. The under-appreciated win: the frustum is built for the *vertical* orientation

This is where your "I may have accidentally solved it" instinct is most justified — just aimed at the other orientation. When the card is printed **near-vertical (75–90°)** — which is what the research says you *should* do — each dot sticks out sideways and its **underside is an overhang built over thin air for the first layers** (CHI's own observation [1]). Overhang severity by base shape:

- **Hemisphere base:** the underside meets the wall at a near-vertical tangent → effectively a ~90° overhang at the worst line → sagging, drooping, rough underside.
- **Tapered frustum base:** the underside is a **cone** at a fixed, gentle angle (e.g., 1.5 → 1.0 mm over 0.4 mm ≈ a ~32° rise) → a **moderate, self-supporting overhang** that FDM handles cleanly without supports.

In other words, the frustum base does for the dot exactly what choosing 75° does for the whole plate: **it converts a vicious overhang into a printable slope.** That is a real, support-free-friendly advantage and a strong reason to keep the shape **for the vertically-printed card** the plan recommends.

### 3d. "Sharp on top" — reframed

A pure sphere/dome that comes to a point is the thing makers complain about: `sav-iqbal/ML-OpenScad-Braille-Generator` moved from spheres to fillets because *"prints are too pointy with a sphere, as the printer places dots on top to complete the shape … leads to unwanted strings."* [9] But ADA/BANA actually want **rounded, not pointed** dots, and the CHI study used **truncated** tops on purpose. [1] The fix the field converged on is a **controlled flat/rounded top**, e.g. `BrailleMaker`'s cylinder + hemisphere-fillet with `dotHeight ≤ dotDia/2`. [10] Your frustum+cap is in the same family; you can deliberately give the cap a small flat or a shallow cap so the nozzle-limited top is **designed**, smooth, and comfortable instead of an accidental nub. Net: the combined shape **helps with "sharp top,"** but the credit is *controlled truncation*, not added height.

### 3e. Novelty, stated honestly

The "base + rounded cap" idea is **established prior art** (BrailleMaker cylinder+fillet [10]; the cone/truncated-cone dots in the companion web app; KitWallace/brailleSCAD lineages). What is reasonably **distinctive in your implementation** is the *fully parametric, independently-tunable* **taper** (`base_diameter → dome_diameter`) plus a **mathematically exact spherical cap** with separate dome diameter/height — i.e., you can dial the base footprint, the taper angle, the cap radius, and the total height independently. That is a better-engineered knob set than a fixed cylinder+hemisphere, and it is what makes 3a and 3c achievable. Call it a strong refinement, not a new principle.

---

## 4. Slicer techniques to improve dome quality on a 0.4 mm nozzle (ranked by payoff)

Ordered from highest to lowest impact for a home FDM printer. Items 1–4 are mainstream and well-proven; items 7–8 are the "recent/frontier" techniques you asked about.

### 1. Layer height — the #1 geometry lever (and variable/adaptive layer height)

- **Drop to 0.10 mm for the braille.** This is the strongest geometry fix and the universal recommendation. 0.1 mm is the practical floor — Prusa explicitly says going below 0.10 mm gives "relatively minor" quality gains for big time costs. Max layer height on a 0.4 mm nozzle is ~0.32 mm (≤80% of nozzle). [17] The braille calibration ecosystem (Katz Creates) ships at **0.10 mm layer / 0.40 mm nozzle.** [6]
- **Use Variable / Adaptive Layer Height instead of slowing the whole print.** This feature exists *specifically* to kill the "staircase feeling on spherical top surfaces and slopes": it auto-thins layers on curves and thickens them on vertical walls. On a 0.4 mm nozzle the usable range is **0.08–0.28 mm**. Use the **Adaptive** slider toward Quality, then **Smooth** (Gaussian filter) with **Keep Minimum** on. Available in PrusaSlicer, OrcaSlicer, Cura, Bambu/Anycubic. *Caveat: not compatible with organic/tree supports.* [16]
- **Height Range Modifier (the surgical version).** In PrusaSlicer/OrcaSlicer, right-click the model → **Height range modifier** → set the dot Z-band to **0.10 mm** and leave the card body at 0.20 mm. This is the exact trick the braille calibration models use (base 0.2 mm, braille 0.1 mm), giving fine dots without doubling whole-card print time. [6][17] **Watch top solid layers**: at 0.1 mm you need ~9 top layers to match the wall thickness 3 layers gave at 0.3 mm. [17]

### 2. Print orientation in the slicer (free, biggest *readability* win)

Even without redesigning the model, orienting the braille face at **75–90°** to the bed is the change with the largest proven effect on reading speed/comfort. [1] 75° keeps other raised features printable while keeping braille smooth. This is a slicer/placement decision as much as a design one — and it is the orientation your frustum base (Section 3c) is built for.

### 3. Perimeter/extrusion-width and small-feature speed

- **Set perimeter extrusion width to ~0.40 mm** (don't let it default wider) so a single clean perimeter defines the small dot wall. [6]
- **Slow "Small perimeters" to ~5 mm/s.** The dot walls are tiny loops; printing them slowly massively reduces ringing, blobs and seam nubs. [6]
- **Arachne perimeter generator (PrusaSlicer/Orca/Cura).** Arachne varies extrusion width to fill thin/variable regions a fixed-width generator would drop or pinch — useful for the narrowing cap and tiny gaps between dots. (Mainstream since PrusaSlicer 2.4 / Cura 5.) Pair with a small "minimum feature size."

### 4. Cooling, temperature, retraction (kills the nubs/strings)

- **Maximize part cooling** on the small layers; **print PLA on the cooler end** to freeze each tiny layer before the next lands. These are the same conditions that make overhangs behave. [13]
- **Tune retraction / temperature to stop stringing** between dots — stringing and the nubs it leaves are a primary source of felt roughness on flat dots; the 7B Industries label guide calls this out and recommends per-printer retraction/temperature tuning. [2]
- **Seam position**: park the perimeter seam on the back face (or "rear"), so the start/stop nub is not on the finger side.

### 5. Ironing — only for *flat-topped* dots (a real but narrow tool)

Ironing smooths a surface by re-running the nozzle with trickle flow — but **only on flat, horizontal, top-most surfaces.** On a curved dome it either **gouges or floats** ("nozzle drag marks across the dome"). So ironing is useless for a rounded apex, **but** if you adopt a **truncated/flat-topped** dot at a single uniform height (the CHI study's shape), "Iron topmost surface only" (PrusaSlicer/Orca) or "Iron only highest layer" (Cura) can polish all the dot tops at once. Use ironing flow ~10%, spacing ~0.1 mm, and note the small-part caveat (<20 mm parts iron unevenly; needs ≥3 top layers). This is a niche optimization, not a primary fix. [18]

### 6. Smaller nozzle — the XY-resolution lever (0.25 mm > 0.20 mm for this job)

Layer height fixes the **vertical** (Z) staircase; only a **smaller nozzle** improves the **in-plane (XY)** crispness of the dot footprint and the gaps between dots. Prusa's nozzle study recommends **0.25 mm** specifically for detailed text/business cards (and notes layer-height changes don't help text legibility — that's nozzle-bound). [12] A real parametric **braille business card with QR** on Cults ships a **0.2 mm-nozzle 3MF "for best detail / crisp dots"** plus a faster 0.4 mm version. [11] Trade-offs: 0.2 mm clogs easily (dry filament, slow), slower prints; **0.25 mm is the sweet spot** — meaningfully crisper dots without 0.2 mm's fragility. Rule of thumb: keep layer height **< half the nozzle diameter** (so a 0.25 mm nozzle wants ≤0.12 mm layers). [21] **You do not *need* a small nozzle** — Katz Creates' whole point is "great braille on a 0.4 mm nozzle" with the settings above [6] — but it is the next step up in dot fidelity.

### 7. Arc Overhangs / Wave Overhangs (recent, support-free overhangs — relevant to vertical dots)

A 2022→2025 line of work prints **90° overhangs with no supports** by laying down self-supporting concentric **arcs** (`stmcculloch/arc-overhang`), refined into smoother **Wave Overhangs** (a PrusaSlicer fork using wave-propagation tool-paths). Both are **purely planar** (work on a stock MK3/Voron, 0.4 mm nozzle) and want **cold + max cooling + ~5 mm/s.** [13][14] Relevance here: in the **vertical** orientation the dot underside is an overhang, so this is conceptually the right family of tool — **but braille dots are ~1.5 mm**, below the scale these arc-fill algorithms target, so in practice the **tapered frustum base (Section 3c) is the more reliable answer** to the same overhang problem. Worth tracking as these land natively in slicers.

### 8. Non-planar / conical slicing (frontier, mostly not home-ready)

Non-planar and **conical/inclined** slicing let tool-paths follow the model surface instead of flat layers, which can lay smooth, conformal passes over a dome (no Z-staircase at all) and print steep overhangs. Mixed/hybrid slicing (planar body + non-planar caps) is the realistic form. [15] **Reality check:** requires special slicers (e.g., conical-slicing forks), nozzle-clearance/collision constraints, and tuning; **not practical for a parametric home-printable card today.** Note it as a future direction, not a current recommendation.

### Post-processing (the consensus fallback)

Across the literature and tools, **light sanding of the dot tops** (dot-side-down on fine grit) is the accepted way to remove residual nubs/strings on flat-printed dots; the CHI study even ran a separate **sanded** experiment because straight-off-the-printer dots could be sharp enough to be uncomfortable. [1][2][7] If you print near-vertical, you largely avoid needing this.

---

## 5. Synthesis: two recommended recipes

**Recipe A — Best quality (the card's default): near-vertical + frustum dot**

- Orientation **75–90°** (face vertical; 75° if other raised features need overhang relief). [1]
- Dot = your **combined frustum + spherical-cap**, base 1.5 mm, total height ≤0.9 mm, with the **taper doing the overhang-softening** on the dot underside. [3c]
- Layer height **0.10 mm** for the braille (Adaptive/Height-Range modifier so the body stays 0.2 mm). [16][17]
- Small-perimeter speed ~5 mm/s, perimeter width ~0.40 mm, max cooling, seam to back. [6]
- Supports: aim **support-free** via an integrated foot/brim (the plan's approach) — the frustum underside is self-supporting at this scale.
- Optional: **0.25 mm nozzle** for crisper dots. [12]

**Recipe B — Fast/flat mode (fallback): flat + controlled truncated dome**

- Orientation **flat (0°)**, dots +Z.
- Dot = frustum + a **deliberately truncated (small-flat) cap** so the top is a designed flat, not an accidental nub; use the full 0.9 mm legal height (Section 3a) for max layers.
- Layer height **0.10 mm** on the dots via Height-Range modifier; **ironing "topmost surface only"** can polish the flat tops (all dots same height). [18]
- Expect to **light-sand** the tops for comfort. [1][2]
- Quality is inherently below Recipe A — this is the "it printed fast" mode, consistent with the plan's `print_orientation` parameter.

---

## 6. Concrete suggestions for this repo's parameters

Tie-ins to the existing `Rounded`-dot knobs (`Braille_Cylinder_STL_Generator.scad`), should the card reuse them:

- **Cap the legal height for signage/card presets:** enforce `rounded_dot_base_height + rounded_dot_dome_height ≤ 0.9`. The current default sums to **1.0 mm** (0.5 + 0.5), which is over the ADA/BANA max for signage. A card preset of **base 0.4 + dome 0.5** (= 0.9 mm, true hemisphere cap on a 1.0 mm dome dia) or **base 0.3 + dome 0.45** keeps it legal while still exploiting the frustum to exceed the 0.75 mm pure-dome ceiling.
- **Keep base ≈ 1.5 mm, dome dia ≈ 1.0 mm** (the current default taper) — it gives a ~32° underside cone, which is the overhang-friendly value for vertical printing.
- **Expose taper angle as the design intent.** Today the taper is implied by `base_diameter` vs `dome_diameter`. For the card it may read better to document/derive it as an explicit "base overhang angle" so users tune the *printability* knob directly.
- **`cone_segments` / `render_quality`:** the dome is a sphere primitive gated by `quality_fn`; for tiny dots the mesh facets can rival the layer steps. Use **High** for final card STLs so mesh faceting isn't the limiting factor (it's cheap at this size).
- **A `print_orientation` parameter** (plan item) should carry **recipe presets**, not just rotate geometry: Vertical→Recipe A defaults, Flat→Recipe B (truncated cap, ironable).
- **Validation hook:** the `tests/` harness already does cross-platform STL/mesh comparison — extend it to assert dot **total height ≤ 0.9 mm** and base **diameter within 1.5–1.6 mm** for card presets.

---

## 7. Honest limitations / what to confirm empirically

This report is a *desk* synthesis. Before claiming the combined dot "solves" anything, validate with prints, because the literature is consistent on one point: **FDM braille is judged by fingers, not calipers, and small features under-build unpredictably** [3].

- **The claim to test:** does the frustum+dome, printed **flat** at 0.1 mm, actually feel smoother than a pure truncated dome at the same height? (Section 3b predicts: *a little*, mostly even sidewalls; same top.) And does it feel better than the same dot printed **vertical**? (Prediction from [1]: vertical wins regardless of profile.)
- **Print the matrix:** {pure truncated dome, frustum+dome} × {0°, 75°, 90°} × {0.10, 0.15 mm layer} × {0.4, 0.25 mm nozzle}. Use the **Katz Creates calibration model** as a ready-made harness. [6]
- **Get the CHI study's exact print settings** from its OSF supplement (`osf.io/t2rbq`) — the paper text omits the layer height; practitioner consensus and the calibration models point to **0.1 mm**, but confirm rather than assume. [1]
- **Recruit braille readers** for any real quality claim — sighted "looks smooth" ≠ "reads fast/comfortably." The CHI study measured reading speed + Likert comfort for exactly this reason. [1]
- **Measure, don't assume, the achieved geometry** (microscope/profilometer): expect height/diameter to come in **under** nominal [3], which is *another* argument for using the frustum to bank extra height.

---

## 8. Sources

1. Puerta, Crnovrsanin, South, Dunne — **"The Effect of Orientation on the Readability and Comfort of 3D-Printed Braille,"** CHI 2024. DOI [10.1145/3613904.3642719](https://doi.org/10.1145/3613904.3642719) · mirror [vis.khoury.northeastern.edu](https://vis.khoury.northeastern.edu/pubs/Puerta2024EffectOrientationReadability/) · supplement [osf.io/t2rbq](https://osf.io/t2rbq/) · preprint [osf.io/preprints/osf/vbqsg](https://osf.io/preprints/osf/vbqsg).
2. 7B Industries — **Braille Label Generator documentation** (FDM print guidance: lowest layer height, dots-up, retraction/temperature for stringing, sand tops). [7bindustries.com](https://www.7bindustries.com/docs/braille_label_generator/index.html)
3. **"Quality Assessment of Braille Dots Printed by FDM,"** Advances in Science and Technology Research Journal (designed 0.5 mm/1.3 mm → measured 0.38 mm/1.0 mm; under-build). [astrj.com](https://www.astrj.com/Quality-Assessment-of-Braille-Dots-Printed-by-Fused-Deposition-Modeling-3D-Printing,191928,0,2.html)
4. **"Geometrical evaluation of additive manufacturing techniques for tactile graphic production"** (FDM poor for small features like braille dots/rounded corners; SLA best, SLS rough). [discovery.researcher.life](https://discovery.researcher.life/article/geometrical-evaluation-of-additive-manufacturing-techniques-for-tactile-graphic-production/64965a16e8553ac2b1cd2e8505dad71d)
5. Barros, Correia, Teixeira — **"Towards the Effectiveness of 3D Printing on Tactile Content Creation,"** Polymers 2023, 15(9):2180 (Prusa MK3S, 0.4 mm nozzle, PLA, 0.1 mm layers). DOI [10.3390/polym15092180](https://doi.org/10.3390/polym15092180) · [PMC10181369](https://pmc.ncbi.nlm.nih.gov/articles/PMC10181369/)
6. Katz Creates — **3D Printed Braille Test Calibration Print** (0.10 mm layer / 0.40 mm nozzle; variable layer height base 0.2/braille 0.1; small-perimeter 5 mm/s; perimeter width 0.4; ≥6 mm exclusion zone) + companion YouTube "How To Make Fast and Easy 3D Printed Braille." [printables.com/model/109513](https://www.printables.com/model/109513-3d-printed-braille-test-calibration-print) · [youtube.com/watch?v=og6wzidwaho](https://www.youtube.com/watch?v=og6wzidwaho)
7. **tactiles.eu — Guideline 4.4 Surfaces and textures** (vertical printing avoids sharp peaks; head "pulls through in one go"; max edge rounding; horizontal needs larger dia + sanding). [tactiles.eu](https://tactiles.eu/guideline/3-2-surfaces-and-textures/)
8. **Hackaday.io — "3D printing Braille"** (Whosawhatsis; blind-reader survey: side-printed dots smoother + more durable; dots must be domed not cylindrical). [hackaday.io](https://hackaday.io/project/11312-3d-prints-for-teachers-of-the-visually-impaired/log/43785-3d-printing-braille)
9. **sav-iqbal/ML-OpenScad-Braille-Generator** (switched spheres→fillet: spheres "too pointy… unwanted strings"). [github.com/sav-iqbal/ML-OpenScad-Braille-Generator](https://github.com/sav-iqbal/ML-OpenScad-Braille-Generator)
10. **crowellhouse/BrailleMaker** (Fusion 360: cylinder + hemisphere fillet, rule `dotHeight ≤ dotDia/2`; defaults dia 1.6 / height 0.8 = hemisphere). [github.com/crowellhouse/BrailleMaker](https://github.com/crowellhouse/BrailleMaker)
11. **Accessible Braille Business Card with QR Code — parametric OpenSCAD** (ships 0.2 mm-nozzle 3MF "best detail / crisp dots" + faster 0.4 mm version). [cults3d.com](https://cults3d.com/en/3d-model/home/accessible-braille-business-card-with-qr-code-fully-parametric-openscad-design)
12. **Prusa — "Everything about nozzles with a different diameter"** (0.25 mm recommended for detailed text/business cards; layer height doesn't fix text legibility — nozzle does). [blog.prusa3d.com](https://blog.prusa3d.com/everything-about-nozzles-with-a-different-diameter_8344/)
13. **stmcculloch/arc-overhang** (support-free 90° overhangs via concentric arcs; planar; cold/slow/max-cooling; 0.4 mm nozzle). [github.com/stmcculloch/arc-overhang](https://github.com/stmcculloch/arc-overhang)
14. **stmcculloch/PrusaSlicer-WaveOverhangs** (wave-propagation refinement of arc overhangs; PrusaSlicer fork). [github.com/stmcculloch/PrusaSlicer-WaveOverhangs](https://github.com/stmcculloch/PrusaSlicer-WaveOverhangs)
15. **"3D Printing 90° Overhangs: Non-Planar Slicing"** (conical/inclined + hybrid planar/non-planar; collision/clearance caveats). [gearxtop.com](https://gearxtop.com/3d-printing-90-overhangs-with-non-planar-slicing/)
16. **Variable / Adaptive Layer Height** — fixes "staircase feeling" on spherical/sloped tops; 0.4 mm nozzle range 0.08–0.28 mm; Adaptive + Smooth (Gaussian) + Keep Minimum; not with tree supports. [OrcaSlicer wiki](https://github.com/OrcaSlicer/OrcaSlicer/wiki/prepare_variable_layer_height) · [Prusa KB](https://help.prusa3d.com/article/variable-layer-height-function_1750) · [Obico guide](https://www.obico.io/blog/orca-slicer-adaptive-and-variable-layer-height-guide-smoother-3d-prints/) · [Anycubic wiki](https://wiki.anycubic.com/en/software-and-app/new-page-anycubic-slicer-beta(orca-version)/variable-layer-height)
17. **Prusa KB — Layers and perimeters** (layer height ≤80% nozzle; ~9 top layers at 0.1 mm; Height Range Modifier; first layer 0.2 mm). [help.prusa3d.com](https://help.prusa3d.com/article/layers-and-perimeters_1748) · Height-Range-Modifier how-to: [Prusa forum](https://forum.prusa3d.com/forum/prusaslicer/changing-layer-height-mid-print/)
18. **"Ironing and Top Surface Finish" (2026 guide)** (ironing flat tops only; gouges/floats on domes; topmost-surface-only; <20 mm + ≥3 top-layer caveats). [blog.uavmodel.com](https://blog.uavmodel.com/ironing-and-top-surface-finish-settings-flow-rate-and-when-it-actually-works-2026-guide/)
19. **BelfrySCAD/brailleSCAD** & **KitWallace braille.scad** (OpenSCAD dot/translation lineages referenced by the plan and adapted by the CHI study). [github.com/BelfrySCAD/brailleSCAD](https://github.com/BelfrySCAD/brailleSCAD)
20. **ADA 703.3 / BANA size & spacing** (domed dots; base 1.5–1.6 mm, height 0.6–0.9 mm). [corada.com ADA 703.3](https://www.corada.com/documents/2010ADAStandards/703-3) · [brailleauthority.org](https://brailleauthority.org/size-and-spacing-braille-characters)
21. **3D Printing StackExchange — "What are the smaller nozzles for?"** (layer height < ½ nozzle diameter; small nozzles for fine/embossed detail). [3dprinting.stackexchange.com](https://3dprinting.stackexchange.com/questions/24447/what-are-the-smaller-nozzles-for)

---

*Prepared as additional research for the Braille Business Card proposal. No production code was changed. Recommendation: fold Sections 5–6 into `02-design-proposal.md` (dot/slicer design rules) and cite Sections 1–4 from `01-research-synthesis.md`.*
