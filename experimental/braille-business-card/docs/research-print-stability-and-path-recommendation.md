# Research + Recommendation: Print Stability for Near-Vertical Braille (Curved Card vs. Wedge Easel)

Status: research / docs-only. No `.scad` changes. Companion to `research-dot-geometry-and-slicer-quality.md` and the `braille-business-card` plan.

The problem you raised: printing a thin (~2 mm) card on edge / near-vertical is **mechanically fragile** — it's whippy, sensitive to vibration, and a single mis-registered layer telegraphs upward into every dot above it. Thicker cards cost filament and time. You proposed two structural workarounds (Path 1: a gently-curved card that flattens via living hinges; Path 2: a self-supporting hollow wedge/easel). This report researches the prior art for both and recommends a path.

---

## TL;DR / Recommendation

- **Your root-cause diagnosis is correct and well-documented.** Tall, thin, vertical walls are the textbook worst case for *ringing/ghosting* and resonance: "a small amount of vibration that's fine on a 60 mm cube turns into obvious ripples on a 400 mm wall," and it "reintroduces ringing halfway up a tall wall." [1][2][5]
- **Before either geometry, the cheapest, highest-leverage fixes are firmware/slicer, not CAD:** **input shaping / resonance compensation** (Klipper, or Marlin `M593`), **slow outer-wall speed (30–40 mm/s)**, **lower acceleration (500–1500 mm/s²)**, tight belts, a **wide brim / anti-tip base**, and a stable bench. These alone often make a near-vertical print acceptable. [1][2][4][5]
- **Recommended primary path: Path 2 (the buttressed hollow wedge / easel).** It is **proven, low-risk, and support-free** — angled business-card *stands* are one of the most common print-without-supports models on Printables/Cults, including ones that lean cards at ~70°. [9][10] It **solves your vibration problem structurally** (triangular gussets + a wide base convert a whippy 2 mm sheet into a braced wedge), it **lands the braille at the research-optimal 75° automatically**, it pairs perfectly with the frustum-base dot from the other report, and it doubles as a desk display stand. It is essentially the plan's "candidate C (75° wedge)" made rigid.
- **Path 1 (curved card) is genuinely clever and half-right, but the flattening mechanism is the weak link.** The **curvature-for-stiffness** intuition is real engineering: curving a thin sheet into an arch can raise its bending stiffness **5×+** vs. a flat plate. [6] And the existing cylinder code already lays braille out by **arc length**, so a flattened arc would actually recover correct ADA spacing. **But the living-hinge step fights two hard facts:** (a) **PLA living hinges are brittle — typically 10–30 flex cycles before cracking** [11][12][13]; and (b) printed *standing* (the orientation that gives you the stiffness + good braille), the hinge grooves run **parallel to the build (Z) axis**, so flattening bends them **across the layer lines — the delamination-prone direction.** Living hinges are supposed to flex *parallel* to layers and be printed flat. [13][14] So Path 1 as drawn (PLA, print-standing, flatten-flat) will likely crack or not stay flat.
- **If you love Path 1, the salvageable version is a *permanently* gently-curved card (large radius, no hinge at all)** — read on the gentle curve (acceptable for gentle curvature [15]), keep the print-stiffness and smooth-toolpath benefits, and skip the fragile hinge. A truly flattening card needs a **material change** (PETG/TPU hinge or multi-material) or a **kerf-bend pattern**, both of which are real but are an R&D branch, not the fast path. [16][17]

**One-line answer:** do the firmware/slicer fixes regardless, ship **Path 2 (wedge easel)** as the stabilizer, and keep Path 1 as an experimental "curved card" branch — ideally as a *permanently curved* card rather than a flatten-flat living-hinge card.

---

## 1. The root problem, and the fixes that may dissolve it (do these first)

What you're seeing — a slightly-off layer that "impacts the entire rest of the print upward" — is the classic signature of **resonance / ringing (ghosting)** amplified by a tall, thin, low-mass geometry. The literature is unambiguous that this is primarily a **motion/mechanics** problem, and that geometry makes it *worse* but is rarely the cheapest place to fix it:

- **Input shaping / resonance compensation is the single biggest lever.** It cancels the vibration in the motion profile itself rather than just slowing down. Available as Klipper Input Shaping (calibrate with an ADXL345 accelerometer) or Marlin `M593` (Fixed-Time Motion). "The single biggest investment in print quality you can make." [1][5]
- **Slow the outer wall and drop acceleration.** Outer-wall **30–40 mm/s**, acceleration **500–1500 mm/s²**, and keep `square_corner_velocity`/jerk modest. You only need to slow the *visible* perimeters, not infill. [1][4]
- **Mechanics first.** Tighten belts to a "firm thud," check eccentric nuts/frame, and put the printer on a heavy/stable surface or anti-vibration pads. Input shaping "only works well when your mechanics are tight." [1][2]
- **Stabilize the base of the print.** A **brim / wide foot / anti-tip base** and a draft-shield-style buttress dramatically reduce the whippiness of a tall thin part. (This is exactly what Path 2 bakes into the model.)

> Implication: a near-vertical card with a **wide foot + brim + input shaping + slow outer walls** may already print cleanly. Treat the geometry paths below as *insurance and ergonomics* on top of these, not as a substitute for them.

The reason near-vertical is worth all this trouble (rather than just printing flat) is the readability result the whole project is built on: readers were significantly faster and more comfortable with braille at **75°–90°** than flat, because the layer seams move off the finger-contact surface. So the goal is "print near-vertical **without** the fragility," which is precisely what both of your paths attack.

---

## 2. How I read your two designs (and one thing to confirm)

### Path 1 — gently-curved card with living-hinge "flats"
A shallow segment of a **very large-diameter cylinder** (gentle convex curve), reusing the cylinder generator. The existing **polygon cutout** is repurposed so its facet count matches the number of braille **columns**, and the inner profile is scalloped so material is **thick (2–3 mm) behind each braille column** and **thin (0.5–1 mm) in the gaps between columns**. Those thin gaps act as **living hinges**: after printing, you press the card onto a flat surface and the thin lines comply/bend so the curved card lies flat, recovering a "flat card."

### Path 2 — self-supporting hollow wedge / easel
A card whose braille face is tilted back to **75°**, fused into a self-supporting wedge:
- a **base rectangle** (≈2–3 mm thick) running the full width along the desk;
- **triangular side walls** (gussets) on the left and right that rise from the base to the top of the card, vertical at the back, following the lean at the front;
- a **vertical back** (a hollowed-out rectangular frame in the Z–X plane);
- the **braille on the front angled face**, dots pointing up-and-out.
Net shape: a **hollow wedge** (thin shell + ribs), so it's rigid but light. It also stands on a desk as a display.

```text
PATH 2 — side cross-section (as it sits on the desk = as it prints)

        front (braille) face leans back 15° from vertical (= 75° from desk)
                 ↘
                  ●●  ← dots point up-and-out (CHI 75° regime)
                  ●●
       vertical    \●●
       back wall →  |  \
       (90°)        |    \
                    |______\____  ← base foot (full width) + brim
                    └ hollow interior, triangular side gussets tie face→base
```

> **One ambiguity to confirm.** You wrote "angled at 75 degrees from the vertical surface." Taken literally that's 75° *off vertical* (≈15° above the desk — almost lying down), which would contradict the project's 75°-**from-horizontal** finding. Given the rest of your description (vertical back, braille on the leaning front), I've assumed you mean the **CHI convention: braille face at 75° from the print bed / desk = 15° lean back from vertical.** If you actually meant a shallower 15°-from-desk display angle, the analysis changes — flag it and I'll redo the geometry. (A confirm question is at the end.)

---

## 3. Path 1 (curved card + living hinge): what's right, what's risky

### 3a. What's genuinely right
- **Curvature really does add stiffness.** Turning a flat sheet into a shallow arch raises its second moment of area; structural studies find a curved panel can be **>5× stiffer than the equivalent flat plate**, because the curvature carries load as an arch. [6] So a gently-curved card resists the out-of-plane whip that plagues a flat 2 mm sheet — your core intuition is sound.
- **Smoother tool-paths, fewer hard reversals.** A flat vertical wall makes the head decelerate/reverse at the same X/Y extremes every layer (and stack the seam in one place). A gentle arc lets the head sweep through a continuous curve, which reduces the sharp direction-changes that *excite* ringing and lets you stagger the seam. Real, if secondary, benefit.
- **The code already lays out braille by arc length.** Spacing is computed angularly (`grid_angle = grid_width / radius`, `cell_spacing_angle`, `dot_spacing_angle`), so dots sit at the correct **arc-length** spacing. That means if the card is later flattened, the spacing **relaxes to the correct flat ADA spacing** — curvature doesn't corrupt the standard, which is a real point in Path 1's favor.

```288:295:Braille_Cylinder_STL_Generator.scad
radius                = active_cylinder_diameter_mm / 2;
grid_angle            = grid_width / radius;
start_angle           = -grid_angle / 2;
cell_spacing_angle    = active_cell_spacing / radius;
dot_spacing_angle     = active_dot_spacing / radius;
dot_col_angle_offsets = [-dot_spacing_angle / 2, dot_spacing_angle / 2];
dot_row_offsets       = [active_dot_spacing, 0, -active_dot_spacing];
dot_positions         = [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]];
```

### 3b. The crux risk: the living hinge (material + orientation)
This is where Path 1 gets hard, and it's two compounding problems:

1. **PLA living hinges are brittle.** Across every design guide, PLA hinges fail in **~10–30 flex cycles** ("like dry spaghetti"); the FDM sweet spot is 0.4–0.6 mm thick, PETG gets 50–100+ cycles, and only **TPU / Nylon / polypropylene** reach hundreds–thousands. [11][12][13] A business card that must be pressed flat (and survive handling) in PLA will likely **crack along the grooves**.
2. **Orientation conflict (the deeper problem).** To get the stiffness + good braille you print the curved card **standing up** (like the cylinder), so layer lines are horizontal and the hinge grooves run **vertically, parallel to the build axis.** Flattening then bends the card about those vertical lines — i.e., it loads the hinge **across the layer lines**, which is exactly the **delamination-prone** direction. Every guide says the opposite: living/compliant hinges should **flex parallel to the layers and be printed flat.** [13][14] So the one orientation that makes Path 1 worth doing is the worst orientation for its hinge.
3. **Elastic vs. plastic dilemma.** If the hinge is stiff enough to *stay* flat, you've plastically deformed PLA (it cracks); if it's compliant enough to bend easily, it **springs back** to curved when released — so it won't sit flat in a wallet anyway.

### 3c. Reading braille on a curve (if you *don't* flatten)
Makers who put braille on cylinders report it's fine **only when the curve is gentle**: "if the surface is gently curved then it should be acceptable, BUT projecting onto a [tight] cylinder gives distorted start/end spacings." [15] Your "much larger theoretical diameter" instinct is the right mitigation. Finger reading also relies on smooth gliding and frequent right-to-left **re-reading/reversals**, so consistent spacing and a snag-free surface matter more than flatness per se. [18] Conclusion: a **large-radius, permanently-curved** card is plausibly readable *without* flattening.

### 3d. Safer Path-1 variants (in increasing effort)
- **(A) Permanent gentle curve, no hinge.** Pick a large radius, print standing, read on the curve. Keeps the stiffness + toolpath benefits, drops the fragile hinge entirely. Lowest risk; the card just isn't perfectly wallet-flat.
- **(B) Material/multi-material hinge.** Print the panels rigid and the hinge lines in **PETG/TPU** (or co-print), so it can actually flex-flat repeatedly. Adds material/printer complexity.
- **(C) Kerf-bend pattern instead of single grooves.** 3D-printed **kerf structures** can make even rigid PLA bend into curved/flat geometries by distributing the bend across many small cuts; flexibility is tuned by cell density/spacing. But PLA kerf tends to **"bend-lock"** and is still fatigue-limited, and it complicates the back face. [16][17] An R&D path, not a quick win.
- **(D) Reorient for the hinge.** Print so the grooves flex *parallel* to layers — but that generally means printing flatter, which sacrifices the braille-quality reason for going vertical. Usually self-defeating here.

### 3e. Code reality for Path 1
The current cutout is a **single regular N-gon** subtracted from the shell:

```535:548:Braille_Cylinder_STL_Generator.scad
module cylinder_shell(cutout_rotate_deg = 0) {
    difference() {
        // Outer cylinder (see $fn TESSELLATION POLICY: case 1)
        cylinder(h = active_cylinder_height_mm, r = active_cylinder_diameter_mm / 2, center = true, $fn = CYLINDER_SHELL_FN);

        // Polygonal cutout if specified
        if (active_polygon_cutout_radius_mm > 0) {
            // Web UI: "Circumscribed Radius" but implementation uses inscribed radius
            cutout_circumradius = active_polygon_cutout_radius_mm / cos(180 / active_polygon_cutout_points);
            rotate([0, 0, cutout_rotate_deg])
                cylinder(h = active_cylinder_height_mm + 2, r = cutout_circumradius, $fn = active_polygon_cutout_points, center = true);
        }
    }
}
```

A regular N-gon gives **uniform** wall thickness oscillation, not "thick exactly behind each column, thin in each gap." To get your scalloped/corrugated inner wall you'd replace this with a **custom `polygon()` whose radius oscillates with angle** (peaks aligned to column centers, troughs in the gaps) and phase-lock it to `start_angle`/`cell_spacing_angle`. That's a new, moderate module — not just bumping `polygon_cutout_points`. Feasible, but it confirms Path 1 is **new code + new risk**, not a free reuse.

---

## 4. Path 2 (hollow wedge / easel): what the prior art says

### 4a. It's a solved, popular pattern
Angled business-card **stands/holders** are among the most common "prints without supports" on Printables/Cults/Thangs, which validates both the geometry and the printability:
- A "Business Card Stand — Angled Desk Display" leans cards at **~70°** with a **back rest + front lip + broad anti-tip base**, explicitly "designed to print flat **without supports**," PLA/PETG, 0.4 mm nozzle, 0.2 mm layers, 15% infill. [10]
- A 45° card holder prints support-free on a budget Ender 3 ("if your printer can handle 45° overhangs… no supports"), 2 perimeters, 20% infill, 1 mm solid bottom. [9b]
- Print-in-place card cases/stands exist in PETG. [9c]

Your wedge is the same family, with the braille *on* the angled face instead of a loose card resting against it.

### 4b. It directly fixes the vibration problem (structurally)
A bare 2 mm card on edge is a cantilevered thin plate — maximally whippy. Your wedge adds:
- **A wide base footprint** (the foot runs the full card width, and the lean creates depth) → low, stable, hard to tip, easy to brim.
- **Two triangular side gussets** → a triangle is the canonical stiffening rib; tying the leaning face to the base kills the out-of-plane wobble that telegraphs into the dots.
- **A vertical back wall** → a second web bracing the structure.
This is the same "turn a floppy sheet into a braced 3D shell" principle as Path 1's curvature, but achieved with **ribs/walls** instead of an arch — and **without** a fragile hinge or a curved reading surface. It is the more direct answer to "make near-vertical printing not fragile."

### 4c. It's automatically at the research-optimal angle, and pairs with the frustum dot
Printed sitting on its base (the natural orientation), the braille face is at **75° from the bed** — the CHI sweet spot that also "minimizes sloped overhangs" vs. 90°. The face is a **mild ~15°-from-vertical overhang**, well within support-free capability, and the dot undersides are exactly the gentle overhangs the **tapered-frustum dot** (other report) is good at. The vertical back wall and side gussets are plain vertical walls — easy prints.

### 4d. Material savings (your hollow concern)
The hollow wedge + ribs is the right way to keep filament/time down while staying rigid: a thin shell (2 perimeters) with **triangular gussets** beats solid infill for stiffness-per-gram. If you want extra rigidity cheaply, a low **gyroid/cubic infill** or a couple of internal ribs adds a lot of stiffness for little mass. Comparable models print in ~50–60 g / ~4 h. [10]

### 4e. Minor risks / things to design for
- **Tip-over while printing/handling** → make the base depth ≥ ~25–30% of card height and add a brim; an anti-tip lip helps.
- **The leaning face is a (mild) overhang** → keep it at **75°, not 90°**, run good cooling, and use the frustum dots; this is why 75° (not vertical) is the better target.
- **Seam placement** → hide the perimeter seam on the back wall, off the finger-read face.
- **It's bulkier than a wallet card** → it's a *stand*, not a pocket card. If you need a pocket-flat card too, that's where a (separate) flat/fast-mode card or Path 1's permanent-curve variant comes in.

---

## 5. Head-to-head

| Criterion | Path 1: curved + living hinge | Path 1A: permanent gentle curve | Path 2: hollow wedge/easel |
|---|---|---|---|
| Fixes vibration/whip | Yes (arch stiffness) | Yes (arch stiffness) | **Yes (ribs + wide base)** |
| Print without supports | Yes (standing) | Yes (standing) | **Yes (proven prior art)** |
| Braille at 75–90° | On the curve (varies across width) | On the curve | **Uniform 75°** |
| ADA spacing correct | Only if flattened (arc-length) | Approx on gentle curve | **Yes (flat face)** |
| Lies flat for wallet | Intended, but **fragile in PLA** | No (stays curved) | No (it's a stand) |
| Material risk | **High (PLA hinge 10–30 cyc; cross-layer bend)** | Low | **Low** |
| New code needed | Custom variable-radius polygon + hinge | Curved-shell variant | New wedge module (straightforward) |
| Prior-art support | Thin (novel combo) | Some (curved braille labels) | **Strong (many card stands)** |
| Doubles as | — | — | **Desk display stand** |

---

## 6. Recommendation and phased next steps

1. **Table stakes (do regardless of path):** enable input shaping / `M593`, set outer-wall 30–40 mm/s, accel 500–1500, tighten belts, and add a brim/wide foot. Re-test a plain near-vertical card first — this may be "enough." [1][4][5]
2. **Primary build — Path 2 wedge easel.** Prototype a hollow 75° wedge: full-width base foot (2–3 mm), two triangular side gussets, vertical hollow back, braille on the front face using the frustum-base dots and a 0.1 mm braille layer height. This realizes the plan's "candidate C" as a *rigid, support-free, display-capable* card. Reuse the dot math + angular spacing; the wedge frame is new but simple geometry.
3. **Experimental branch — Path 1 as a *permanent gentle curve* (Variant A).** If a near-flat pocket form is wanted, try a large-radius curved card with **no hinge**, read on the curve; validate legibility with a braille reader. Only escalate to a flatten-flat hinge if you move to **PETG/TPU/multi-material or a kerf pattern** — treat that as a separate experiment with its own fatigue testing.
4. **Validate** with the `tests/` harness for geometry (dot height/spacing) and with **real finger testing** for comfort; the readability claims are tactile, not visual.

This keeps you shipping on the low-risk, well-supported path while preserving your curved-card idea as a focused experiment rather than a blocker.

---

## 7. Sources

1. **3D Printing Ghosting (Ringing): Causes, Fixes & Input Shaping (2026)** — input shaping cancels resonance; accel 500–1500, tighten belts, anti-vibration pads, slow outer walls. [3dtechvalley.com](https://www.3dtechvalley.com/ringing-3d-printing/)
2. **Sovol — Active Vibration Compensation for Large-Scale/Tall Prints** ("fine on a 60 mm cube → ripples on a 400 mm wall"; input shaping needs tight mechanics). [sovol3d.com](https://www.sovol3d.com/blogs/news/active-vibration-compensation-for-large-scale-prints-input-shaping-3d-printer-workflow)
3. **goodprints3d — Fix Ringing/Ghosting Without Slowing Everything** (tall narrow parts exaggerate vibration; treat as geometry-specific; reorient/support). [goodprints3d.com](https://www.goodprints3d.com/blogs/3d/how-to-fix-ringing-and-ghosting-in-3d-prints-without-slowing-every-job-to-a-crawl)
4. **FixMyPrint — Ringing & Ghosting** (outer wall 30–40 mm/s; accel 500–1000; calibrate input shaping). [fixmyprint3d.com](https://www.fixmyprint3d.com/guides/ringing-ghosting)
5. **Klipper — Resonance Compensation** (input shaping technique, ADXL345 calibration, square_corner_velocity caveat). [klipper3d.org](https://www.klipper3d.org/Resonance_Compensation.html)
6. **"Curvature increases bending stiffness"** — curved stiffened panel >5× stiffer than a flat plate; curvature acts as an arch (raises second moment of area). [hal.science PDF](https://hal.science/hal-01073382v1/file/doc00019587.pdf) · curved-crease corrugation stiffness redistribution [Woodruff & Filipov 2020](https://drsl.engin.umich.edu/wp-content/uploads/sites/414/2020/06/WoodruffAndFilipov_2020_CurvedCreasesRedistributeGlobalBendingStiffness.pdf)
7. **"Arch effect" of curved/corrugated sheets** (curvature transforms sheet into arch; global load capacity up despite local losses). [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0263823118305615)
8. *(reserved)*
9. **Business Card Holder 45° (Chris Aero)** — support-free if printer handles 45°; "Ensure vertical shell thickness." [printables.com/model/557413](https://www.printables.com/model/557413-business-card-holder) · 9b same · Card Case/Stand print-in-place PETG [printables.com/model/367406](https://www.printables.com/model/367406-business-card-case-holder-stand-credit-card-too-pr) (9c)
10. **Business Card Stand — Angled Desk Display (~70° lean, anti-tip base, no supports)** — PLA/PETG, 0.4 mm, 0.2 mm, 15% infill, ~57 g / ~4 h. [cults3d.com](https://cults3d.com/en/3d-model/tool/business-card-stand-angled-desk-display-holder-for-89mm-cards-with-front-lip) · also "Card Display" vertical/horizontal stand, no supports [thangs.com](https://thangs.com/designer/3DPrinty/3d-model/Card%20Display-1027048)
11. **Protolabs/Hubs — Designing living hinges for 3D printing** (FDM hinges are prototyping-grade; FDM 0.4–0.6 mm; recommended material Nylon 12; example achieved ~25 cycles). [hubs.com](https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/)
12. **Mandarin3D — Living Hinges for Flexible 3D Prints** (PLA <30 cycles; PETG 50–100+ at 0.5 mm; TPU 500–1000; 0.4–0.6 mm sweet spot; radii at transitions). [mandarin3d.com](https://mandarin3d.com/blog/designing-living-hinges-for-flexible-3d-prints)
13. **EliteMoldTech — 3D Printed Living Hinge Design Guide** (PLA snaps in 10–20 cycles; print flat in XY to tame layer lines; thickness 0.4–0.6 mm, length 8–12× thickness; PP is king). [elitemoldtech.com](https://elitemoldtech.com/3d-printed-living-hinge-design-guide/)
14. **Makelab — Snap-fit & living hinge design** ("flex parallel to layers, not across them — across-layer flex causes delamination"; PLA "too brittle"). [help.makelab.com](https://help.makelab.com/help/article/snap-fit-and-living-hinge-design-for-3d-printing)
15. **SketchUcation — braille dots on curved surfaces** ("if gently curved it should be acceptable; tight cylinders distort spacing; split text"). [community.sketchucation.com](https://community.sketchucation.com/topic/143237/is-it-possible-to-create-3d-braille-dots-on-any-surface) · companion project's [CYLINDER_GUIDE.md](https://github.com/BrennenJohnston/braille-card-and-cylinder-stl-generator/blob/main/docs/guides/CYLINDER_GUIDE.md) (print standing; polygon inner faces).
16. **Hackaday — Living Hinge / kerf bending in 3D printing** (cut patterns let rigid sheets bend; gaps/scale/thickness control flex; tiny gaps bridge). [hackaday.com/tag/living-hinge](https://hackaday.com/tag/living-hinge/)
17. **Additively manufactured kerf structures (Int. J. Solids Struct. 2025)** (PLA/TPU/Onyx kerf; PLA = high load-bearing + **bend-locking**; TPU = flexible/low load). [colab.ws](https://colab.ws/articles/10.1016%2Fj.ijsolstr.2025.113331) · FDM kerf overview [NSF PAR](https://par.nsf.gov/servlets/purl/10438996)
18. **Braille reading finger motion** (gliding + frequent right-to-left reversals/re-reading are core to reading; spacing consistency matters). [PLOS One](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0148356)

---

*Prepared as additional research for the Braille Business Card proposal. No production code changed. Folds into the plan as a print-orientation/stability addendum to `02-design-proposal.md` (candidate C) and `04-roadmap.md`.*
