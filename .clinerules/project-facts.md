# Project Facts — braille-stl-generator-openscad (always active)

Offline OpenSCAD companion of the braille-cylinder web app: braille embossing
and counter plates for cylinders, fully client-free. Working branch: develop.

1. Main model: Braille_Cylinder_STL_Generator.scad. Presets: presets.scad.
   MakerWorld variant: makerworld\Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad
   (keep deliberately in sync when the main model changes).
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
