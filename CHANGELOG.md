# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Entry wording signed off by Brennen 2026-08-25; whether these fold into 2.8.0
before it tags is still his call.

### Added

- **Both-plates mode (BETA): `render_both_plates = "Off"; // [Off, On]` plus
  `pair_spacing_mm = 10; // [2:1:50]`**, both builds, `[Plate Selection]` tab.
  On, one render builds the complete pair side by side — Cylinder A (embossing
  plate) on the left, Cylinder B (counter plate) on the right, barrel surfaces
  exactly `pair_spacing_mm` apart (centres one diameter plus the gap apart;
  Brennen chose the barrel-based measure 2026-08-25 — with gears On the tips
  overhang to a 8.58 mm tip-to-tip gap, documented on the slider). `plate_type`
  is ignored while On, and the console suggests `Cylinder_Pair_<name>.stl`.
  **Off, renders are byte-identical to before** (sha256-checked on both plates,
  with and without gears). Matches the web app's new combined-pair download.
- **A "Rendering feels very slow" README section.** Measured 2026-08-25: the
  stable 2021.01 release takes over ten minutes (CGAL) for the counter plate
  Nightly's Manifold engine renders in about 2 s — use Nightly — and inside
  Nightly the F5 preview re-pays ~0.5–1 s per frame while rotating (OpenCSG),
  which is normal, while F6 stays fast.
- **A hardware-compatibility warning on Integrated Gears** (customizer text and
  a console `NOTE:` while gears are on): the gears fit only version 2 of the
  braille embosser hardware, not version 1. Wording signed off by Brennen
  2026-08-25; a link to the version 2 build files will be added once published.

### Fixed

- **Both-plates preview no longer comes back empty.** Two whole plates in one
  preview tree could blow past OpenCSG's normalization cap ("Normalized tree is
  growing past 200000 elements … resulted in an empty tree" — reported from the
  GUI 2026-08-25, reproduced with both plates + gears + double-sided). Each
  body in the pair branch is now wrapped in `render()`: the preview tree stays
  at two elements whatever the dials say, at the cost of one ~2 s evaluation.
  Single-plate renders never enter that branch — their output is proven
  byte-identical (sha256) — and the exported pair STL still passes every
  both-plates test.

### Changed

- `gear_set()` takes its plate as a parameter (`emboss = true/false`) instead
  of reading the global plate selection, so a single render can give each
  cylinder its own gear set. No geometry change (sha256-verified).
- The double-sided per-plate filename hint stands aside while
  `render_both_plates` is On — one render, one suggested filename (the pair
  hint). Condition change only; the signed wording is untouched.

## [2.8.0] - UNRELEASED (version bump, tag and release are Brennen's call)

Integrated gears, in beta: a cylinder can now be generated as ONE solid part with
its top and bottom drive gears already attached, instead of a bare barrel that
separately printed gears are pushed onto. Meshed gears are also what keeps a
paired set turning together. **Renders at the shipped defaults are unchanged** —
`integrated_gears` is Off by default, and with it off both plates render
byte-identically to v2.7.0.

Wording in this entry signed off by Brennen 2026-08-25.

### Added

- **`integrated_gears = "Off"; // [Off, On]`, desktop build only.** On, either
  plate exports as a 72 mm roller: the barrel at z 0..52 with a 10 mm gear at
  each end (z −10..0 and 52..62). Measured on both plates — ONE watertight body,
  no enclosed cavity, 24 tooth clusters in each gear band.

- **`assets/gears_a.stl` and `assets/gears_b.stl`**, with
  `assets/GEARS_PROVENANCE.json`. These are a 1:1 replication of the reference
  gear set, never parametric geometry: 24 teeth, tip diameter 32.2187 mm, root
  radius 13.6613702290795, 10.000 mm thick, blind bores, and the axially crowned
  tooth form (a flipped gear is a different gear). A meshed pair runs at an axis
  distance of **32.0473 mm**, which leaves 32.0473 − 30.8000 = **1.2473 mm** of
  barrel-to-barrel gap at the nip. They are derived by the web generator's
  `scripts/derive_gear_assets.py` and converted into this file's frame by
  `python -m tests.test_gear_assets`; never edit them by hand. Both hashes are
  pinned by `tests/test_gear_assets.py`.

- **Two hidden weld rings** (r 8.0–13.0 × 0.1 mm) at the gear/barrel interfaces.
  The gear meets the barrel on an exactly coincident face, which the
  printability rules forbid and float32 STL rounding can turn into a pinch edge.
  They are entirely buried: no external surface changes.

### Changed

- **The barrel prints SOLID while gears are on**, and the console says so when a
  polygonal cutout was set. A one-piece roller has no through-path along its
  axis anyway — the gear bores are blind pockets — so keeping the cutout would
  seal a cavity nothing can reach or drain.

- **Raised tactile row arrows grow by 0.005 mm while gears are on.** At the
  default 10 mm indicator length on 10 mm line spacing each arrow's apex touches
  the next arrow's base exactly, and float32 STL rounding welds that tangency
  into a non-manifold pinch edge — which would break the watertight promise.
  5 µm makes it a real overlap: 2.5% of the recess nesting clearance, far below
  print accuracy. **Off, the outline is untouched**, so existing exports keep the
  tangency they ship with.

- **The MakerWorld single-file build carries the same geometry body**, because
  `tests/test_makerworld_sync.py` requires the two files to stay byte-identical
  below the compatibility marker. It ships no `assets/` folder, so its copy of
  the `integrated_gears` dropdown is declared in a **Hidden** tab and its
  Customizer never offers it.

### Notes

- **The cylinder size is fixed while gears are on: 30.8 mm × 52.0 mm, or the
  render is refused** with "Integrated gears are matched to the reference roller
  and only fit a 30.8 mm x 52 mm cylinder." The gears are baked at fixed heights
  and do not move with the barrel: 1 mm short exports as three loose bodies —
  and each of those is closed, so the file still reports watertight, which is
  why only a body count catches it — while 10 mm tall swallows the teeth. Both
  paper-thickness presets already set 30.8 × 52, so the shipped defaults pass.

- **MakerWorld support is DEFERRED, not forgotten.** That build accepts a single
  `.scad` file and cannot `import()` external assets; embedding two
  30,000-triangle meshes as `polyhedron()` text would risk the Customizer's
  limits. If it is wanted there later, that is its own decision.

- The version bump, tag and release for 2.8.0 are Brennen's to make.


## [2.7.0] - 2026-08-23

One printability threshold moves and one workaround it forced is removed, so this
generator and the web app now warn at the same number. **Renders at the shipped
defaults are unchanged** — the only geometry difference is that the raised
"DOTS TOO CLOSE" text can now appear for the 0.4 mm package in a band that is
reachable only by moving the interpoint offsets off 1.25.

### Changed

- **`DS_GAP_RELIABLE` lowered 0.50 → 0.45 mm, and it is PROVISIONAL.** The web
  app made this change first, after an NVDA walkthrough on 2026-08-23 found that
  its shipped 0.4 mm package (0.4678 mm nominal) sat permanently below the
  0.50 mm line, so *every* double-sided run warned about a package the physical
  validation records as embossing clean. Investigating it turned up that
  **0.50 had no stated basis** in either generator or in any specification: it
  sits beside `DS_GAP_FLOOR` in the same comment, but the Bambu X1C Arachne
  figures quoted there (paths 0.1–0.34 mm force-widened to 0.34, dropped below
  0.1) justify only the floor.

  **0.45 is not a measured value either, and the comment in the `.scad` says so.**
  The two data points that exist — 0.4953 and 0.4278 mm printed ridge — *both
  passed*, and two passing samples cannot locate a failure boundary; they prove
  only that it lies below 0.4278. A print test that walks the gap down until the
  ridge visibly fails is what should set the real number.

- **BEHAVIOUR CHANGE — `DS_GAP_ACCEPTED` is now one line for both packages.** It
  was `ds_use_03_package ? DS_GAP_RELIABLE : DS_GAP_FLOOR`, ratified 2026-08-20,
  which pointed the 0.4 package at the floor and so **retired the physical
  "DOTS TOO CLOSE" text for it entirely**. That existed only to stop the 0.4
  package nagging against a 0.50 mm line it could never clear. At 0.45 it clears
  the line honestly (0.4678 nominal), so the workaround has nothing left to work
  around and it is gone — this generator and the web app now warn at the same
  number instead of two.

  **What existing users of the default 0.4 mm package will see:** the raised
  "DOTS TOO CLOSE" text can now appear in the **0.34–0.45 mm nominal band**, where
  it was previously silent. That band is only reachable by moving
  `interpoint_offset_x_mm` / `interpoint_offset_y_mm` away from 1.25 — at the
  shipped default nothing changes. Verified by facet count: **27,134 facets at
  offset 1.25 (quiet) against 32,038 at 1.21 (text present)**.

  The hard assert is untouched: it still measures `ds_printed_ridge_mm` against
  `DS_GAP_FLOOR` (0.34), so exactly the same renders are blocked as before.

  `makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad` is synced from
  the canonical file, and two tests were updated to pin the new single line.


## [2.6.2] - 2026-08-21

Documentation and test hygiene only. **No `.scad` file was touched**, so every
model renders byte-identically to 2.6.1 — no geometry, dimension, parameter,
default, or range changed.

### Fixed

- **`docs/PARAMETER_MAPPING.md` gains the double-sided parameters.**
  `tests/parameter_mapping.json` went to mapping version 2.6.0 in 2.6.0 with 13
  new entries, but the prose mapping was never updated to match: grepping it for
  `double_sided`, `Back_Line` or `interpoint` returned **nothing**. This repo's
  stated convention — see the 2.5.0 entry — is that the `.md` and the `.json`
  move together, and 2.6.0 broke it. The `.md` now carries a
  **Double-Sided Card (BETA)** section documenting `double_sided`,
  `Back_Line_1`–`Back_Line_10` (as the composite mapping onto the web app's single
  `back_lines` array), and both interpoint offsets with their 1.15–1.35 mm range,
  the two asserts that guard them, and the measured 1.19–1.31 mm renderable band
  on the 0.4 mm package. The mapping version is unchanged at 2.6.0: the `.md` is
  catching up to the `.json`, not describing anything new.

- **Note 5's "Counter Plate Universality" claim is now scoped to single-sided.**
  It stated flatly that counter plates carry recesses at every possible dot
  position and are therefore reusable for any braille pattern. That is false with
  `double_sided` On, where both cylinders carry 1:1 paired recesses and the pair
  is specific to its text.

### Changed

- **The three shared warning-test fixtures move into `tests/conftest.py`.**
  `_trimesh`, `warning_offsets` and `warning_runner` lived in
  `tests/test_text_too_long.py` and were imported by `tests/test_too_many_lines.py`,
  where the import shadowed the test's own parameter names and needed an `F811`
  suppression to stay quiet. A conftest fixture needs no import, so the warning
  now has nothing to report and the suppression is gone along with two `F401`
  ones. The plain helpers (`_render`, `_baseline_params`, `_scad_constant`,
  `_resolve_openscad_path`, `_z_max`, `BRAILLE_FULL_CELL`) deliberately stay in
  `test_text_too_long.py` — ordinary imports never triggered `F811`, and four
  modules import them from there. `tests/conftest.py` also puts the tests
  directory on `sys.path` itself rather than relying on a test module having done
  it first. Suite unchanged at **224 passed, 0 xfailed**.

## [2.6.1] - 2026-08-21

Fuses every raised braille dot to the cylinder shell. **No dimension changed** -
no dot height, diameter or spacing, and no parameter, default or range - so every
model renders the same shape it did in 2.6.0. What changed is the mesh's
topology, and it changed on every cylinder this project has ever produced.

### Fixed

- **Raised dots no longer export as separate bodies.** The shell is a 64-sided
  prism, so each facet dips inside the ideal radius at its centre - 0.0186 mm on
  the shipped 30.8 mm cylinder. A dot's flat base sat at exactly that ideal
  radius, spanning the dip instead of biting into it, so it touched the shell
  only along the facet edges and exported as its own connected body. Measured
  with trimesh: the single-sided emboss default split into **32** bodies (1 shell
  + 31 dots), double-sided Cylinder A into **6** and Cylinder B into **9**, which
  is where the negative Genus readings came from. All three are now **1** body,
  and OpenSCAD reports **Genus 1** on the default where it reported -30.

  The meshes were watertight before and remain so - this was a topology artefact,
  never a hole - but a loose body can be shifted or dropped by some toolchains,
  the gap was a real void under a tactile feature, and a negative Genus reading
  masks any future manifoldness bug behind noise.

  The fix is `DOT_BASE_EMBED`, which lengthens each dot's base frustum downward
  along its own taper so it overlaps solid shell. Because the skirt continues the
  same cone, the dot's radius **at** the shell surface is still the full base
  diameter and its tip is still exactly where it was: the furthest vertex from
  the axis is unchanged to five decimal places in every shipped configuration.
  The tactile seam arrow already did this via `TACTILE_BASE_EMBED`; the dots
  never got the equivalent.

  `DOT_BASE_EMBED` is derived from `radius` and `CYLINDER_SHELL_FN` rather than
  being a fixed figure, because the facet dip scales with radius: 0.0186 mm at
  30.8 mm but 0.0602 mm at the 100 mm the diameter slider allows, so a constant
  small enough to be tidy would leave large cylinders floating. It works out at
  0.0371 mm on the shipped default.

### Known issues

- Inside every *rounded* dot the dome's base circle exactly meets the frustum's
  top with no overlap, and the two are tessellated differently (`cone_segments`
  16 against `quality_fn` 24). It welds today, but it is a zero-overlap tangency
  and therefore luck, not design - a large enough base embed (0.08 mm, 0.18 mm
  and 0.20 mm were all observed) splits the dome off as its own body. Pre-existing
  and unrelated to the embed above; reported, not fixed.

## [2.6.0] - 2026-08-21

Ports the web app's double-sided (interpoint) beta to OpenSCAD, so a single pass
between the two cylinders can emboss braille on **both** faces of one card.

Two of the changes below reach **single-sided Tactile renders as well**: the two
tactile indicator defaults now match the web app, and a new wall guard reports a
printability problem that has been latent in Tactile mode since 2.4.0. Visual
mode — the shipped default — renders byte-identically to 2.5.0 either way.

### Added

- **Double-Sided Card (BETA).** `double_sided = "On"` turns the existing pair of
  plates into partners that each carry raised dots *and* recesses:
  - **Cylinder A** (the Embossing Plate) — the FRONT text as raised dots, plus
    one recessed seat for every BACK dot the other cylinder raises.
  - **Cylinder B** (the Counter Plate) — the BACK text as raised dots, plus one
    recessed seat for every FRONT dot Cylinder A raises.

  Two things change in this mode. There is **no universal recess grid**: every
  recess is the 1:1 partner of an actual dot, so a seat can never sit under this
  plate's own raised dot. And **row indicators are always Tactile** (the raised
  seam arrows), because the paired seats occupy the ground the Visual marker
  columns would stand on, and a blind user needs the arrow to tell the two
  cylinders apart. Choosing Visual while `double_sided` is On is overridden, and
  the model says so on the console and in red text above the cylinder.

  The two faces are offset from each other by the **interpoint offsets**,
  `interpoint_offset_x_mm` and `interpoint_offset_y_mm`, both defaulting to
  1.25 mm and adjustable over 1.15–1.35 mm. Clearance between a dot and its
  neighbouring recess is widest at 1.25 mm and falls off symmetrically toward
  both ends of that range, so "back toward 1.25 mm" is always the fix — never
  "larger" or "smaller".

  **Back-of-card text** goes in `Back_Line_1` – `Back_Line_10`. As on the front,
  this is **pre-translated Unicode braille only** — translation stays a web-app
  feature and is not ported (OpenSCAD has no liblouis). Translate the back the
  same way as the front: Branah, same grade, Unicode Braille output.

  **Double-sided dot and bowl footprints are fixed** — no Customizer dials —
  and **keyed to `paper_thickness_preset`**, which is the card-stock thickness
  being embossed:

  | `paper_thickness_preset` | raised dot | paired recess (nominal) | recess as printed |
  |---|---|---|---|
  | `0.3mm` | ⌀1.2 mm, 0.4 mm base + ⌀0.8 mm dome 0.4 mm high (total 0.8 mm) | ⌀1.3 × 0.5 mm | ⌀1.345 × 0.6725 mm deep |
  | `0.4mm` (default) | ⌀1.2 mm, 0.5 mm base + ⌀1.0 mm dome 0.5 mm high (total 1.0 mm) | ⌀1.4 × 0.5 mm | ⌀1.480 × 0.740 mm deep |

  Both packages were chosen by physical embossing tests on a Bambu Lab X1C with
  a 0.4 mm nozzle during 2026-08, not by calculation: the `0.3mm` package
  embossed legible braille on both sides of 0.3 mm card stock, and the `0.4mm`
  package is the only one in the test matrix that came out clean on 0.4 mm
  stock. Total dot height is capped at 1.0 mm because taller dies scrape the
  embosser's cylinder-holder housing.

  The port is **cross-validated against the web generator's committed
  double-sided golden STL pair**: all 26 double-sided features on both plates
  land within 0.0068 mm of arc and 0.0024 mm of height of their golden partners,
  and the A-minus-B volume (in which the shell cancels exactly) agrees to
  0.168 mm³, or 0.157%. Because the goldens were generated with the `0.3mm`
  package, that comparison renders this program at
  `paper_thickness_preset = "0.3mm"`.

- **`[Double-Sided Card (BETA)]` Customizer tab.** It holds the `double_sided`
  gate, all ten `Back_Line_N` fields, and both interpoint offset sliders
  (`[1.15:0.01:1.35]`, the same range the render's own assert enforces). All ten
  back lines sit in the one tab — there is no back-side counterpart to the
  front's `[More Braille Lines (Advanced)]` tab — and the footprints above are
  deliberately absent, so there is nothing there to hunt for.

- **Back lines are covered by the existing text warnings.** This is the
  user-visible half of the tab. Until now, untranslated text in a back line
  rendered an all-zero dot pattern and left the back of the card **silently
  blank**. `INVALID CHARACTERS`, `TEXT TOO LONG` and `TOO MANY LINES` all count
  the back lines whenever `double_sided` is On, and each console message names
  the `Back_Line` that actually overflowed.

- **A suggested export filename** is echoed on every double-sided render —
  `Cylinder_A_…` for the Embossing Plate, `Cylinder_B_…` for the Counter Plate —
  so the pair does not get mixed up between two renders.

- **Tactile seam-recess wall guard — this affects single-sided renders too.**
  The counter plate's arrow recess cuts inward toward the polygonal cutout, and
  nothing stopped a user thinning the wall between them past what an FDM printer
  can hold. When `indicator_mode` is Tactile and a polygonal cutout is present,
  the generator now checks that wall against a 1.2 mm minimum; below it, the
  console echoes a `WARNING:` naming the measured thickness and red
  `TACTILE WALL TOO THIN: <n> mm` text renders above the cylinder for the
  MakerWorld preview, which has no console. It **warns only** — the STL is still
  written, on the same reasoning as `TACTILE GAP TOO SMALL`: this is a wall an
  informed user may have a reason to thin.

  At the shipped defaults the wall measures **1.224 mm** and is clear. The
  pre-2.6.0 `tactile_indicator_raise` of 0.8 mm left **0.924 mm** — already
  under the printable minimum, which is what the guard was written to catch.

### Changed

- **`tactile_indicator_length` 5.0 → 10.0 mm** and **`tactile_indicator_raise`
  0.8 → 0.5 mm**, aligning both with the web app, which has carried these values
  since it ported tactile mode. These were the only two numeric drifts in a
  46-parameter audit against the web schema.

  **This is a behavior change for existing users, in Tactile indicator mode
  only** — Visual-mode renders are byte-identical to 2.5.0. The arrow is now
  twice as long along the cylinder axis (at the 10 mm default `line_spacing`,
  each row's arrow meets the base of the one above) and stands 0.3 mm lower.
  The safety consequence, measured off real STLs rather than assumed: on the
  counter plate the seam recess is now 0.7 mm deep instead of 1.0 mm, which
  takes the wall out to the polygonal cutout from 0.924 mm to **1.224 mm** —
  the old value was below the 1.2 mm minimum FDM wall.

- **`INVALID CHARACTERS` is now shown on the Counter Plate as well as the
  Embossing Plate — this affects single-sided renders too.** Before, a counter
  plate rendered from untranslated text said nothing at all, even though its
  paired embossing plate would come out blank. This follows the precedent set by
  `TACTILE GAP TOO SMALL`, which has always appeared on both plates because the
  pair is printed from one set of settings.

- **The double-sided printability guard now measures the recess's PRINTED mouth
  rather than its nominal diameter.** The recess is cut as a hemisphere centred
  on the shell surface, so its mouth comes out wider than the number typed into
  it — ⌀1.480 mm printed against a ⌀1.4 mm nominal on the `0.4mm` package — and
  the old guard let through a ridge the printer cannot hold.

  Consequence worth knowing before you move a slider: with the `0.4mm` package
  the renderable interpoint-offset band is **1.19–1.31 mm**, not the slider's
  full 1.15–1.35 mm; the `0.3mm` package accepts the whole range. Clearance
  peaks at 1.25 mm and falls off symmetrically toward both ends, so the guard's
  message points back to 1.25 mm rather than telling you to increase or decrease
  anything. The `DOTS TOO CLOSE` warning deliberately still reports the
  **nominal** figure, so it keeps quoting the same number as the web app's live
  warning.

- `tests/parameter_mapping.json` is bumped to mapping version 2.6.0 — 13 new
  entries, for 59 parameters and 31 slider ranges.

### Notes for maintainers

- **The MakerWorld v2 variant is synced, and it has no geometry or default
  divergences from the canonical file at all.** With identical `-D` arguments
  the two builds now produce **byte-identical** double-sided STLs on both
  plates. Only three **presentation** differences remain above the sync marker:
  the MakerWorld single-file header block, the three-line `dot_shape` comment
  explaining the flattened build's Rounded default, and `presets.scad` inlined
  in place of `include <presets.scad>;`. All three double-sided asserts were
  copied across verbatim rather than swapped for rendered red text, so the two
  builds agree about what is printable.
- The MakerWorld sync guard in `tests/test_makerworld_sync.py` now compares
  **parameter defaults and slider ranges** across 89 top-level declarations —
  every Customizer parameter, all twenty text fields, and every `DS_*` constant
  — plus the inlined `presets.scad` block, not just the geometry body. The
  earlier body-only guard is what let the two tactile defaults above drift apart
  in the first place.
- MakerWorld users receive the double-sided beta **and** the two tactile default
  changes in this one release; desktop users on 2.5.x already had neither.
- `makerworld/README.md`'s re-flatten procedure gained the step it was missing:
  the `DOUBLE-SIDED (INTERPOINT) MATH` section must be copied into the variant's
  header **after** the inlined-presets `END` sentinel, because `ds_use_03_package`
  reads `paper_thickness_preset` and `ds_printed_ridge_mm` reads both offset
  sliders, and OpenSCAD evaluates top-level assignments in source order.
- The SCAD hashes move with this release. The web app repo vendors the MakerWorld
  build and pins it by hash, so it needs a re-vendor against this tag.

## [2.5.0] - 2026-08-01

Closes the gap between how many braille rows the generator can render and how
many the Customizer let you type. `grid_rows` has allowed up to 10 rows since
2.0.0, but only four `Line_N` fields existed — so rows 5 through 10 were
reachable only by editing the source or passing `-D` flags.

### Added

- **`Line_5` – `Line_10`.** `Line_5` – `Line_8` join the existing
  `[Text Input - Pre-Translated Braille]` tab, so eight rows are visible without
  hunting for anything. `Line_9` and `Line_10` sit in a new
  `[More Braille Lines (Advanced)]` tab: the Customizer cannot add fields on
  demand the way the web app grows its line list, and putting all ten in the
  first tab pushes the rest of the settings off screen for the common case. The
  parameter names are the same wherever they display, so presets and `-D`
  overrides are unaffected.
- **`TOO MANY LINES: n/grid_rows` warning.** Only the first `grid_rows` rows are
  ever rendered. Until now, braille pasted into a line past that limit simply
  never appeared — no console message, nothing on the model, and an exported STL
  quietly missing text. The generator now reports it the way it reports every
  other problem: a console `echo()` naming the row to raise `grid_rows` to, plus
  red text above the cylinder for the MakerWorld preview, which has no console.
  Unlike `TEXT TOO LONG` this is not gated on `text_limit_check`; rows past the
  grid cannot be drawn under any setting, so there is no bypass worth offering.
- `tests/test_too_many_lines.py`: render test comparing bounding-box Z-max
  (skipped without OpenSCAD, as `test_text_too_long.py` does), source guards for
  the warning, and guards pinning the `Line_1` – `Line_10` wiring — every row
  declared, `_all_lines` complete and in order, no stray `Line_N` outside its
  declaration, the `grid_rows` slider max matching the field count, and the
  MakerWorld build carrying the same declarations.

### Changed

- **`_all_lines` is now the single source of truth for the text.** The capacity
  check, the per-line console diagnostics, the invalid-character check, and the
  dot loop each used to name `Line_1` through `Line_4` individually, which is
  four places to forget when a row is added. They all iterate one list now, so
  adding row 11 someday means declaring it and appending it — nothing else.
- `docs/PARAMETER_MAPPING.md` and `tests/parameter_mapping.json` (bumped to
  mapping version 2.4.0) document the six new parameters and the Advanced tab.

### Notes for maintainers

- The MakerWorld build was re-flattened per `makerworld/README.md`; its geometry
  body stays byte-identical to the canonical file.
- The SCAD hashes move with this release. The web app repo vendors the MakerWorld
  build and pins it by hash, so it needs a re-vendor against this tag.

## [2.4.1] - 2026-07-29

### Changed
- Web app links now point at `https://braille-cylinder-stl-generator.vercel.app`.
  The web app's Vercel project was recreated under its renamed GitHub repo, so the
  old `braille-card-and-cylinder-stl-gener.vercel.app` deployment is no longer the
  one receiving updates. Changed in the REFERENCES header of both SCAD builds,
  `README.md`, `CONTRIBUTING.md`, `docs/PARAMETER_MAPPING.md`, `tests/README.md`,
  and `tests/fixtures/cross_platform/README.md`. Geometry is untouched, so the
  reference STLs and `fixture_version` are unchanged — but the SCAD hashes move,
  which is why this needs a tag: the web app repo vendors the MakerWorld build and
  pins it by hash.
- Documentation now reflects that the web app has ported tactile indicator mode
  (2026-07-29). `docs/PARAMETER_MAPPING.md` claimed "the web app has no tactile
  indicator mode, so all six map to `web_api_name: null`", which is no longer
  true: all six parameters carry the same names there, and the five numeric
  defaults are asserted equal by a test on the web side. Filled in the real
  `web_api_name` values in both `docs/PARAMETER_MAPPING.md` and
  `tests/parameter_mapping.json`; `text_limit_check` remains the only
  genuinely OpenSCAD-only parameter.
- Noted in `README.md` and `docs/PARAMETER_MAPPING.md` that the pre-translated
  braille workflow is no longer unique to this version — the web app has a
  Braille (Unicode) field that is used verbatim. Automatic translation is the
  one thing working offline still costs you.
- Expanded the phone-number guidance in `docs/MAKERWORLD_QUICK_START.md` to
  explain *why* hyphens have to become periods: a period keeps UEB numeric mode
  but a hyphen or parenthesis ends it, so `206-543-4779` correctly needs three
  number signs (15 cells, will not fit) against one for `206.543.4779` (13
  cells). Previously the guide only warned about translators repeating the sign
  after periods, which is a different cause with a different fix.

## [2.4.0] - 2026-07-27

### Added
- **Tactile indicator mode (`indicator_mode` = `Visual` / `Tactile`).** A new
  `/* [Indicator Mode] */` Customizer section in both SCAD builds. `Visual`
  (default) is the existing behavior, byte-for-byte: recessed alignment
  triangle at the start of every row, plus the letter square when Indicator
  Letters are On. `Tactile` replaces those marker columns with a
  blind-accessible indicator that both plates share:
  - **Raised arrow on the embossing plate, matching recess on the counter
    plate**, one per braille row, centred in the seam gap between the last and
    first cell. Because the grid is centred on angle 0, that midpoint is always
    exactly 180° — the fixed point of the counter plate's `mirror([0,1,0])` /
    angle-negation construction — so the arrow and its recess self-align
    radially at any rotation of the paired cylinders.
  - **The arrow points at the cylinder top**, so a user can feel which end is
    up on either plate, while raised-vs-recessed tells them which cylinder they
    are holding. It is circumferentially symmetric so the mirrored recess has
    the identical outline and the two nest instead of colliding.
  - **Crush-safe by design.** The 0.8 mm default raise is deliberately below
    the 1.0 mm braille dot height, so the dots — never the indicator — carry
    the rolling pressure. Verified nesting at defaults: arrow tip at radius
    16.2 mm, recess floor at 14.4 mm (0.2 mm radial slack), 0.2 mm outline
    clearance, and 0.93 mm of wall left over the polygonal cutout.
  - **Marker columns are dropped**, so `grid_columns` alone sets the grid and
    up to 14 text cells fit the default 30.8 mm cylinder. The Indicator Letters
    toggle is ignored in this mode.
  - Five Tactile-only sliders (`tactile_indicator_width`,
    `tactile_indicator_length`, `tactile_indicator_raise`,
    `tactile_recess_clearance`, `tactile_recess_extra_depth`). Like
    `grid_columns`, they are slider-only — the paper-thickness presets never
    touch them.
  - Curvature-conforming geometry: both features are a radial prism
    intersected with a shell band built at `CYLINDER_SHELL_FN`, so the raise
    and recess depth stay uniform across the whole arrow (a flat prism would
    lose ~0.13 mm at its edges to the chord sagitta — large next to a 0.2 mm
    nesting margin).
- **`TACTILE GAP TOO SMALL` warning.** In Tactile mode, when the seam gap can
  no longer hold the indicator plus a clear zone either side (e.g.
  `grid_columns = 15` on the default cylinder, which leaves only 5.8 mm), red
  3D text renders above the cylinder on **both** plates with the measured gap,
  plus a desktop `echo()` naming the fix. Stacked one step above
  `TEXT TOO LONG`, reusing the shared `INVALID_TEXT_*` placement constants.
- **`tests/test_tactile_mode.py`.** Fast source-only guards (32 checks across
  both SCAD builds) covering the Customizer surface, the 180° placement, the
  shell-band tessellation, the recess clearance offset, the crush-safety
  invariant (raise < dot height), and the Visual path staying gated behind
  `!tactile_on`. Includes an ordering guard for `TACTILE_MIN_GAP_MARGIN`:
  OpenSCAD evaluates top-level assignments sequentially, so a forward
  reference would silently resolve to `undef` and the warning would never fire.
- **Two Tactile reference fixtures** (`cylinder_rounded_emboss_tactile`,
  `cylinder_rounded_counter_tactile`), fixture set version 2.4.0. All 14
  pre-existing reference STLs are byte-identical after regeneration, which is
  the proof that Visual mode is untouched.
- **`text_limit_check` On/Off parameter (Text Input section).** `On` (default)
  keeps the existing behavior: rows are clipped to the cell capacity and the
  red warning renders when a line is too long. `Off` bypasses the check —
  every pasted cell renders (embossing dots and counter-plate recesses alike)
  and no warning appears, at the cost of overlong rows possibly crowding the
  seam gap. Added to both SCAD files, `tests/parameter_mapping.json`,
  `docs/PARAMETER_MAPPING.md`, and the README troubleshooting section.
- **Counts in the `TEXT TOO LONG` warning.** The red extrusion now reads
  `TEXT TOO LONG: <longest line>/<capacity>` (e.g. `TEXT TOO LONG: 16/13`) so
  MakerWorld users — who cannot see the console — know how far over the limit
  they are. Desktop users additionally get a per-line `echo()` warning naming
  the offending `Line_N`, its cell count, the capacity, and the available
  fixes.
- **MakerWorld Quick Start Guide.** New `docs/MAKERWORLD_QUICK_START.md` plus
  a generated PDF (`docs/MakerWorld_Quick_Start_Guide.pdf`) covering the
  upload flow, braille translation, capacity rules, phone-number formatting,
  and the counter-plate pairing tip. Linked from `makerworld/README.md`.

### Changed
- **Default `dot_shape` is now `"Rounded"`** (was `"Cone"`) in both
  `Braille_Cylinder_STL_Generator.scad` and the MakerWorld single-file build,
  matching the web app where the 0.4mm/0.3mm presets default to the Rounded
  dot shape. The dropdown still offers `Cone`. Preset dot/spacing dimensions
  are unchanged. `tests/test_makerworld_sync.py` now asserts the Rounded
  default in both files.
- **Indicator Letters toggle no longer removes the triangle.** The triangle
  alignment indicator at column 0 is now always generated on both plates — it
  is critical to the mechanical device the cylinder mounts into and has no
  user-facing toggle. The `indicators` toggle (relabeled "Indicator Letters")
  gates only the square/rectangle marker at column 1. Grid widening is now
  `+2` cells when On (triangle + square) and `+1` when Off (triangle only),
  so turning Indicator Letters Off frees 1 cell of physical space per row (up
  to 14 text cells fit the default cylinder, up from 13). Text capacity
  remains `grid_columns` in both states. Applied to `place_row_indicators`,
  `actual_grid_columns`, and the emboss/counter dot-placement offsets in both
  SCAD files; docs (`README.md`, `docs/PARAMETER_MAPPING.md`,
  `docs/MAKERWORLD_QUICK_START.md`, `makerworld/README.md`) updated to match.
- **Regenerated the 14 cross-platform reference fixtures** (OpenSCAD self-test
  mode). Geometry changed only for the four `indicators_off` core-matrix cases
  (the always-present triangle) and the two indicator-isolation fixtures; the
  `indicators_on` core-matrix STLs are byte-identical, confirming indicators-on
  geometry is unchanged. This also refreshed the stale
  `cylinder_indicator_recess_rounded` reference, which had drifted from the
  current code (pre-existing ~2.75% volume mismatch) before these changes.
- **`grid_columns` default raised from 11 to 13.** Matches the web app's
  13-cell default row capacity, so a BANA-formatted 10-digit phone number
  (e.g. `⠼⠃⠚⠋⠲⠋⠁⠋⠲⠛⠋⠛⠓`, 13 cells) fits on one row out of the box. Applied
  to both SCAD files, `tests/parameter_mapping.json`, and docs.
- **`grid_columns` / `grid_rows` removed from the paper-thickness presets.**
  `PRESET_04` and `PRESET_03` now control 21 parameters (down from 23); the
  capacity sliders always govern the grid, matching the web app where the
  Card Thickness dropdown never touches columns/rows. Updated `presets.scad`,
  the inlined MakerWorld copy, `tests/test_presets.py`, and docs.
- **MakerWorld single-file build renamed to
  `Braille_Cylinder_STL_Generator_MakerWorld_v2.scad`.** Byte-identical rename
  of the previous file; `tests/test_makerworld_sync.py`, `README.md`,
  `makerworld/README.md`, and `docs/MAKERWORLD_QUICK_START.md` now point at the
  new filename.
- **Repository renamed to `braille-cylinder-stl-generator-openscad`,** matching
  its web app companion's rename to `braille-cylinder-stl-generator`. Neither
  tool has generated flat cards since the web app's v2.0.0, so the old names
  advertised a feature that no longer exists. GitHub redirects the old URLs; the
  CI badge, clone instructions, LICENSE required notice, and every cross-link in
  the READMEs, docs, tests, and both SCAD headers now use the new names.
- **Sibling-repo links that pointed at private repos.** The README's Spin-off
  Projects table linked private `plug-puller-openscad`, which 404s for anyone
  but the owner; it now links the public release repo
  [openscad-plug-puller](https://github.com/BrennenJohnston/openscad-plug-puller).
  `cad-to-openscad-pipeline` is unpublished, so it is named as private instead of
  linked.

### Removed
- **Braille wedge card generator split into its own repository.** The
  experimental leaning-card generator
  (`experimental/braille-business-card/`) was refactored into a pure
  directly-readable braille card (embossing-era plate/counter/indicator
  concepts removed, 20 text rows, print-tested Try_4 defaults, its own
  tests/docs/CI) and extracted with history via `git subtree split` to
  [braille-wedge-card-openscad](https://github.com/BrennenJohnston/braille-wedge-card-openscad)
  (v1.0.0). The folder is deleted here; a "Spin-off Projects" row in
  `README.md` links to the new repo. Cylinder generator code, tests, and
  fixtures are untouched.

### Fixed
- **`tests/validate_parameter_schema.py` was failing on the `dot_shape`
  default.** `tests/parameter_mapping.json` still recorded `"Cone"` after the
  default changed to `"Rounded"`, so the CI schema check errored out. The
  mapping now records `"Rounded"`, matching both SCAD builds.
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
  moved to `plug-puller-openscad` (private dev repo); the public release lives
  at [openscad-plug-puller](https://github.com/BrennenJohnston/openscad-plug-puller).
- DXF/SVG conversion scripts (`scripts/dxf_to_openscad_polygon.py`,
  `scripts/extract_svg_overlay_outline.py`) — moved to
  `cad-to-openscad-pipeline` (private).
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
- Spin-off sibling repository `plug-puller-openscad` (private) — holds the
  Plug Puller v1/v2/v3/v4 design work previously living in
  `Plug Puller Test/`. Public release:
  [openscad-plug-puller](https://github.com/BrennenJohnston/openscad-plug-puller).
- Spin-off sibling repository `cad-to-openscad-pipeline` (private) — packages
  the CAD-to-OpenSCAD methodology and the general-purpose
  `dxf-to-openscad-polygon` console script.

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
