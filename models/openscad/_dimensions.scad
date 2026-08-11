// =============================================================================
// _dimensions.scad -- engineering-drawing dimension lines for the
// technical_drawing.scad output.
// =============================================================================
//
// A small library that draws standard architectural-drawing dim
// lines + arrows + text labels. Use the provided dim_* modules
// from technical_drawing.scad; or build your own at lower level
// with witness_line(), dim_arrow(), dim_text().
//
// Coordinate system: dim_* functions place elements in 2D (the
// projection plane). All units are in inches to match the rest
// of the model.
//
// Default style:
//   - witness lines: 0.02" thick, extend 0.3" beyond the feature
//   - dimension line: 0.02" thick, with arrowheads at each end
//   - text: 0.2" tall, centered above the line
//   - color: black (0, 0, 0); the technical_drawing Starnight
//     colorscheme renders text in a contrast color
//
// Usage:
//   dim_horizontal(start=-48, end=48, y=14, label="96\" bed length");
//   dim_vertical(start=0, end=14, x=-50, label="14\" wall height");
//
// The arrows are small filled triangles, scaled for legibility
// at 2000x1200 image size (the tech drawing's default render).

include <wattplot_params.scad>

// Witness line: a short line from the feature to the dim line.
module witness_line(x1, y1, x2, y2, w=0.02) {
    color([0, 0, 0])
    translate([x1, y1, 0])
        cube([x2 - x1, y2 - y1, w], center=false);
}

// Filled arrowhead at (x, y) pointing in (+x, -x) direction.
// size is the half-length; thickness is 0.05" for legibility.
module arrow_head(x, y, dir, size=0.3, thick=0.04) {
    color([0, 0, 0])
    translate([x, y, 0])
    if (dir > 0) {
        // Arrow pointing in +x direction
        polygon(points=[
            [0, 0],
            [-size, thick/2],
            [-size * 0.7, thick/2],
            [-size * 0.7, -thick/2],
            [-size, -thick/2],
        ]);
    } else {
        // Arrow pointing in -x direction
        polygon(points=[
            [0, 0],
            [size, thick/2],
            [size * 0.7, thick/2],
            [size * 0.7, -thick/2],
            [size, -thick/2],
        ]);
    }
}

// Dimension arrow line with arrowheads at both ends.
// p1 and p2 are [x, y] endpoints.
module dim_arrow(p1, p2, w=0.02) {
    color([0, 0, 0])
    translate([p1[0], p1[1], 0])
        cube([p2[0] - p1[0], p2[1] - p1[1], w], center=false);
    // Arrowheads: at the line's ends, perpendicular to the
    // direction. Compute direction from dx, dy.
    dx = p2[0] - p1[0];
    dy = p2[1] - p1[1];
    L = sqrt(dx*dx + dy*dy);
    if (L > 0) {
        ux = dx / L;
        uy = dy / L;
        size = 0.3;
        thick = 0.04;
        // Arrow at p1 pointing back toward p2
        translate([p1[0], p1[1], 0])
            rotate(atan2(uy, ux) - 90)
                polygon(points=[
                    [size, 0],
                    [-size * 0.7, thick],
                    [-size * 0.7, -thick],
                ]);
        // Arrow at p2 pointing back toward p1
        translate([p2[0], p2[1], 0])
            rotate(atan2(-uy, -ux) - 90)
                polygon(points=[
                    [size, 0],
                    [-size * 0.7, thick],
                    [-size * 0.7, -thick],
                ]);
    }
}

// Dimension text. halign centers above the line; valign=baseline
// means the bottom of the text is on the line.
module dim_text(x, y, label, size=0.35, halign="center", valign="bottom") {
    color([0, 0, 0])
    translate([x, y, 0])
        text(label, size=size, halign=halign, valign=valign, font="Liberation Sans");
}

// Horizontal dimension: two features at (x_start, y_feat) and
// (x_end, y_feat), label centered above the dim line. y_label
// is the y of the text; the dim line sits at y_label - 0.3.
module dim_horizontal(x_start, x_end, y_feat, label, ext=0.4) {
    // Witness lines from each feature down to the dim line.
    y_dim = y_feat - ext;
    witness_line(x_start, y_feat, x_start, y_dim + 0.05);
    witness_line(x_end, y_feat, x_end, y_dim + 0.05);
    // Dim line
    dim_arrow([x_start, y_dim], [x_end, y_dim]);
    // Text above the line
    dim_text((x_start + x_end) / 2, y_dim + 0.3, label);
}

// Vertical dimension: features at (x_feat, y_start) and
// (x_feat, y_end).
module dim_vertical(x_feat, y_start, y_end, label, ext=0.4) {
    x_dim = x_feat - ext;
    witness_line(x_feat, y_start, x_dim + 0.05, y_start);
    witness_line(x_feat, y_end, x_dim + 0.05, y_end);
    dim_arrow([x_dim, y_start], [x_dim, y_end]);
    dim_text(x_dim - 0.3, (y_start + y_end) / 2, label, halign="right", valign="center");
}

// Arc for showing the panel tilt angle.
module dim_angle_arc(cx, cy, radius, start_deg, end_deg) {
    steps = 16;
    step_deg = (end_deg - start_deg) / steps;
    color([0, 0, 0])
    for (i = [0:steps-1]) {
        a1 = start_deg + i * step_deg;
        a2 = a1 + step_deg;
        p1 = [cx + radius * cos(a1), cy + radius * sin(a1)];
        p2 = [cx + radius * cos(a2), cy + radius * sin(a2)];
        translate([p1[0], p1[1], 0])
            cube([p2[0] - p1[0], p2[1] - p1[1], 0.02], center=false);
    }
}