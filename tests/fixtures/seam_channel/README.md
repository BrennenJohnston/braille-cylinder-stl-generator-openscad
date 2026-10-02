# Seam-channel baseline hashes

`hashes.json` records a geometry signature of the four default plates —
Version 1 and Version 2, embossing and counter — rendered on 2026-09-21
**before** the slicer seam channel was added to the OpenSCAD files (phase O0 of
the OpenSCAD parity plan, research folder `New Developement_2026_09_20`).

From phase O1 on, `tests/test_seam_channel_scad.py` renders each plate with
`seam_channel = "Off"` and the recorded flags, and the geometry must match
these records exactly. That is the "off is identical" contract the web app
pins with its `tests/e2e/fixtures/*_before_seam_channel.stl`.

## What the signature is, and why not the file hash

Triangle count, unique vertex count, the sha256 of the unique vertices rounded
to 1e-5 mm, volume and area. OpenSCAD 2026.01.03 renders the same command to
the same bytes (every record was made twice and matched itself), but a
**changed command line** — one more `-D`, one flag — makes it split a few
coplanar quads on the Version 2 countersink slivers along the other diagonal:
identical vertices, different bytes. The signature does not move under that
flip; the whole-file `sha256` and `byte_size` in the record are informational.
The STLs themselves are not committed (1–8 MB each; `*.stl` is Git LFS here).

## The recorded command

```
openscad.com --hardwarnings --check-parameter-ranges=true --export-format binstl -o <out> -D plate_type="<plate>" -D seam_channel="Off" <file>
```

Every other parameter at its default — note that `Line_1` **and** `Line_2`
default to text. Since 2026-09-24 the Version 2 file defaults to `Tactile`, so
its two records also pass `-D indicator_mode="Visual"` — the style every record
was made in; the recorded bytes and signatures did not change. Use `tests/test_seam_channel_scad.py` rather than a bare
render.

## Re-recording

Only when the pre-channel geometry is meant to change (and say why in the
commit): re-render the four plates with the command above, compute the
signature with the test's `_signature()`, and paste the new values here. The
`warnings_or_errors` count must stay 0.
