# Retinal Vessel Mask Sensitivity Analysis

A reproducible computer-vision study of how controlled changes to expert retinal vessel segmentation masks affect quantitative vascular measurements.

The project uses real colour fundus photographs, expert vessel annotations, and field-of-view (FOV) masks from the **High-Resolution Fundus (HRF) Image Database**. It applies controlled morphological erosion and dilation to the expert masks, then compares mask overlap and changes in extracted vessel features.

> **Research scope:** This project studies the sensitivity of measurements derived from segmentation masks. It does not train a vessel-segmentation model, classify eye diseases, or provide medical diagnoses.

## Research question

**How sensitive are quantitative retinal vessel measurements to small, controlled changes in an expert vessel segmentation mask?**

A segmentation mask is often used as the starting point for downstream measurements. Even when the underlying fundus photograph remains unchanged, small changes to the mask can affect the apparent vessel area and the structure of its skeleton. This project measures those effects under a controlled experimental setup.

## Objectives

- Load original HRF fundus photographs together with their expert vessel annotations and FOV masks.
- Apply reproducible morphological perturbations to copies of the expert vessel masks.
- Quantify the overlap between each perturbed mask and its original reference annotation.
- Extract pixel-based vascular features from each mask.
- Compare feature changes across perturbation conditions and across the available images.
- Produce reproducible CSV tables and figures for further analysis.

## Dataset

This project uses the **segmentation subset** of the HRF Image Database.

| Dataset component          | Description                                       |
| -------------------------- | ------------------------------------------------- |
| Fundus photographs         | 45 high-resolution colour retinal images          |
| Healthy cases              | 15 images                                         |
| Diabetic retinopathy cases | 15 images                                         |
| Glaucoma cases             | 15 images                                         |
| Vessel annotations         | Expert-generated binary vessel reference masks    |
| FOV masks                  | Masks identifying the valid retinal field of view |

**Official dataset:** [High-Resolution Fundus (HRF) Image Database](https://www5.informatik.uni-erlangen.de/research/data/fundus-images/)

**Dataset licence:** Creative Commons Attribution 4.0 International (CC BY 4.0). The dataset is separate from this repository's software licence. Attribute the dataset creators and cite the associated publication when using the data.

The dataset archive is downloaded by the project script into `data/HRF/`. The original dataset is not committed to this Git repository. This keeps the repository lightweight and preserves the original dataset as a separately licensed research resource.

The downloader validates the expected HRF directory structure and checks that the segmentation subset contains 45 images, at least 45 manual vessel masks, and FOV masks before the experiment proceeds.

## Experimental design

For each HRF image, the expert vessel annotation is treated as the reference mask. The experiment creates four controlled morphological variants in addition to the original mask:

| Condition     | Operation       | Structuring element  |
| ------------- | --------------- | -------------------- |
| `original`    | No perturbation | —                    |
| `erosion_r1`  | Erosion         | Disk radius 1 pixel  |
| `erosion_r2`  | Erosion         | Disk radius 2 pixels |
| `dilation_r1` | Dilation        | Disk radius 1 pixel  |
| `dilation_r2` | Dilation        | Disk radius 2 pixels |

All feature extraction is restricted to the supplied FOV mask. The original annotation is not modified; perturbations are applied to derived copies in memory.

These transformations are controlled experimental perturbations. They are not additional patient observations and should not be interpreted as a complete simulation of errors produced by every segmentation algorithm.

## Measurements and evaluation

### Mask overlap

Each perturbed mask is compared with the original expert annotation using:

- **Dice coefficient:** measures overlap between the reference and perturbed masks.
- **Intersection over Union (IoU):** measures the intersection relative to the union of the masks.

For two binary masks, the metrics are:

\[
\mathrm{Dice}(A,B)=\frac{2|A\cap B|}{|A|+|B|}
\]

\[
\mathrm{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}
\]

### Extracted vascular features

The current implementation computes six features for each condition:

| Feature                  | Current definition                                                                     |
| ------------------------ | -------------------------------------------------------------------------------------- |
| Vessel area (pixels)     | Number of vessel pixels inside the FOV                                                 |
| Vessel area fraction     | Vessel pixels divided by valid FOV pixels                                              |
| Skeleton pixel count     | Number of pixels in the skeletonized vessel mask                                       |
| Skeleton component count | Number of connected components in the skeleton, using 8-neighbour connectivity         |
| Endpoint pixel count     | Skeleton pixels with exactly one neighbouring skeleton pixel in the 8-neighbourhood    |
| Junction cluster count   | Connected clusters of skeleton pixels with at least three neighbouring skeleton pixels |

Feature changes are expressed as percentage differences from the original-mask measurement:

\[
\mathrm{Change}(\%)=100\times\frac{F*{perturbed}-F*{original}}{F\_{original}}
\]

When the original feature value is zero, the percentage change is undefined and is recorded as `NaN` rather than dividing by zero.

**Measurement note:** These are pixel-based image features. They are not calibrated physical measurements of vessel length or diameter. The endpoint and junction quantities are implementation-specific pixel/cluster counts, not clinical vascular biomarkers.

## Methodology pipeline

```text
HRF fundus photograph
        +
Expert vessel annotation
        +
Field-of-view mask
        |
        v
Validate and pair dataset files
        |
        v
Create original and perturbed masks
        |
        +--> Original
        +--> Erosion (radius 1 px)
        +--> Erosion (radius 2 px)
        +--> Dilation (radius 1 px)
        +--> Dilation (radius 2 px)
        |
        v
Restrict analysis to field of view
        |
        +--> Dice and IoU against original mask
        +--> Vessel area and area fraction
        +--> Skeletonization and component count
        +--> Endpoint and junction-cluster counts
        |
        v
Per-image results and condition-level summary
        |
        v
CSV tables and comparison figures
```

## Repository structure

```text
retinal-vessel-mask-sensitivity/
├── .github/
│   └── workflows/
│       └── tests.yml
├── data/
│   └── README.md
├── notebooks/
│   └── 01_mask_perturbation_analysis.ipynb
├── results/
│   └── figures/
├── scripts/
│   └── download_data.py
├── src/
│   └── retina_sensitivity/
│       ├── __init__.py
│       ├── data.py
│       ├── experiment.py
│       ├── features.py
│       ├── network.py
│       └── perturbations.py
├── tests/
│   ├── test_core.py
│   └── test_network.py
├── CITATION.cff
├── LICENSE
├── pyproject.toml
├── pytest.ini
└── requirements.txt
```

## Installation and usage

### Requirements

- Python 3.11 or newer
- Internet access for the initial HRF dataset download
- JupyterLab for running the notebook

### Windows PowerShell

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Download and validate the HRF dataset:

```powershell
python scripts\download_data.py
```

Run the tests:

```powershell
python -m pytest -q
```

Launch JupyterLab:

```powershell
python -m jupyter lab
```

Open `notebooks/01_mask_perturbation_analysis.ipynb` and use **Kernel → Restart Kernel and Run All Cells** to execute the workflow from a clean kernel.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python scripts/download_data.py
python -m pytest -q
python -m jupyter lab
```

### Run a small smoke test

The notebook processes all 45 HRF images by default. To test the workflow on three images before running the complete dataset, set the environment variable **before launching Jupyter**.

Windows PowerShell:

```powershell
$env:RETINA_SAMPLE_LIMIT = "3"
python -m jupyter lab
```

macOS / Linux:

```bash
RETINA_SAMPLE_LIMIT=3 python -m jupyter lab
```

To process the full dataset, remove the variable or set it to `0` before starting Jupyter.

Windows PowerShell:

```powershell
Remove-Item Env:RETINA_SAMPLE_LIMIT -ErrorAction SilentlyContinue
python -m jupyter lab
```

macOS / Linux:

```bash
unset RETINA_SAMPLE_LIMIT
python -m jupyter lab
```

## Generated outputs

After a successful notebook run, the project writes:

| Output                                    | Description                                                                                                                               |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `results/per_image_features.csv`          | One row per image and experimental condition, including overlap metrics, extracted features and percentage changes from the original mask |
| `results/summary.csv`                     | Condition-level means across processed images                                                                                             |
| `results/figures/mask_overlap.png`        | Mean Dice overlap for the five mask conditions                                                                                            |
| `results/figures/feature_sensitivity.png` | Mean percentage change in selected features for the four perturbed conditions                                                             |

With all 45 images and five conditions per image, the per-image table is expected to contain 225 rows. The summary contains one row per condition. These are expected output dimensions, not reported scientific findings.

Generated CSVs and figures are excluded from version control by default. Add selected, reproducible outputs to the repository only after reviewing them and deciding that they are appropriate to share.

## Testing

Run the test suite from the repository root:

```bash
python -m pytest -v
```

The tests check mask perturbation behaviour, shape and FOV preservation, overlap metrics, feature extraction, and verified HTTPS download configuration. Small artificial binary arrays are used only as unit-test fixtures; they are not represented as HRF research data and are not used as experimental observations.

## Reproducibility and implementation notes

- The analysis uses the HRF expert annotations as reference masks.
- The original masks are not modified by the perturbation functions.
- The FOV mask is applied during feature extraction.
- Morphological structuring elements and radii are explicitly defined in the source code.
- The notebook supports a sample limit for smoke testing; the default is all 45 images.
- The downloader uses verified HTTPS connections. Do not disable TLS certificate verification to work around network or certificate errors.

## Limitations

1. The perturbation study currently uses only morphological erosion and dilation at two pixel radii. It does not represent every error mode found in model-generated segmentations.
2. The experiment starts from expert reference masks and does not evaluate a newly trained or existing vessel-segmentation model.
3. Measurements are reported in pixels or pixel-derived quantities; physical calibration is not performed.
4. Skeleton, endpoint and junction measurements depend on the chosen skeletonization and 8-neighbour connectivity definitions.
5. The current summary reports means by perturbation condition. It does not perform inferential statistical testing or establish clinical differences between diagnostic groups.
6. The HRF dataset is a research benchmark and this project is not a medical device or diagnostic system.

## Future work

Potential extensions, subject to appropriate implementation and validation, include:

- Additional controlled perturbations such as local vessel breaks, false-positive additions and spatially varying mask noise.
- Analysis of segmentation predictions from independently developed vessel-segmentation methods.
- Robustness comparisons across additional public retinal vessel datasets.
- Statistical uncertainty estimates and per-image distribution plots.
- Physical-scale measurements where reliable image calibration metadata is available.

These are possible extensions and are not claimed as completed features of the current implementation.

## Dataset citation

Please cite the HRF dataset and its associated publication when using the data:

Budai, A., Bock, R., Maier, A., Hornegger, J., & Michelson, G. (2013). **Robust Vessel Segmentation in Fundus Images.** _International Journal of Biomedical Imaging_, 2013, Article 154860. https://doi.org/10.1155/2013/154860

BibTeX:

```bibtex
@article{budai2013robust,
  title   = {Robust Vessel Segmentation in Fundus Images},
  author  = {Budai, Attila and Bock, R{\"u}diger and Maier, Andreas and Hornegger, Joachim and Michelson, Georg},
  journal = {International Journal of Biomedical Imaging},
  volume  = {2013},
  pages   = {154860},
  year    = {2013},
  doi     = {10.1155/2013/154860}
}
```

## Software licence

The source code in this repository is distributed under the MIT License. The HRF dataset is a separate resource distributed under CC BY 4.0; its licence and attribution requirements continue to apply independently of the software licence.

## Author

**Vinay Kartheek Bathala**  
B.Tech, Computer Science and Engineering (Artificial Intelligence & Machine Learning)  
SRM Institute of Science and Technology
