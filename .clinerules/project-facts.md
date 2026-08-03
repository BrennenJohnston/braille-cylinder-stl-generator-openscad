# Project Facts — braille-stl-generator-openscad (always active)

Offline OpenSCAD companion of the braille-cylinder web app: braille embossing
and counter plates for cylinders, fully client-free. Working branch: develop.

1. Main model: Braille_Cylinder_STL_Generator.scad. Presets: presets.scad.
   MakerWorld variant: makerworld\Braille_Cylinder_STL_Generator_MakerWorld_v2.scad
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
