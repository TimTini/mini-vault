# Housing mouth: continuous feature CSG

## Recessed capsule grooves: corrected 2026-10-17

The current 200 preset uses a 3 mm main wall with 0.6 mm grooves cut directly
into that wall. The groove floors retain 2.4 mm and the uncut lands remain
3 mm. Maximum dimensions stay 200 x 200 x 200 mm. There is no added exterior
panel. This supersedes the earlier raised-panel interpretation.

Groove walls now slope at 45 degrees through the full 0.6 mm depth. The outer
capsule mouth stays 20 mm wide, while the flat floor is 18.8 mm wide. Two conical
cutters joined by a convex hull preserve this slope around the rounded ends as
well as along the straight sides. This applies to both current 150 and 200
presets. It adds no material outside the original shell. Print appearance still
requires slicer and physical validation.

`housing_texture=0` keeps the plain shell; `1` subtracts capsule cutters from
four sidewalls adjoining the mouth. The rear remains 2 mm and the door remains
2.4 mm, both plain. Functional mouth, hinge guides and lock pockets keep their
previous geometry. Main-wall measurements do not describe the unchanged lip.

`housing_texture_depth/width/pitch` use final millimetres; defaults are
0.6 / 20 / 32. The old `housing_texture_height` parameter is removed. There are
five grooves per face in the 200 preset. A 25 mm front band stays untouched;
the first groove tip is 33 mm behind the front, with a 16 mm rear margin.
Short bodies that cannot fit the margins and rounded groove ends, or depth
settings leaving less than 1.8 mm of wall, are rejected explicitly.

Run `python -m unittest tests.test_housing_texture tests.test_housing_features
tests.test_native_housing -v`. Check contacts with `python
work/verify-housing-texture.py --backup <snapshot-directory> --openscad
<openscad.com>` against a local hash-verified snapshot. The verifier compares
21 static pairs, 361 door positions, two sliders at 121 positions, and nine
rotating parts at 180 angles: 2244 pairwise records. These are geometry checks,
not thermal deformation, physical strength or print validation.

After export, add `--delivered` to check the actual housing STL against its
current print manifest without rendering again; `--openscad` is then optional.
The report records the selected housing path, source mode and exact file hash.
Select `--preset '150 - scale 1'` to compare the 150 kit with its own snapshot;
its report is `contact-verification-150.json`, separate from the default 200
report. For both variants the 45-degree slope is checked by transverse rays and
capsule-end rays, with the original wall floor and outer envelope retained.

Export and read back the 200 kit with `work/export-print-kit.py` and
`work/verify-print-delivery.py --preset '200 - scale 1'`. Older numerical
checkpoints below describe the source at their recorded state.

`geometry/housing.scad` owns the housing shell and mouth. Dimensions are in mm
before the final `size_scale`. Datum: X/Z are the front sketch, Y is depth;
the hinge pivot is `[20,-0.5,0]`. Relations recovered from the reference are
inferred design intent, while dimensions below are measured.

The mouth no longer loads `profiles/housing.scad`. That file is retained only as
historical reference data; its 461 front layers are not executed by the model.

## Features and ownership

- Outer shell and edge rounds: existing `native_housing_outer`, unchanged.
- Front opening: corner centres X=-80/30, Z=±30, R10.2; straight Y=-7.5..14.
  The R0.5 entrance round is a quarter-circle loft. Panel spans follow
  `body_point`; mounting dimensions retain their original values.
- Right swing clearance: rounded opening swept through a symmetric cubic loft.
  For `t=abs(Y+0.5)/6.5`, the right edge is
  `40.2+0.9*(1-1.5*t*t+0.5*t*t*t)` over Y=-7..6. Against 25 independent
  reference section vertices at Z=0, maximum residual was 0.0063 mm.
  One convex hull of 33 stations approximates this concave boundary curve in
  32 intervals. The constant left/top/bottom extents make that hull appropriate;
  the independent right-edge residual must be rechecked if the curve changes.
  These are stations of one named feature, not measured STL layers.
- Left lead-in: union the narrow opening with a conical/planar 45° loft,
  left corner centres X=-88, Z=±30, radius `Y-0.8` over Y=3..11.
  The rear opening then continues to Y=14. The ordinary wall-thickness cavity
  takes over behind Y=14.
- Lock pockets: X=-98.2..-90.2, Y=-5.2..0.2, Z=15.8..24.2 and -24.2..-15.8.
  The upper pocket retains the measured R1 concave entrance around its four
  edges. Its cross-sections are rectangles expanded by `1-cos(a)` as X follows
  `-91.2+sin(a)`, a quarter-circle law. The lower pocket retains square edges.
- Central lock stop: trapezoid X=-90.2..-88.2, Z=±9 at its root / ±7 at its tip,
  Y=-5..-3; a 45° rear taper ends at Y=-1.
- Hinge guide pair: X=3.5..15.5, |Z|=36.2..40.2, Y=-5..4, then a 45° ramp
  ends at Y=8. A recess X=5.5..15.5, |Z|≥38.1, Y=-3..2 keeps the socket step.
- Optional hinge gussets: existing construction and parameter, unchanged.

The front lip is independent of `wall_thickness` and `body_corner_radius`.
The rear cavity still follows both. Width changes move left-side lock features
with the left wall; height changes move hinge guides with the top/bottom panels.

## Verification

Keep `$fn=128`, Manifold backend, and exporter tolerance 0.005 mm when comparing
builders. Source complexity, direct indexed faces, and simplified STL triangles
are separate measurements. `tests/test_housing_features.py` rejects a production
measured-profile dependency and a default indexed mesh with 20,000 or more faces.

Local reconstruction evidence and failed prototypes stay under
`work/housing-feature-rebuild/`; the immutable old builder and current-kit
snapshot stay under `work/backup/housing-feature-20261017/`. These local inputs
are not part of a public source clone. Reproduce the matrix and sampled motion
check with the project Python runtime and its `requirements.txt` dependencies:

```powershell
& '<project-python>' work/verify-housing-features.py --openscad '<openscad.com>'
$env:MINI_VAULT_OPENSCAD='<openscad.com>'
& '<project-python>' -m unittest tests.test_housing_features tests.test_native_housing -v
```

The verifier leaves delivered kits untouched. It compares every saved preset,
minimum depth, rounded corners and maximum dimensions to the snapshotted old
builder, including targeted functional contours and two-way seeded surface
samples. At a sharp pocket end, compare indexed CSG within 0.005 mm of the seam:
the old simplified STL can smear an 8 mm step across that tiny distance.
Printed-mesh contour probes sit 0.02 mm away; the tolerance remains 0.1 mm.

Housing contacts are compared using rigid door poses (0..90°, 0.25° steps) and
121 slider positions for both active print presets. These checks do not establish
physical fit, force, durability, warping, slicing, or an independent exhaustive
self-intersection audit.

## Checkpoint: 2026-10-17

OpenSCAD 2026.09.29, Manifold, curve_segments=128, simplify=0.005 mm:

- Default: 307,260 → 17,204 indexed faces; 130,512 → 9,972 STL triangles.
- 200 - scale 1: 314,736 → 16,838 indexed faces; 128,972 → 10,510 STL triangles.
- 220 - scale 1.5: 314,594 → 17,074 indexed faces; 152,792 → 10,616 STL triangles.
- Eight geometry cases passed: all five saved presets, minimum depth, R13 outer
  corners, and maximum dimensions with wall 3 / rear 4 / R14 corners.
- Five focused unit tests passed, including five-preset mounting measurements.
- Each active print preset had 21 static housing pairs, 361 door poses and 121
  slider poses compared; no increased significant housing contact was found.
- Both 22-part STL kits were regenerated and read back. Only the housing source
  mesh changed; the other 21 source STL hashes stayed identical in each kit.

This is a bounded reconstruction: for the 200 preset, the two-way seeded surface
sample maximum against the previous builder was 0.0196 mm, and the largest
tested regular contour deviation was 0.0202 mm. These are sampled measurements,
not a Hausdorff bound or proof of physical fit. Existing slicer 3MF projects and
printer profiles were not changed by this source reconstruction.


Superseded raised-panel delivery checkpoint: 11 focused housing tests and 4 viewer tests passed;
2244 pairwise contacts showed no increased significant overlap. The delivered
housing has 29344 indexed faces / 22886 STL triangles and no final zero-area
triangles. All 22 print parts were read back as closed solids with exact source
triangles and placement. Only the housing source STL changed; all other 21
hashes matched the pre-texture snapshot. Chrono poses and viewer input checks
were refreshed. Local evidence is bound by
`work/housing-texture/final-acceptance.json`. Existing 3MF projects are unchanged.

Corrected recessed-groove delivery checkpoint: 12 focused housing tests passed,
plus three thickness, margin and topology checks on the actual delivered STL.
That housing has 27236 indexed faces / 20912 STL triangles, no final zero-area
triangles and one closed volume. All 22 print parts passed readback; only the
housing changed and the other 21 source STL hashes match the snapshot.
The actual delivered housing passed 2244 pairwise contact comparisons with no
increased significant overlap. Chrono poses and viewer input checks passed.
Local evidence is bound by `work/housing-texture/recessed-final-acceptance.json`.
