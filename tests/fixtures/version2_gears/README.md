# Version 2 gears-Off baseline signature

`gears_off_signature.json` records a geometry signature of the two default
Version 2 plates (embossing and counter; `integrated_gears` Off, `seam_channel`
On, every other parameter at its default) rendered on 2026-09-21 from
`Braille_Cylinder_STL_Generator_EmbosserV2.scad` as committed at `0f1dd48` —
**before** the fixed-gear switch was added (phase O5 of the OpenSCAD parity
plan, research folder `New Developement_2026_09_20`).

`tests/test_embosser_v2_gears_scad.py::test_gears_off_is_the_pre_gears_geometry`
renders each plate with the recorded flags and the geometry must match exactly.
That is the "off is identical" contract the web generator proved for fused
Version 2 at five levels, and the one `tests/fixtures/seam_channel/` keeps for
the channel.

The signature is the one `tests/test_seam_channel_scad.py::_signature()`
computes (triangle count, unique vertex count, sha256 of the unique vertices
rounded to 1e-5 mm, volume, area) — robust to the coplanar-quad diagonal flips
a changed command line causes; see `tests/fixtures/seam_channel/README.md`.

## The recorded command

```
openscad.com --hardwarnings --check-parameter-ranges=true --export-format binstl -o <out> -D plate_type="<plate>" Braille_Cylinder_STL_Generator_EmbosserV2.scad
```

## What the test pins today

The file's defaults have moved twice since the signature was taken, in ways that
are not about the gears: `indicator_mode` defaults to Tactile since 2.10.0 and the
single `key_clearance_mm` (0.110 when recorded) became four per-gear dials at
0.095 in 2.11.0. The test therefore renders with `-D indicator_mode="Visual"` and
the four `key_clearance_{a1,a2,b1,b2}_mm` at 0.11, as the fixture's `defines`
record - reproducing the signature at the old value on four dials is also the
proof that the per-key refactor moved nothing.

## Re-recording

Only when the gears-Off Version 2 geometry is meant to change (and say why in
the commit): render both plates with the command above, compute the signature
with `_signature()`, and paste the new values here.
