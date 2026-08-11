#!/usr/bin/env bash
# Render the canonical wattplot.scad (and any preset variants) to
# STL files. Convenience wrapper around the Makefile for users
# without `make` or who want a one-liner.
#
# Usage:
#   tools/render_openscad.sh                  # default: LONGi 620W only
#   tools/render_openscad.sh all              # all 5 panel presets
#   tools/render_openscad.sh preview          # PNG previews (faster)
#   tools/render_openscad.sh clean            # remove generated files
#
# Requires OpenSCAD 2021.01+ on PATH (apt install openscad,
# brew install openscad, choco install openscad).

set -euo pipefail

OPENSCAD="${OPENSCAD:-openscad}"
OUT_DIR="${OUT_DIR:-renders}"
COMMON=(--enable=fast-csg --enable=sort-stl)

# Per-preset dimensions (kept in sync with wattplot_params.py
# PANEL_PRESETS).
declare -A PRESETS=(
  [longi_620W]='97.0 44.6 620'
  [residential_60cell]='65.0 39.0 250'
  [residential_72cell]='77.0 39.0 300'
  [commercial_96cell]='65.0 41.0 400'
  [large_format_1m65]='65.0 41.0 400'
)

mkdir -p "$OUT_DIR"

render_one() {
  local preset="$1"
  local dims=(${PRESETS[$preset]})
  local L="${dims[0]}" W="${dims[1]}" WATT="${dims[2]}"
  local out="$OUT_DIR/wattplot_${preset}.stl"
  echo "  render  $out  (L=$L W=$W ${WATT}W)"
  "$OPENSCAD" "${COMMON[@]}" \
    -D "panel_L_in=$L" -D "panel_W_in=$W" -D "panel_wattage=$WATT" \
    -o "$out" models/openscad/wattplot.scad
}

render_preview() {
  local preset="$1"
  local dims=(${PRESETS[$preset]})
  local L="${dims[0]}" W="${dims[1]}" WATT="${dims[2]}"
  local out="$OUT_DIR/wattplot.scad-${preset}.png"
  echo "  preview  $out  (L=$L W=$W ${WATT}W)"
  "$OPENSCAD" "${COMMON[@]}" \
    --camera=12,-22,11,60,0,40,80 \
    --imgsize=1200,800 \
    --colorscheme=Tomorrow \
    --view=axes --projection=p \
    -D "panel_L_in=$L" -D "panel_W_in=$W" -D "panel_wattage=$WATT" \
    -o "$out" models/openscad/wattplot.scad
}

# Confirm OpenSCAD is available.
if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
  echo "error: $OPENSCAD not found on PATH" >&2
  echo "  install with: apt install openscad / brew install openscad / choco install openscad" >&2
  exit 1
fi

case "${1:-default}" in
  default|"")
    render_one longi_620W
    ;;
  all)
    for preset in "${!PRESETS[@]}"; do
      render_one "$preset"
    done
    ;;
  preview)
    for preset in "${!PRESETS[@]}"; do
      render_preview "$preset"
    done
    ;;
  clean)
    rm -f "$OUT_DIR"/wattplot*.stl "$OUT_DIR"/wattplot*.png
    echo "cleaned $OUT_DIR/wattplot*.{stl,png}"
    ;;
  *)
    echo "usage: $0 [default|all|preview|clean]" >&2
    exit 2
    ;;
esac