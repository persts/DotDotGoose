"""
Microscopy candidate union + gated detection (224, no-norm by default)

This script runs the full CellCounter/DDG biomarker-detection pipeline on a single
microscopy image and writes:

- A PNG overlay with detections drawn as circles
- A CSV of detections (x, y, score)
- A CSV of artifact/debug paths
- A DDG-compatible .pnt file with point annotations for DotDotGoose

High-level pipeline
-------------------
1. **Load image**
2. **Optional edge/green/yellow gate** (structural + color gate)
3. **Strict HSV yellow candidates**
4. **Candidate union + small-radius NMS** (dedupe)
5. **Center crops around candidates**
6. **Optional pre-CNN FP filters** (compactness, blobness, red-edge, gate proximity)
7. **CNN scoring** (ResNet-18, 224x224 crops, 1 output logit per crop)
8. **Score thresholding**
9. **Radius-based NMS** (pre-snap)
10. **Optional snapping to yellow centroids** (HSV-based refinement with jump safety)
11. **Radius-based NMS** (post-snap)
12. **Tight-pair pruning** (remove very close duplicates)
13. **Write overlay + CSVs + PNT**

Usage
-----
python infer_single_overlay_improved.py \
    --image /path/to/image.png \
    --weights /path/to/resnet18_weights.pt \
    --out_dir experiments/quickcheck \
    [other optional flags...]

By default:
- Model expects 224x224 crops
- No normalization (unless --normalize is set)
- Color order is BGR->RGB before feeding the model (color_order="rgb")
"""

import sys
import os
import argparse
import csv
import json
from pathlib import Path
from typing import List, Tuple, Any, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn

# -------------------- Utility Functions --------------------

def load_image_bgr(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img

def to_tensor_bchw_uint8(crops: List[np.ndarray], color_order: str, normalize: bool,
                          mean_str: str, std_str: str, device: torch.device) -> torch.Tensor:
    if not crops:
        return torch.empty(0, device=device)
    arr = np.stack(crops, axis=0)
    if color_order.lower() == "rgb":
        arr = arr[:, :, :, ::-1]
    arr = arr.astype(np.float32) / 255.0
    if normalize:
        mean = np.array([float(v) for v in mean_str.split(",")], dtype=np.float32).reshape(1, 1, 1, 3)
        std  = np.array([float(v) for v in std_str.split(",")],  dtype=np.float32).reshape(1, 1, 1, 3)
        arr = (arr - mean) / (std + 1e-7)
    arr = arr.transpose(0, 3, 1, 2)
    return torch.from_numpy(arr).to(device)

def strip_prefix_if_present(state_dict, prefix: str):
    keys = list(state_dict.keys())
    if keys and all(k.startswith(prefix) for k in keys):
        return {k[len(prefix):]: v for k, v in state_dict.items()}
    return state_dict

def build_resnet18(num_classes: int) -> nn.Module:
    import torchvision.models as tvm
    m = tvm.resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, num_classes)
    return m

def extract_state_dict(ckpt: Any, checkpoint_key: Optional[str]):
    if isinstance(ckpt, dict):
        if checkpoint_key and checkpoint_key in ckpt and isinstance(ckpt[checkpoint_key], dict):
            return ckpt[checkpoint_key]
        for k in ("state_dict", "model_state", "model", "net", "weights"):
            v = ckpt.get(k)
            if isinstance(v, dict) and v and isinstance(next(iter(v.values())), torch.Tensor):
                return v
        if ckpt and isinstance(next(iter(ckpt.values())), torch.Tensor):
            return ckpt
    if hasattr(ckpt, "keys") and ckpt and isinstance(next(iter(ckpt.values())), torch.Tensor):
        return ckpt
    return {}

def load_model(weights_path: str, device: torch.device, num_classes: int) -> nn.Module:
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Model weights not found at: {weights_path}")
    ckpt = torch.load(weights_path, map_location=device)
    state = extract_state_dict(ckpt, None)
    model = build_resnet18(num_classes=num_classes).to(device)
    for pref in ("module.", "model.", "net."):
        if any(k.startswith(pref) for k in state.keys()):
            state = strip_prefix_if_present(state, pref)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model

def find_yellow_candidates(img_bgr: np.ndarray, h_lo=15, h_hi=40, s_lo=80, v_lo=80, min_area=5, max_area=500):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([h_lo, s_lo, v_lo], dtype=np.uint8)
    upper = np.array([h_hi, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.medianBlur(mask, 5)
    kernel_small = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=2)
    kernel_medium = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    for c in contours:
        a = cv2.contourArea(c)
        if a < min_area or a > max_area: continue
        M = cv2.moments(c)
        if M["m00"] != 0:
            centers.append((int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])))
    return centers, mask

def _float_rgb(img_bgr):
    img = img_bgr.astype(np.float32) / 255.0
    return img[..., 2], img[..., 1], img[..., 0]

def build_edge_green_yellow_gate(img_bgr, edge_band_px=5, canny_lo=10, canny_hi=40, green_k=0.25,
                                 tR=0.55, tG=0.55, tB=0.35, delta_rg=0.20, rg_ratio=0.75,
                                 min_cc_area=6, max_cc_area=200, keep_border=False, border_px=8,
                                 debug=False, debug_prefix="debug"):
    H, W = img_bgr.shape[:2]
    R, G, B = _float_rgb(img_bgr)
    red_u8 = np.clip(R * 255, 0, 255).astype(np.uint8)
    red_blur = cv2.GaussianBlur(red_u8, (0, 0), 1.0)
    edges = cv2.Canny(red_blur, canny_lo, canny_hi)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * edge_band_px + 1, 2 * edge_band_px + 1))
    edge_band = cv2.dilate(edges, kernel) > 0
    g_blur = cv2.GaussianBlur(G, (0, 0), 1.0)
    g_thr = float(np.mean(g_blur) + green_k * np.std(g_blur))
    green_mask = (g_blur > g_thr)
    yellow = (R > tR) & (G > tG) & (B < tB) & (np.abs(R - G) < delta_rg)
    rg_min, rg_max = np.minimum(R, G) + 1e-6, np.maximum(R, G) + 1e-6
    yellow &= (rg_min / rg_max) > rg_ratio
    cand = edge_band & green_mask & yellow
    if not keep_border:
        inner = np.zeros_like(cand, dtype=bool)
        inner[border_px:H - border_px, border_px:W - border_px] = True
        cand &= inner
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cand = cv2.morphologyEx(cand.astype(np.uint8), cv2.MORPH_OPEN, k3)
    cand = cv2.morphologyEx(cand, cv2.MORPH_CLOSE, k3).astype(bool)
    num, lab, stats, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
    good = np.zeros_like(cand, dtype=bool)
    for i in range(1, num):
        if min_cc_area <= stats[i, cv2.CC_STAT_AREA] <= max_cc_area:
            good |= (lab == i)
    return good, {}

def center_crop(img, x, y, size):
    h, w = img.shape[:2]
    r = size // 2
    x0, y0 = max(0, x - r), max(0, y - r)
    x1, y1 = min(w, x + r), min(h, y + r)
    crop = img[y0:y1, x0:x1, :]
    if crop.shape[0] != size or crop.shape[1] != size:
        pad_t, pad_l = (size - crop.shape[0]) // 2, (size - crop.shape[1]) // 2
        pad_b, pad_r = size - crop.shape[0] - pad_t, size - crop.shape[1] - pad_l
        crop = cv2.copyMakeBorder(crop, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_REFLECT_101)
    return crop

def snap_to_yellow_centroids(img_bgr, pts_xy, search_r=8, h_lo=18, h_hi=42, s_lo=150, v_lo=170,
                             min_area=8, max_area=220):
    if len(pts_xy) == 0: return np.empty((0, 2), dtype=np.float32), np.empty((0,), dtype=np.int32)
    H, W = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (h_lo, s_lo, v_lo), (h_hi, 255, 255))
    mask = cv2.medianBlur(mask, 3)
    snapped, keep_idx = [], []
    for i, (x, y) in enumerate(pts_xy.astype(int)):
        x0, y0 = max(0, x - search_r), max(0, y - search_r)
        x1, y1 = min(W, x + search_r + 1), min(H, y + search_r + 1)
        num, lab, stats, cents = cv2.connectedComponentsWithStats(mask[y0:y1, x0:x1], connectivity=8)
        best_d2, best_xy = None, None
        for j in range(1, num):
            if not (min_area <= stats[j, cv2.CC_STAT_AREA] <= max_area): continue
            cx, cy = cents[j]
            d2 = (cx - (x-x0)) ** 2 + (cy - (y-y0)) ** 2
            if (best_d2 is None) or (d2 < best_d2):
                best_d2, best_xy = d2, (x0 + cx, y0 + cy)
        if best_xy is not None:
            snapped.append(best_xy)
            keep_idx.append(i)
    if not snapped: return np.empty((0, 2), dtype=np.float32), np.empty((0,), dtype=np.int32)
    return np.array(snapped, dtype=np.float32), np.array(keep_idx, dtype=np.int32)

def dot_compactness_ok(crop_bgr, min_ratio=0.003, max_ratio=0.030, blur_sigma=1.0):
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    if blur_sigma > 0: gray = cv2.GaussianBlur(gray, (0,0), blur_sigma)
    _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    ratio = float((thr > 0).sum()) / thr.size
    return (min_ratio <= ratio <= max_ratio)

def log_blobness_score(crop_bgr, sigma=1.2):
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)/255.0
    g = cv2.GaussianBlur(gray, (0,0), sigma)
    lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    return float(np.clip(lap, 0, 1).mean()) - 0.6 * float(np.clip(-lap, 0, 1).mean())

def red_edge_ok(crop_bgr, canny_lo=10, canny_hi=40, min_edge_pct=0.010):
    R = crop_bgr[..., 2]
    rb = cv2.GaussianBlur(R, (0,0), 1.0)
    return (cv2.Canny(rb, canny_lo, canny_hi) > 0).mean() > min_edge_pct

def require_gate_proximity(points, gate_mask, radius=4):
    if gate_mask is None or len(points) == 0: return np.arange(len(points), dtype=np.int32)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*radius+1, 2*radius+1))
    near = cv2.dilate(gate_mask.astype(np.uint8), k) > 0
    return np.array([i for i,(x,y) in enumerate(points.astype(int)) 
                     if 0 <= y < near.shape[0] and 0 <= x < near.shape[1] and near[y,x]], dtype=np.int32)

def prune_tight_pairs(points, scores, floor=8):
    if len(points) == 0: return points, scores
    keep = []
    used = np.zeros(len(points), bool)
    order = np.argsort(-scores)
    f2 = floor*floor
    for i in order:
        if used[i]: continue
        keep.append(i)
        used |= ((points[:,0]-points[i,0])**2 + (points[:,1]-points[i,1])**2 <= f2)
        used[i] = True
    keep = np.array(keep, dtype=np.int32)
    return points[keep], scores[keep]

def save_detections_csv(csv_path, coords_xy, scores):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "score"])
        for (x, y), s in zip(coords_xy, scores):
            writer.writerow([int(x), int(y), float(s)])

def save_artifacts_csv(csv_path, artifact_rows):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["artifact_type", "path"])
        for t, p in artifact_rows:
            writer.writerow([t, os.path.abspath(p)])

def save_detections_pnt(pnt_path, image_path, coords_xy):
    os.makedirs(os.path.dirname(pnt_path), exist_ok=True)
    pkg = {
        "classes": ["output"],
        "points": {image_path: {"output": [{"x": float(x), "y": float(y)} for x, y in coords_xy]}},
        "colors": {"output": [255, 255, 0]},
        "metadata": {"survey_id": "", "coordinates": {}},
        "custom_fields": {"fields": [], "data": {}},
        "ui": {"grid": {"size": 200, "color": [255, 255, 255]}, "point": {"radius": 6, "color": [255, 255, 0]}}
    }
    with open(pnt_path, "w") as f:
        json.dump(pkg, f, indent=2)

# -------------------- MAIN LOGIC (FUNCTIONALIZED) --------------------

def run_inference(image: str, weights: str, out_dir: str = "experiments/quickcheck", 
                  window=224, normalize=False, mean="0.485,0.456,0.406", std="0.229,0.224,0.225",
                  color_order="rgb", device="cpu", threshold=0.935, nms_radius=18,
                  circle_radius=8, thickness=-1, h_lo=22, h_hi=36, s_lo=200, v_lo=200,
                  min_area=10, max_area=240, use_edge_gate=False, edge_band_px=5,
                  canny_lo=10, canny_hi=40, green_k=0.25, tR=0.55, tG=0.55, tB=0.40,
                  delta_rg=0.22, rg_ratio=0.78, min_cc_area_gate=6, max_cc_area_gate=260,
                  keep_border=False, border_px=8, debug_masks=False, candidate_union_radius=8,
                  snap=False, snap_search_r=8, snap_h_lo=18, snap_h_hi=42, snap_s_lo=150,
                  snap_v_lo=170, snap_min_area=8, snap_max_area=220, snap_jump_limit=9.0,
                  fp_compactness=False, fp_blobness=False, fp_rededge=False, fp_gate_proximity=False,
                  post_tight_pair_floor=8, **kwargs):
    
    # 1. Setup
    device_obj = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
    os.makedirs(out_dir, exist_ok=True)
    artifacts = []
    stem = Path(image).stem

    # 2. Load Image
    try:
        img = load_image_bgr(image)
    except Exception as e:
        print(f"[ERROR] {e}")
        return [] # Return empty list on failure

    # 3. Gate
    gate_mask = None
    if use_edge_gate:
        dbg_p = os.path.join(out_dir, f"{stem}")
        gate_mask, _ = build_edge_green_yellow_gate(
            img, edge_band_px, canny_lo, canny_hi, green_k, tR, tG, tB, delta_rg, rg_ratio,
            min_cc_area_gate, max_cc_area_gate, keep_border, border_px, debug_masks, dbg_p
        )
    
    gate_pts = []
    if gate_mask is not None:
        num, _, stats, cent = cv2.connectedComponentsWithStats(gate_mask.astype(np.uint8), connectivity=8)
        for i in range(1, num):
            if min_cc_area_gate <= stats[i, cv2.CC_STAT_AREA] <= max_cc_area_gate:
                gate_pts.append((int(round(cent[i][0])), int(round(cent[i][1]))))

    # 4. Candidates
    hsv_pts, yellow_mask = find_yellow_candidates(img, h_lo, h_hi, s_lo, v_lo, min_area, max_area)
    
    all_pts = (gate_pts or []) + (hsv_pts or [])
    cand_xy = []
    if len(all_pts):
        P = np.array(all_pts, dtype=np.int32)
        # Inline NMS logic for dedupe
        if len(P) > 0:
            order = np.arange(len(P))
            keep_idx, used = [], np.zeros(len(P), dtype=bool)
            rr = candidate_union_radius**2
            for i in order:
                if used[i]: continue
                keep_idx.append(i)
                used |= ((P[:,0]-P[i,0])**2 + (P[:,1]-P[i,1])**2 <= rr)
                used[i] = True
            cand_xy = [tuple(map(int, P[i])) for i in keep_idx]

    # Return if no candidates
    if len(cand_xy) == 0:
        save_detections_pnt(os.path.join(out_dir, f"{stem}.pnt"), image, [])
        return []

    # 5. Crops
    crops = [center_crop(img, x, y, window) for (x, y) in cand_xy]
    
    # 6. Filters
    valid_indices = list(range(len(crops)))
    if fp_compactness: valid_indices = [i for i in valid_indices if dot_compactness_ok(crops[i])]
    if fp_blobness: valid_indices = [i for i in valid_indices if log_blobness_score(crops[i]) > 0.010]
    if fp_rededge: valid_indices = [i for i in valid_indices if red_edge_ok(crops[i], canny_lo, canny_hi)]
    if fp_gate_proximity and gate_mask is not None:
        kept = require_gate_proximity(np.array(cand_xy)[valid_indices], gate_mask)
        valid_indices = [valid_indices[k] for k in kept]

    crops = [crops[i] for i in valid_indices]
    cand_xy = [cand_xy[i] for i in valid_indices]

    if not crops:
        save_detections_pnt(os.path.join(out_dir, f"{stem}.pnt"), image, [])
        return []

    # 7. Inference
    try:
        model = load_model(weights, device=device_obj, num_classes=1)
        x_tensor = to_tensor_bchw_uint8(crops, color_order, normalize, mean, std, device_obj)
        with torch.no_grad():
            probs = torch.sigmoid(model(x_tensor).squeeze()).cpu().numpy()
    except Exception as e:
        print(f"Error during inference: {e}")
        return []

    probs = np.atleast_1d(probs)
    keep = probs >= threshold
    sel_xy = np.array(cand_xy)[keep]
    sel_sc = probs[keep]

    # 8. Post-Processing NMS/Snap
    if nms_radius > 0:
        pts_tmp, sc_tmp = prune_tight_pairs(sel_xy, sel_sc, floor=nms_radius)
        sel_xy, sel_sc = pts_tmp, sc_tmp

    if snap and len(sel_xy) > 0:
        snap_pts, idxs = snap_to_yellow_centroids(
            img, sel_xy, snap_search_r, snap_h_lo, snap_h_hi, snap_s_lo, snap_v_lo, snap_min_area, snap_max_area
        )
        if len(snap_pts) > 0:
            jump = np.sqrt(((snap_pts - sel_xy[idxs])**2).sum(1))
            valid = jump <= snap_jump_limit
            sel_xy = snap_pts[valid]
            sel_sc = sel_sc[idxs][valid]
            if nms_radius > 0:
                 sel_xy, sel_sc = prune_tight_pairs(sel_xy, sel_sc, floor=nms_radius)

    if post_tight_pair_floor > 0:
        sel_xy, sel_sc = prune_tight_pairs(sel_xy, sel_sc, floor=post_tight_pair_floor)

    # 9. Save and Return
    overlay = img.copy()
    for (x, y) in sel_xy:
        cv2.circle(overlay, (int(x), int(y)), circle_radius, (255, 255, 255), thickness)
    
    cv2.imwrite(os.path.join(out_dir, f"{stem}_overlay.png"), overlay)
    save_detections_csv(os.path.join(out_dir, f"{stem}_detections.csv"), sel_xy, sel_sc)
    save_detections_pnt(os.path.join(out_dir, f"{stem}.pnt"), image, sel_xy)
    
    # Return list of tuples [(x,y), ...]
    return [tuple(pt) for pt in sel_xy]

# -------------------- CLI WRAPPER --------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser("Microscopy candidate union + gated detection")
    
    # Required
    ap.add_argument("--image", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--out_dir", default="experiments/quickcheck")

    # Model / Preprocessing
    ap.add_argument("--window", type=int, default=224)
    ap.add_argument("--normalize", action="store_true", default=False)
    ap.add_argument("--mean", default="0.485,0.456,0.406")
    ap.add_argument("--std", default="0.229,0.224,0.225")
    ap.add_argument("--color_order", choices=["rgb", "bgr"], default="rgb")
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    # Scoring / Drawing
    ap.add_argument("--threshold", type=float, default=0.935)
    ap.add_argument("--nms_radius", type=int, default=18)
    ap.add_argument("--circle_radius", type=int, default=8)
    ap.add_argument("--thickness", type=int, default=-1)

    # HSV params
    ap.add_argument("--h_lo", type=int, default=22)
    ap.add_argument("--h_hi", type=int, default=36)
    ap.add_argument("--s_lo", type=int, default=200)
    ap.add_argument("--v_lo", type=int, default=200)
    ap.add_argument("--min_area", type=int, default=10)
    ap.add_argument("--max_area", type=int, default=240)

    # Gate params
    ap.add_argument("--use_edge_gate", action="store_true")
    ap.add_argument("--edge_band_px", type=int, default=5)
    ap.add_argument("--canny_lo", type=int, default=10)
    ap.add_argument("--canny_hi", type=int, default=40)
    ap.add_argument("--green_k", type=float, default=0.25)
    ap.add_argument("--tR", type=float, default=0.55)
    ap.add_argument("--tG", type=float, default=0.55)
    ap.add_argument("--tB", type=float, default=0.40)
    ap.add_argument("--delta_rg", type=float, default=0.22)
    ap.add_argument("--rg_ratio", type=float, default=0.78)
    ap.add_argument("--min_cc_area_gate", type=int, default=6)
    ap.add_argument("--max_cc_area_gate", type=int, default=260)
    ap.add_argument("--keep_border", action="store_true")
    ap.add_argument("--border_px", type=int, default=8)
    ap.add_argument("--debug_masks", action="store_true")

    # Candidate union & snap
    ap.add_argument("--candidate_union_radius", type=int, default=8)
    ap.add_argument("--snap", action="store_true")
    ap.add_argument("--snap_search_r", type=int, default=8)
    ap.add_argument("--snap_h_lo", type=int, default=18)
    ap.add_argument("--snap_h_hi", type=int, default=42)
    ap.add_argument("--snap_s_lo", type=int, default=150)
    ap.add_argument("--snap_v_lo", type=int, default=170)
    ap.add_argument("--snap_min_area", type=int, default=8)
    ap.add_argument("--snap_max_area", type=int, default=220)
    ap.add_argument("--snap_jump_limit", type=float, default=9.0)

    # FP filters
    ap.add_argument("--fp_compactness", action="store_true", default=False)
    ap.add_argument("--fp_blobness", action="store_true", default=False)
    ap.add_argument("--fp_rededge", action="store_true", default=False)
    ap.add_argument("--fp_gate_proximity", action="store_true", default=False)
    ap.add_argument("--post_tight_pair_floor", type=int, default=8)

    # Eval helpers
    ap.add_argument("--truth_csv", default=None)
    ap.add_argument("--match_tol_px", type=float, default=10.0)

    args = ap.parse_args()
    
    # Pass all parsed args as keyword arguments to the function
    run_inference(**vars(args))