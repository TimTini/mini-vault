# Door rear: continuous feature CSG

`geometry/door.scad` owns the panel and marker. `geometry/door-rear.scad` owns
the rear mounting features. `profiles/door.scad` remains historical reference;
its 475 measured rear layers are no longer loaded by the production model.
Dimensions below are millimetres before the final `size_scale`; X/Z form the
front sketch and Y is depth. Recovered feature relationships are inferred
design intent, rather than an original manufacturer's CAD specification.

## Editable features

- Central carrier: R8 boss at Y=-5..-2, circular shaft bore, and opposed
  bayonet entry windows at Y=-4..-2. Two R4.6/R2.6 annular sectors extend
  from Y=-2 to the rear. Changing `shaft_stem_diameter` radially offsets their
  vertices by half the diameter change, preserving the previous contract.
  `disk_pitch` controls the rear endpoint, `13+2*(disk_pitch-5)`.
- Latch fork: R5.2 outer capsule joining centres X=-66/-34, with an R4.2
  grip opening and two right arms. The opening moves with the left wall
  and retains the existing fit compensation.
- Latch rails: paired compact functional profiles, R2 rounded ends, an R1
  top cap, and an R1.9 concave internal fillet. `link_web_thickness` retains
  its mapped reinforcement and fade near X=-20..-18. The reinforced left
  end applies that mapping after the R2 trim. Sixteen analytic arc intervals
  approximate this one feature. The scaled R1 cap uses 32 analytic intervals
  to retain the radial fit compensation at its inner top corner. These
  constructions do not replay measured mesh layers.
- Hinge receivers: paired C-sections with their socket slots, solid rear
  cheeks and R2 end relief. Height, socket root thickness and scaled fit
  compensation use the existing mounting transformation.
- Cover supports: straight ledges, retaining tabs, 45-degree lead-ins and
  the measured 35-degree angled supports. The lower ledge and tab share
  one continuous prism.

The panel, marker, mounting datums and parameter ranges remain in their
existing owners. The scaled panel's leading chamfer now hulls directly into
the full backing slab, avoiding a redundant 0.001 mm belt. Circle arcs share
one angular grid with the panel bore. Boolean overlaps of 0.001 mm and, at the
reinforced R2 end, up to 0.005 mm prevent numerical tangent seams. They are
bounded construction adjustments, not changes to the fit-gap parameters.

## Reproduction and acceptance

Use the project Python runtime with `requirements.txt`, OpenSCAD 2026.09.29,
Manifold, `curve_segments=128`, and the unchanged 0.005 mm door export tolerance:

```powershell
$env:MINI_VAULT_OPENSCAD='<openscad.com>'
& '<project-python>' -m unittest tests.test_door_features tests.test_native_door -v
& '<project-python>' work/verify-door-features.py --openscad '<openscad.com>' --output work/door-feature-verified
```

The first command covers source independence, direct face budget, indexed and
final zero-area triangles, all five saved presets, shaft bore, latch rail,
rear axial coupling, reference geometry and marker dimensions. The full
comparison additionally needs the local hash-verified old-source snapshot
`work/backup/door-feature-20261017/`, reference meshes and existing print-kit
meshes. Those local inputs are not distributed in a public source clone.

The verifier leaves delivered kits untouched and writes its reports under
`--output`. It compares all five presets, minimum depth, R11 door corners and
modified shaft/pitch, and combined scale/reinforcement against the old builder. Existing geometry gates remain:
bounds 0.1 mm, two-way seeded surface p95 0.1 mm / maximum 0.25 mm, and
functional contours 0.1 mm. Indexed contours are checked on both sides of
Y=0: the old simplified STL bridges that sharp discontinuity, so its nearby
printed-mesh contour errors are retained as diagnostics. Printed contours
away from that seam still participate in acceptance.

For both active print presets, rigid motion comparisons check individual
door/housing and hinge-leaf pairs over 361 door poses, two sliders over 121
positions, and shaft/dial/knob plus three disks and their three fasteners over
180 rotations. Static pairs are also checked. A contact increase exceeding
0.001 mm3 after the existing sliver classifier fails acceptance. Report hashes
bind the source, snapshot, preset, helper scripts and actual compared meshes.

These sampled checks establish neither physical fit nor force, durability,
warping, slicing or an exhaustive independent self-intersection audit.
Existing slicer 3MF projects and printer profiles require separate updates.

## Checkpoint: 2026-10-17

With the same curve segmentation and export tolerance:

- Default: 286,628 -> 6,862 indexed faces; 19,172 -> 4,854 STL triangles.
- 200 - scale 1: 275,712 -> 6,980 indexed faces; 19,614 -> 5,180 STL triangles.
- 220 - scale 1.5: 280,494 -> 7,342 indexed faces; 26,112 -> 6,216 STL triangles.
- All nine geometry cases passed, including the combined scaled/reinforced case.
  Indexed and final STL exact zero-area face counts were zero in every case.
- Six focused unit tests passed, including saved presets and the combined case.
- Maximum sampled surface error was 0.00974 mm for 200 and 0.07571 mm for
  scaled 220. Maximum tested indexed contour error was 0.01906 / 0.07742 mm.
  These are sampled observations, not a complete Hausdorff bound.

Both active print presets passed 2,966 pairwise static/motion comparisons each
with no increased significant contact. Both 22-part print kits were regenerated
and all 44 individual STL files were read back against their exact source
triangles and placements. Only the door source STL changed in each kit;
the other 21 source STL hashes stayed identical. Current local evidence is
bound by `work/door-feature-verified/final-acceptance.json`. Slicer 3MF projects
and previously published archives remain at their earlier checkpoints.
