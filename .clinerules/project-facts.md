# Project Facts — braille-stl-generator-openscad (always active)

Offline OpenSCAD companion of the braille-cylinder web app: braille embossing
and counter plates for cylinders, fully client-free. Working branch: develop.

1. Main model: Braille_Cylinder_STL_Generator.scad. Presets: presets.scad.
   Version 2 model: Braille_Cylinder_STL_Generator_EmbosserV2.scad.
   MakerWorld uploads in makerworld\: _v1.5.scad (Version 1) and _v2.scad
   (Version 2) - keep them deliberately in sync with their model - and
   _v2_Fixed_Gears.scad, which is GENERATED (python
   scripts\build_makerworld_fixed_gears.py; never edit it by hand).
2. Named checks: powershell -ExecutionPolicy Bypass -File scripts\scad-check.ps1
   (after every .scad edit) and python -m pytest tests/ -v (before commits).
   CI renders with OpenSCAD 2026.01.03 — same as the local canonical binary.
3. The web app repo (braille-cylinder-stl-generator\OpenSCAD\) VENDORS a copy
   of this generator. After changing Braille_Cylinder_STL_Generator.scad here,
   tell me the web repo needs re-vendoring (see its VENDORED.json).
4. Canonical braille constants (do not change without my approval): dot
   spacing 2.5 / cell 6.5 / line 10.0 mm; dot map [[0,0],[1,0],[2,0],[0,1],
   [1,1],[2,1]] = dots 1–6. Full geometry specs live in the web repo at
   braille-cylinder-stl-generator\docs\specifications\ — load only the one
   spec a task needs.
5. New Research\ contains vendored third-party material — never edit it.
6. Render-and-look cameras: both plates are translated up by
   cylinder_height/2 (26 mm at the default 52 mm height), so a camera aimed
   at z=0 clips them — the model sits half out of frame. Aim at z=26:
   --camera=0,0,26,90,0,0,150   (front)
   --camera=0,0,26,90,0,90,150  (side)
   --camera=0,0,26,60,0,45,150  (three-quarter)
   Raise the last number (distance) if a taller cylinder still overflows.
   Since v2.9.0 the default render is BOTH cylinders side by side
   (render_both_plates = "On", about 82 mm wide): use distance 200 and add
   --render (a preview of the counter plate comes out blank), or pass
   -D 'render_both_plates="Off"' to look at one plate.
7. The Customizer MIRRORS THE WEB APP'S UI (Brennen, 2026-10-07): the same
   sections in the same top-down order under the same names, and every dial
   the web app keeps under Expert Mode in an "Expert Mode - <its submenu>"
   tab. A dial the web app lacks goes at the end of its section or in the
   OpenSCAD-only Expert tabs after the mirrored ones. Each dial's
   description is ONE comment line directly above it: OpenSCAD and
   MakerWorld show only that line. tests/test_customizer_layout.py pins all
   of this. When a web app UI change adds, moves, renames or reorders a
   control or section, change the four model files and that test, and
   regenerate the fixed-gear upload, in the same round.
