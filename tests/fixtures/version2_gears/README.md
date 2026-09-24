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

## Re-recording

Only when the gears-Off Version 2 geometry is meant to change (and say why in
the commit): render both plates with the command above, compute the signature
with `_signature()`, and paste the new values here.
