import os
import math
import subprocess
from typing import Dict, Any
from pathlib import Path

OUTPUT_DIR = os.path.expanduser("~/Desktop/MAYA_CAD_Exports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class MayaCadEngine:
    @staticmethod
    def generate_parametric_mesh(part_name: str) -> Dict[str, Any]:
        """
        Generates 3D procedural vertex & schematic data for real-time in-browser Three.js rendering.
        Supports: 'web_shooter', 'trigger', 'reactor', 'bracket', 'gear', 'mount', 'box'
        """
        part = part_name.lower().strip()
        
        # 1. Spider-Man Web Shooter / Barrel Assembly
        if "shooter" in part or "barrel" in part:
            return {
                "type": "web_shooter",
                "label": "TASER WEB-SHOOTER MK-1",
                "geometry": "cylinder_complex",
                "params": {"radiusTop": 0.75, "radiusBottom": 0.92, "height": 2.5, "segments": 32},
                "accent_color": "#00f0ff",
                "status": "3D SCHEMATIC LOADED"
            }
        
        # 2. Insulated Trigger Assembly
        elif "trigger" in part:
            return {
                "type": "trigger",
                "label": "NON-CONDUCTIVE DUAL TRIGGER",
                "geometry": "box_compound",
                "params": {"width": 0.6, "height": 1.5, "depth": 1.2},
                "accent_color": "#f59e0b",
                "status": "DIELECTRIC RUBBER SPEC"
            }

        # 3. Mechanical Mounting Bracket / Gear
        elif "bracket" in part or "mount" in part or "gear" in part:
            return {
                "type": "bracket",
                "label": "HIGH-TENSILE CHASSIS BRACKET",
                "geometry": "bracket_torus",
                "params": {"radius": 0.82, "tube": 0.12, "tubularSegments": 120, "radialSegments": 24},
                "accent_color": "#38bdf8",
                "status": "AEROSPACE ALLOY SPEC"
            }

        # 4. Default Arc Core / Reactor
        else:
            return {
                "type": "reactor",
                "label": "PRIMARY FLUX GENERATOR",
                "geometry": "torus_knot",
                "params": {"radius": 0.88, "tube": 0.075, "tubularSegments": 200, "radialSegments": 36},
                "accent_color": "#00f0ff",
                "status": "PARAMETRIC CAD ONLINE"
            }

    @staticmethod
    def generate_parametric_stl(part_type: str, dimensions: dict = None) -> str:
        """
        Generates a 3D printable ASCII STL file using native parametric generation.
        Supports: 'bracket', 'spacer', 'trigger', 'mount', 'box', 'plate', 'enclosure'
        """
        if dimensions is None:
            dimensions = {}

        part_type = part_type.lower().strip()
        part_id = int(dimensions.get('id', 101))
        filename = f"{part_type}_{part_id}.stl"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Default dimensions in mm
        w = float(dimensions.get("width", 35.0))
        h = float(dimensions.get("height", 15.0))
        d = float(dimensions.get("depth", 8.0))

        v = [
            (0, 0, 0), (w, 0, 0), (w, h, 0), (0, h, 0),
            (0, 0, d), (w, 0, d), (w, h, d), (0, h, d)
        ]

        facets = [
            (0,2,1), (0,3,2), (4,5,6), (4,6,7), # Bottom / Top
            (0,1,5), (0,5,4), (2,3,7), (2,7,6), # Front / Back
            (0,4,7), (0,7,3), (1,2,6), (1,6,5)  # Left / Right
        ]

        with open(filepath, "w") as f:
            f.write(f"solid MAYA_{part_type.upper()}\n")
            for p1, p2, p3 in facets:
                f.write("  facet normal 0.0 0.0 0.0\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {v[p1][0]} {v[p1][1]} {v[p1][2]}\n")
                f.write(f"      vertex {v[p2][0]} {v[p2][1]} {v[p2][2]}\n")
                f.write(f"      vertex {v[p3][0]} {v[p3][1]} {v[p3][2]}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
            f.write(f"endsolid MAYA_{part_type.upper()}\n")

        return filepath

    @staticmethod
    def send_to_slicer(stl_path: str, slicer_name: str = "PrusaSlicer") -> str:
        """Opens the exported model in preferred slicer or CAD viewer."""
        try:
            slicer_candidates = [slicer_name, "PrusaSlicer", "BambuStudio", "Bambu Studio", "OrcaSlicer", "UltiMaker Cura", "Blender", "FreeCAD", "OpenSCAD"]
            for app in slicer_candidates:
                result = subprocess.run(["open", "-a", app, stl_path], capture_output=True)
                if result.returncode == 0:
                    return f"Sent {os.path.basename(stl_path)} to {app}."
            
            subprocess.run(["open", stl_path])
            return f"Model ready and opened: {stl_path}"
        except Exception as e:
            return f"Slicer launch error: {e}"
