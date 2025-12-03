import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple

from PyQt6 import QtCore

# IMPORTS THE INFERENCE LOGIC DIRECTLY
# Note: 'ai_model' must contain an __init__.py file
try:
    from ai_model import infer_single_overlay_improved as inference_engine
except ImportError:
    # Fallback if running from a different root context
    import infer_single_overlay_improved as inference_engine


def _resource_path(relative: str) -> str:
    """ Resolve a resource path in both dev and PyInstaller exe modes. """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent

    return str(base / relative)


class CellDetectorWrapper(QtCore.QObject):

    detection_started = QtCore.pyqtSignal()
    detection_complete = QtCore.pyqtSignal(list)
    detection_error = QtCore.pyqtSignal(str)
    detection_log = QtCore.pyqtSignal(str)

    def __init__(self, inference_script_path: str = None, model_path: str = None):
        super().__init__()
        
        # We don't strictly need script path anymore since we import it, 
        # but we keep the logic for the model path.
        default_model = "ai_model/cell_classifier_best.pth"

        if model_path is None:
            self.model_path = _resource_path(default_model)
        elif os.path.isabs(model_path):
            self.model_path = model_path
        else:
            self.model_path = _resource_path(model_path)

        print(f"[DEBUG] Model path: {self.model_path}")

    def detect_cells(self, image_path: str) -> List[Tuple[int, int]]:
        try:
            self.detection_started.emit()

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model weights not found: {self.model_path}")

            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            temp_dir = tempfile.mkdtemp(prefix="cell_detection_")
            self.detection_log.emit(f"Running inference on {image_path}...")
            
            # CALL THE FUNCTION DIRECTLY (No Subprocess)
            # This passes all your custom parameters directly to the function
            coordinates = inference_engine.run_inference(
                image=image_path,
                weights=self.model_path,
                out_dir=temp_dir,
                device="cpu",         # Force CPU for stability in app
                color_order="rgb",
                window=200,
                use_edge_gate=True,
                keep_border=True,
                border_px=2,
                green_k=0.24,
                tR=0.55, tG=0.55, tB=0.42,
                delta_rg=0.16, rg_ratio=0.82,
                min_cc_area_gate=8, max_cc_area_gate=240,
                candidate_union_radius=5,
                nms_radius=20,
                post_tight_pair_floor=18,
                fp_gate_proximity=True,
                fp_rededge=True,
                snap=True,
                snap_search_r=10,
                snap_jump_limit=12.0,
                snap_s_lo=150, snap_v_lo=170,
                h_lo=24, h_hi=34, s_lo=210, v_lo=210,
                min_area=8, max_area=240,
                threshold=0.92
            )

            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            self.detection_log.emit(f"Detection complete. Found {len(coordinates)} cells.")
            self.detection_complete.emit(coordinates)
            return coordinates

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Error during detection: {str(e)}"
            self.detection_error.emit(error_msg)
            return []

    def load_pnt_file(self, pnt_file: str) -> List[Tuple[int, int]]:
        # This function might not be needed anymore since run_inference 
        # returns the coordinates directly, but keeping it just in case.
        with open(pnt_file, "r") as f:
            data = json.load(f)
        coordinates = []
        if "points" in data:
            for _, classes in data["points"].items():
                for _, points in classes.items():
                    for point in points:
                        coordinates.append((int(point["x"]), int(point["y"])))
        return coordinates


class DetectionWorker(QtCore.QRunnable):

    def __init__(self, detector: CellDetectorWrapper, image_path: str):
        super().__init__()
        self.detector = detector
        self.image_path = image_path

    def run(self):
        self.detector.detect_cells(self.image_path)