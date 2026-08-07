// =============================================================================
// technical_drawing.scad -- 2D technical drawings for the docs site
// =============================================================================
//
// Renders orthographic projections of the canonical Wattplot assembly
// at three view angles. Exports to PNG for the docs engineering
// section. The camera is positioned via OpenSCAD's --camera flag
// at the make / shell level (this file doesn't bake in a view).
//
// Outputs:
//   docs/renders/wattplot_top_view.png
//   docs/renders/wattplot_side_view.png
//   docs/renders/wattplot_front_view.png
//
// Render:
//   make scad-tech-drawings
//   or (from the repo root):
//     openscad --camera=0,20,0,0,0,0,200 \
//       --projection=o --imgsize=2000,1500 \
//       -o out_top.png models/openscad/technical_drawing.scad
//     openscad --camera=0,0,-20,0,0,90,200 \
//       --projection=o --imgsize=2000,1500 \
//       -o out_side.png models/openscad/technical_drawing.scad
//     openscad --camera=20,0,0,0,90,0,200 \
//       --projection=o --imgsize=2000,1500 \
//       -o out_front.png models/openscad/technical_drawing.scad
//
// The projections are pure (no perspective foreshortening) so
// the docs site can use them as engineering drawings. The view
// is selected at render time by the --camera flag; this file just
// renders the same model in whatever view the camera is pointed
// at.

include <wattplot_params.scad>
use <parts/bed.scad>
use <parts/posts.scad>
use <parts/hinges.scad>
use <parts/panel.scad>
use <parts/frame.scad>
use <parts/actuator.scad>

col_bed_skin   = [0.78, 0.55, 0.35];
col_bed_cleat  = [0.85, 0.65, 0.45];
col_skid       = [0.55, 0.40, 0.30];
col_soil       = [0.40, 0.25, 0.15];
col_post       = [0.70, 0.55, 0.40];
col_frame      = [0.90, 0.90, 0.88];
col_panel      = [0.20, 0.30, 0.55];
col_actuator   = [0.40, 0.40, 0.45];
col_hinge      = [0.60, 0.60, 0.65];

$fn = 32;  // smaller $fn for tech drawings (faster, less detail)

bed_assembly();
posts_assembly();
hinges_assembly();
actuator_assembly();
frame_assembly();
panel_assembly();