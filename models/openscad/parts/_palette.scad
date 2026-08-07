// =============================================================================
// parts/_palette.scad -- shared color palette (used by all part modules)
// =============================================================================
//
// The canonical wattplot.scad defines its own colors inline. The
// per-part modules also define defaults so they can be rendered
// standalone. This file is the source of truth if a future
// "tweak palette" refactor wants to centralize.

col_bed_skin_palette  = [0.78, 0.55, 0.35];   // cedar
col_bed_cleat_palette = [0.85, 0.65, 0.45];
col_skid_palette       = [0.55, 0.40, 0.30];   // PT DF
col_soil_palette       = [0.40, 0.25, 0.15];   // wet loam
col_post_palette       = [0.70, 0.55, 0.40];
col_frame_palette      = [0.90, 0.90, 0.88];   // 2x6 painted
col_panel_palette      = [0.20, 0.30, 0.55];   // LONGi blue
col_actuator_palette   = [0.40, 0.40, 0.45];
col_hinge_palette      = [0.60, 0.60, 0.65];