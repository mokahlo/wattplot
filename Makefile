# Wattplot OpenSCAD model
#
# Renders the canonical wattplot.scad to an STL for the booth
# preview, the docs site 3D viewer, or 3D printing.
#
# See wattplot.scad for the design and wattplot_params.scad for the
# parameters (a mirror of wattplot_params.py at the repo root).
#
# Render all presets:
#   make scad-stl
# Render one preset at 35 deg:
#   openscad -o wattplot_longi_620W.stl models/openscad/wattplot.scad
# Render a different panel preset:
#   openscad -D 'panel_L_in=65.0' -D 'panel_W_in=39.0' \
#            -D 'panel_wattage=250' \
#            -o wattplot_60cell.stl models/openscad/wattplot.scad
# (manual override; the per-preset .scad files in presets/ wrap
# this for repeatable rendering)

OPENSCAD ?= openscad
OUT_DIR ?= renders
PRESET_DIR := presets
COMMON := --enable=fast-csg --enable=sort-stl

# Per-preset render targets. Each entry: <preset_name>:<L>:<W>:<Wattage>:<tilt>:<output>
# Keep in sync with wattplot_params.py PANEL_PRESETS.
PRESETS := longi_620W \
           residential_60cell \
           residential_72cell \
           commercial_96cell \
           large_format_1m65

# LONGi Hi-MO X10 620 W (default)
LONGI_L     = 97.0
LONGI_W     = 44.6
LONGI_WATT  = 620

# Residential 60-cell (e.g., Kyocera KD215, Sanyo HIT)
RES60_L     = 65.0
RES60_W     = 39.0
RES60_WATT  = 250

# Residential 72-cell (e.g., Canadian Solar CS6K-300)
RES72_L     = 77.0
RES72_W     = 39.0
RES72_WATT  = 300

# Commercial 96-cell (e.g., SunPower SPR-400)
COM96_L     = 65.0
COM96_W     = 41.0
COM96_WATT  = 400

# Large-format 1.65 m (e.g., REC Alpha 400)
LARGE_L     = 65.0
LARGE_W     = 41.0
LARGE_WATT  = 400

.PHONY: all scad scad-stl scad-stl-all scad-preview scad-tech-drawings scad-clean

all: scad-stl

# Quick render: just the canonical LONGi 620W model at $fn=16
# (fast preview, 200-500 KB STL, blocky curves).
scad: $(OUT_DIR)/wattplot.scad-preview.png

# Full STLs for the booth and 3D viewer ($fn=64 default).
scad-stl: $(addprefix $(OUT_DIR)/wattplot_,longi_620W.stl)

# All 5 panel presets
scad-stl-all: $(addprefix $(OUT_DIR)/wattplot_,$(addsuffix .stl,$(PRESETS)))

# Cheap preview PNGs for the docs site
scad-preview: $(addprefix $(OUT_DIR)/wattplot.scad-,$(addsuffix .png,$(PRESETS)))

# 2D technical drawings (top / side / front orthographic projections)
# for the docs engineering section. Renders directly to PNG with
# the camera angle set per-view.
scad-tech-drawings: $(addprefix $(OUT_DIR)/wattplot_,$(addsuffix .png,top_view side_view front_view))

scad-clean:
	rm -f $(OUT_DIR)/wattplot*.stl $(OUT_DIR)/wattplot*.png

# ----------------------------------------------------------------------------
# Render recipes
# ----------------------------------------------------------------------------
# Each preset is rendered with `-D` overrides for panel dimensions.
# OpenSCAD doesn't have a config file equivalent, so we use -D
# for the per-preset overrides. The .scad file uses
# `include <wattplot_params.scad>` so the override takes effect.

$(OUT_DIR)/wattplot_%.stl: models/openscad/wattplot.scad | $(OUT_DIR)
	@echo "  render  $(notdir $@)"
	@case "$*" in \
	  longi_620W)         OPTS="-D panel_L_in=$(LONGI_L) -D panel_W_in=$(LONGI_W) -D panel_wattage=$(LONGI_WATT)" ;; \
	  residential_60cell)  OPTS="-D panel_L_in=$(RES60_L) -D panel_W_in=$(RES60_W) -D panel_wattage=$(RES60_WATT)" ;; \
	  residential_72cell)  OPTS="-D panel_L_in=$(RES72_L) -D panel_W_in=$(RES72_W) -D panel_wattage=$(RES72_WATT)" ;; \
	  commercial_96cell)   OPTS="-D panel_L_in=$(COM96_L) -D panel_W_in=$(COM96_W) -D panel_wattage=$(COM96_WATT)" ;; \
	  large_format_1m65)   OPTS="-D panel_L_in=$(LARGE_L) -D panel_W_in=$(LARGE_W) -D panel_wattage=$(LARGE_WATT)" ;; \
	  *) echo "unknown preset: $*" >&2; exit 2 ;; \
	esac
	$(OPENSCAD) $(COMMON) $$OPTS -o $@ models/openscad/wattplot.scad

# Preview PNG (camera above and to the south, looking north-east).
# $fn=16 for speed; the docs site shows the high-$fn STL anyway.
$(OUT_DIR)/wattplot.scad-%.png: models/openscad/wattplot.scad | $(OUT_DIR)
	@echo "  preview  $(notdir $@)"
	@case "$*" in \
	  longi_620W)         OPTS="-D panel_L_in=$(LONGI_L) -D panel_W_in=$(LONGI_W) -D panel_wattage=$(LONGI_WATT)" ;; \
	  residential_60cell)  OPTS="-D panel_L_in=$(RES60_L) -D panel_W_in=$(RES60_W) -D panel_wattage=$(RES60_WATT)" ;; \
	  residential_72cell)  OPTS="-D panel_L_in=$(RES72_L) -D panel_W_in=$(RES72_W) -D panel_wattage=$(RES72_WATT)" ;; \
	  commercial_96cell)   OPTS="-D panel_L_in=$(COM96_L) -D panel_W_in=$(COM96_W) -D panel_wattage=$(COM96_WATT)" ;; \
	  large_format_1m65)   OPTS="-D panel_L_in=$(LARGE_L) -D panel_W_in=$(LARGE_W) -D panel_wattage=$(LARGE_WATT)" ;; \
	  *) echo "unknown preset: $*" >&2; exit 2 ;; \
	esac
	$(OPENSCAD) $(COMMON) --camera=12,-22,11,60,0,40,80 \
		--imgsize=1200,800 \
		--colorscheme=Tomorrow \
		--view=axes \
		--projection=p \
		$$OPTS \
		-o $@ models/openscad/wattplot.scad

# 2D technical drawings. Each view is a different camera angle.
# Camera args: eyex,eyey,eyez,centerx,centery,centerz,distance
#   top_view:    looking down (0, 20, 0)
#   side_view:   looking from south (0, 0, -20)
#   front_view:  looking from east (20, 0, 0)
$(OUT_DIR)/wattplot_%.png: models/openscad/technical_drawing.scad | $(OUT_DIR)
	@echo "  drawing  $(notdir $@)"
	@case "$*" in \
	  top_view)    CAM="--camera=0,15,0,0,0,0,40" ;; \
	  side_view)   CAM="--camera=0,5,-15,0,30,0,40" ;; \
	  front_view)  CAM="--camera=15,5,0,0,30,0,40" ;; \
	  *) echo "unknown view: $*" >&2; exit 2 ;; \
	esac
	$(OPENSCAD) --projection=o --imgsize=2000,1200 \
		--colorscheme=Starnight \
		--view=axes \
		$$CAM \
		-o $@ models/openscad/technical_drawing.scad

$(OUT_DIR):
	mkdir -p $@

.PHONY: help
help:
	@echo "make targets:"
	@echo "  scad          -- render the canonical LONGi 620W preview PNG"
	@echo "  scad-stl      -- render the LONGi 620W STL (default)"
	@echo "  scad-stl-all  -- render all 5 panel presets"
	@echo "  scad-preview  -- render preview PNGs for the docs site"
	@echo "  scad-clean    -- remove generated STL/PNG files"
	@echo ""
	@echo "Manual:"
	@echo "  openscad -o out.stl models/openscad/wattplot.scad"