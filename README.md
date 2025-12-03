=# CellCounter Biomarker Detection Pipeline

CellCounter is a computer-vision + deep-learning pipeline for detecting microscopic biomarkers in tissue-stained microscopy images.
It uses color-space gating, candidate generation, CNN classification, geometric postprocessing, and exports DDG-compatible `.pnt` annotation files for use inside DotDotGoose.

---

## Purpose

This tool automates the process of detecting biomarkers that would otherwise be manually counted by a human using DotDotGoose.

This enables:

- automated microscopy detection
- reproducible & consistent annotation
- rapid dataset labeling
- direct interoperability with DotDotGoose
- hybrid AI + human review workflows

---

## Detection Pipeline Overview

1. Load microscopy image
2. Optional structural edge+green+yellow gating
3. Strict HSV yellow-range centroids
4. Merge gate + HSV candidates
5. Non-max suppression (candidate dedupe)
6. Center crop around each candidate (224×224)
7. ResNet-18 scoring
8. Thresholding
9. Optional snap-to-yellow centroid refinement
10. Post-snap NMS
11. Tight-pair pruning
12. Output overlay, CSV, and PNT files

---

## Output Files

Given `sample.png`, the pipeline produces:

- sample_overlay.png      # detections drawn
- sample_detections.csv   # x,y,score
- sample_artifacts.csv    # debug outputs
- sample.pnt              # DotDotGoose annotation file

---

## Dependencies

### Runtime:

- Python 3.8+
- NumPy
- OpenCV
- PyTorch
- torchvision
- Pillow

### Model Weights

The trained model file used by the AI is located at:
CellCounter499/ai_model/cell_classifier_best.pth

This file is bundled into the executable at build time and automatically loaded inside the DotDotGoose UI. Users do not need to manually interact with it.

---

## Installation & Setup

### 1. Clone and Environment Setup

```bash
git clone [https://github.com/.../CellCounter499](https://github.com/.../CellCounter499)
cd CellCounter499

# Create virtual environment
python3 -m venv cc-env

# Activate Environment
# macOS / Linux:
source cc-env/bin/activate
# Windows:
cc-env\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
pip install pyinstaller

# Remove previous builds to prevent caching issues then build app
# macOs/Linux:
 cd package
rm -rf build dist
pyinstaller --clean --noconfirm ddg_mac.spec
# Windows:
cd package
pyinstaller --clean --noconfirm ddg.spec