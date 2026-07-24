"""
Wattplot v2 — Interactive FreeCAD build walkthrough.

Builds the assembly phase by phase, with each phase in its own group.
A FreeCAD task panel lets the user step through the build with a slider
(or Prev/Next/Show All buttons), watching the assembly grow.

Two modes:

1. GUI mode (FreeCAD desktop app, NOT freecadcmd):
   - Open FreeCAD
   - Tools menu > Macros > Run macro > select this file
   - The assembly builds, a task panel appears with a slider
   - Drag the slider to advance/reverse through the build phases

2. Headless mode (freecadcmd):
   - Builds the same phase groups
   - Exports one STL per phase for booth images / documentation
   - Use: freecadcmd -c "exec(open('assemble_walkthrough.py').read())"

The script is parametric — it reads the current wattplot_params state,
so any panel preset (or custom spec) works automatically.

Adapted from models/freecad/assemble.py.
"""
import sys
import os
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Running via exec() in freecadcmd -c; fall back to cwd
    HERE = os.path.dirname(os.path.abspath("models/freecad/assemble_walkthrough.py"))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

import FreeCAD as App
import Part
import Mesh
import MeshPart

import wattplot_params as P
from models.freecad.parts.bed_wall import make_bed_long_wall, make_bed_short_wall
from models.freecad.parts.skid import make_skids
from models.freecad.parts.frame import make_frame_assembly
from models.freecad.parts.panel import make_panel
from models.freecad.parts.hinge import make_all_hinges
from models.freecad.parts.panel_clamp import make_all_clamps
from models.freecad.parts.actuator_mount import make_actuator_mount

OUTDIR_MODELS = os.path.join(ROOT, "models")


# ---- color helpers ---------------------------------------------------------

COLORS = {
    "wood":   (0.55, 0.40, 0.25, 1.0),
    "frame":  (0.45, 0.32, 0.20, 1.0),
    "metal":  (0.50, 0.50, 0.55, 1.0),
    "panel":  (0.10, 0.15, 0.30, 0.85),
    "clamp":  (0.75, 0.75, 0.78, 1.0),
    "skid":   (0.45, 0.32, 0.20, 1.0),
}


def set_color(obj, rgba):
    if obj.ViewObject is None:
        return
    try:
        obj.ViewObject.ShapeColor = rgba[:3]
        obj.ViewObject.Transparency = int((1 - rgba[3]) * 100)
    except Exception:
        pass


# ---- phase definitions -----------------------------------------------------

# Each phase has:
#   - name (display)
#   - description (one-line, shown in the task panel)
#   - list of (part_key, color_key) pairs to build (mapped to PART_BUILDERS below)
#   - "info_only" flag: True for phases that have no 3D parts (pre-build, wiring, done)
#     These are shown in the task panel but not exported as STLs.

PHASES = [
    {
        "name": "Pre-build",
        "desc": "Order lumber, hardware, panel. No 3D parts yet.",
        "parts": [],
        "info_only": True,
    },
    {
        "name": "Phase 1: Bed",
        "desc": "Cut half-lap notches. Assemble the bed box. Attach skids.",
        "parts": [("bed_walls", "wood"), ("skids", "skid")],
    },
    {
        "name": "Phase 2: Frame",
        "desc": "Build the 2x6 frame rectangle. Add the diagonal brace.",
        "parts": [("frame", "frame")],
    },
    {
        "name": "Phase 3: Hinges",
        "desc": "Mount 4 butt hinges on the bed's south wall. Insert the continuous rod.",
        "parts": [("hinges", "metal")],
    },
    {
        "name": "Phase 4: Panel + clamps",
        "desc": "Mount the panel on the frame using 6 mid-clamps.",
        "parts": [("panel", "panel"), ("clamps", "clamp")],
    },
    {
        "name": "Phase 5: Actuator",
        "desc": "Mount the actuator between the bed's north wall and the panel's underside.",
        "parts": [("actuator", "metal")],
    },
    {
        "name": "Phase 6: Wiring",
        "desc": "Wire panel to MPPT to battery. Wire ESP32 controller + sensors. No 3D parts.",
        "parts": [],
        "info_only": True,
    },
    {
        "name": "Phase 7: Done",
        "desc": "Full assembly complete. Plant tomatoes, fill with soil, run the dashboard.",
        "parts": [],
        "info_only": True,
        "final": True,  # show all parts visible at this phase
    },
]


PART_BUILDERS = {
    "bed_walls": lambda doc: [
        make_bed_long_wall(doc, "north"),
        make_bed_long_wall(doc, "south"),
        make_bed_short_wall(doc, "west"),
        make_bed_short_wall(doc, "east"),
    ],
    "skids": lambda doc: [make_skids(doc)],
    "frame": lambda doc: [make_frame_assembly(doc)[0]],
    "panel": lambda doc: [make_panel(doc)],
    "hinges": lambda doc: make_all_hinges(doc)[1],
    "clamps": lambda doc: make_all_clamps(doc)[1],
    "actuator": lambda doc: [make_actuator_mount(doc)],
}


# ---- build all phases into one document ------------------------------------

def build_all_phases(doc=None):
    """Build the full assembly as phase groups. Returns (doc, phase_groups)."""
    if doc is None:
        doc = App.newDocument("Wattplot_Walkthrough")
    doc.recompute()

    panel_L = P.PANEL["L_in"]
    panel_W = P.PANEL["W_in"]
    panel_W_rating = int(P.PANEL["wattage"])
    print(f"[walkthrough] Building for panel: {panel_L}\" × {panel_W}\", "
          f"{panel_W_rating}W")
    print(f"[walkthrough] Bed: {P.BED['outer_L_in']}\" × {P.BED['outer_W_in']}\"")

    phase_groups = {}
    for phase in PHASES:
        # Slug for the group name (FreeCAD group names should be valid identifiers)
        slug = phase["name"].lower()
        for ch in " :+()/":
            slug = slug.replace(ch, "_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        slug = slug.strip("_")
        group = doc.addObject("App::DocumentObjectGroup", slug)
        group.Label = phase["name"]
        # Build the parts for this phase
        for part_key, color_key in phase["parts"]:
            if part_key in PART_BUILDERS:
                for obj in PART_BUILDERS[part_key](doc):
                    group.addObject(obj)
                    if color_key in COLORS:
                        set_color(obj, COLORS[color_key])
        phase_groups[phase["name"]] = group

    print(f"[walkthrough] {len(phase_groups)} phase groups created "
          f"({sum(1 for p in PHASES if not p.get('info_only'))} with 3D parts)")
    return doc, phase_groups


def set_visibility(phase_groups, phase_index):
    """Show only the parts in phases 0..phase_index (cumulative).

    Handles 'final' phases by showing all parts visible.
    """
    names = list(phase_groups.keys())
    phase_def = PHASES[phase_index]
    is_final = phase_def.get("final", False)

    if is_final:
        show_all(phase_groups)
        return

    for i, (name, group) in enumerate(phase_groups.items()):
        phase_def_i = PHASES[i] if i < len(PHASES) else {}
        if phase_def_i.get("info_only", False):
            # info-only phases: visibility depends on whether we've reached
            # them in the timeline
            visible = (i <= phase_index)
        else:
            # 3D phase: parts visible if we've reached this phase
            visible = (i <= phase_index)
        for obj in group.Group:
            if obj.ViewObject is not None:
                try:
                    obj.ViewObject.Visibility = visible
                except Exception:
                    pass


def show_all(phase_groups):
    """Make every part visible."""
    for group in phase_groups.values():
        for obj in group.Group:
            if obj.ViewObject is not None:
                try:
                    obj.ViewObject.Visibility = True
                except Exception:
                    pass


def export_phase_stls(phase_groups, prefix="wattplot_walkthrough"):
    """Export one STL per phase with 3D parts (skip info-only phases)."""
    for i, (name, group) in enumerate(phase_groups.items()):
        phase_def = PHASES[i] if i < len(PHASES) else {}
        if phase_def.get("info_only", False):
            print(f"[walkthrough] {name}: info-only, no STL")
            continue
        # Set cumulative visibility up to this phase
        set_visibility(phase_groups, i)
        # Collect shapes from all earlier 3D phases
        shapes = []
        for j in range(i + 1):
            if j < len(PHASES) and PHASES[j].get("info_only", False):
                continue
            for obj in phase_groups[list(phase_groups.keys())[j]].Group:
                if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():
                    shapes.append(obj.Shape)
        if not shapes:
            print(f"[walkthrough] {name}: no shapes to export")
            continue
        compound = Part.makeCompound(shapes)
        mesh = MeshPart.meshFromShape(compound,
                                      LinearDeflection=1.0,
                                      AngularDeflection=0.5,
                                      Relative=False)
        # Slug for the filename
        slug = name.lower()
        for ch in " :+()/":
            slug = slug.replace(ch, "_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        slug = slug.strip("_")
        out_path = os.path.join(OUTDIR_MODELS, f"{prefix}_{slug}.stl")
        mesh.write(out_path)
        print(f"[walkthrough] {name}: {out_path}")
    show_all(phase_groups)


# ---- GUI: FreeCAD task panel ----------------------------------------------

def show_gui_walkthrough(phase_groups):
    """Show a task panel in FreeCAD with a slider for stepping through phases.

    Requires the FreeCAD GUI to be running (NOT freecadcmd).
    """
    try:
        import FreeCADGui as Gui
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        print("[walkthrough] PySide2 not available — run from FreeCAD GUI, not freecadcmd")
        return

    phase_names = list(phase_groups.keys())
    n_phases = len(phase_names)
    descriptions = {p["name"]: p["desc"] for p in PHASES}

    class WalkthroughPanel:
        """Minimal TaskPanel class. Qt widgets are created on demand."""

        def __init__(self):
            self.form = QtWidgets.QWidget()
            self.form.setWindowTitle("Wattplot Build Walkthrough")
            self.current_phase = 0
            layout = QtWidgets.QVBoxLayout()

            # Title
            title = QtWidgets.QLabel(f"<h2>Wattplot Build Walkthrough</h2>")
            layout.addWidget(title)
            panel_info = QtWidgets.QLabel(
                f"<b>Panel:</b> {P.PANEL['L_in']}\" × {P.PANEL['W_in']}\" "
                f"({P.PANEL['L_in']/12:.2f} × {P.PANEL['W_in']/12:.2f} ft), "
                f"{int(P.PANEL['wattage'])} W<br>"
                f"<b>Bed:</b> {P.BED['outer_L_in']}\" × {P.BED['outer_W_in']}\" "
                f"({P.BED['outer_L_in']/12:.2f} × {P.BED['outer_W_in']/12:.2f} ft)"
            )
            layout.addWidget(panel_info)

            # Phase info label
            self.info_label = QtWidgets.QLabel()
            self.info_label.setWordWrap(True)
            self.info_label.setStyleSheet("padding: 8px; background: #2a2a2a; border-radius: 4px;")
            layout.addWidget(self.info_label)

            # Slider
            self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.slider.setMinimum(0)
            self.slider.setMaximum(n_phases - 1)
            self.slider.setValue(0)
            self.slider.setTickInterval(1)
            self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            self.slider.valueChanged.connect(self._on_slider)
            layout.addWidget(self.slider)

            # Buttons
            btn_row = QtWidgets.QHBoxLayout()
            self.prev_btn = QtWidgets.QPushButton("◀ Previous")
            self.prev_btn.clicked.connect(self._on_prev)
            self.show_all_btn = QtWidgets.QPushButton("Show all")
            self.show_all_btn.clicked.connect(self._on_show_all)
            self.next_btn = QtWidgets.QPushButton("Next ▶")
            self.next_btn.clicked.connect(self._on_next)
            btn_row.addWidget(self.prev_btn)
            btn_row.addWidget(self.show_all_btn)
            btn_row.addWidget(self.next_btn)
            layout.addLayout(btn_row)

            # Phase jump buttons (compact)
            jump_row = QtWidgets.QHBoxLayout()
            self.jump_buttons = []
            # Friendly short labels for each phase
            short_labels = {
                "Pre-build": "Pre",
                "Phase 1: Bed": "P1 Bed",
                "Phase 2: Frame": "P2 Frame",
                "Phase 3: Hinges": "P3 Hinge",
                "Phase 4: Panel + clamps": "P4 Panel",
                "Phase 5: Actuator": "P5 Act",
                "Phase 6: Wiring": "P6 Wire",
                "Phase 7: Done": "Done",
            }
            for i, name in enumerate(phase_names):
                btn = QtWidgets.QPushButton(short_labels.get(name, name))
                btn.setToolTip(name)
                btn.clicked.connect(lambda checked=False, idx=i: self._on_jump(idx))
                jump_row.addWidget(btn)
                self.jump_buttons.append(btn)
            layout.addLayout(jump_row)

            self.form.setLayout(layout)
            self._show_phase(0)

        def _on_slider(self, value):
            self._show_phase(value)

        def _on_prev(self):
            if self.current_phase > 0:
                self.current_phase -= 1
                self.slider.setValue(self.current_phase)

        def _on_next(self):
            if self.current_phase < n_phases - 1:
                self.current_phase += 1
                self.slider.setValue(self.current_phase)

        def _on_jump(self, idx):
            self.slider.setValue(idx)

        def _on_show_all(self):
            show_all(phase_groups)
            self.current_phase = n_phases - 1
            self.slider.setValue(self.current_phase)

        def _show_phase(self, index):
            self.current_phase = index
            set_visibility(phase_groups, index)
            name = phase_names[index]
            self.info_label.setText(f"<b>{name}</b><br>{descriptions.get(name, '')}")
            # Update button highlight (visual feedback)
            for i, btn in enumerate(self.jump_buttons):
                btn.setDefault(i == index)

        def getStandardButtons(self):
            return int(QtWidgets.QDialogButtonBox.Close)

        def accept(self):
            Gui.Control.closeDialog()

        def reject(self):
            Gui.Control.closeDialog()

    panel = WalkthroughPanel()
    Gui.Control.showDialog(panel)


# ---- main ------------------------------------------------------------------

def main():
    """Build all phases. If GUI is available, show the task panel. Else
    just build and export STLs (for headless use)."""
    doc, phase_groups = build_all_phases()

    # Detect GUI mode
    has_gui = False
    try:
        import FreeCADGui as Gui
        Gui.ActiveDocument  # accessing this raises if no GUI
        has_gui = True
    except Exception:
        has_gui = False

    if has_gui:
        show_gui_walkthrough(phase_groups)
        print("[walkthrough] Task panel opened. Use the slider to step through phases.")
    else:
        print("[walkthrough] Headless mode: exporting one STL per phase")
        export_phase_stls(phase_groups)
        print("[walkthrough] Done.")


if __name__ == "__main__":
    main()
