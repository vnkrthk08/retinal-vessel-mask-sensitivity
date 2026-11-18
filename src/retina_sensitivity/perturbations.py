from __future__ import annotations

import numpy as np
from skimage.morphology import dilation, erosion, disk


def make_perturbations(vessel_mask: np.ndarray, fov_mask: np.ndarray) -> dict[str, np.ndarray]:
    vessel = np.asarray(vessel_mask, dtype=bool) & np.asarray(fov_mask, dtype=bool)
    return {
        "original": vessel,
        "erosion_r1": erosion(vessel, footprint=disk(1)) & fov_mask,
        "erosion_r2": erosion(vessel, footprint=disk(2)) & fov_mask,
        "dilation_r1": dilation(vessel, footprint=disk(1)) & fov_mask,
        "dilation_r2": dilation(vessel, footprint=disk(2)) & fov_mask,
    }


def overlap_metrics(reference: np.ndarray, candidate: np.ndarray) -> tuple[float, float]:
    reference = np.asarray(reference, dtype=bool)
    candidate = np.asarray(candidate, dtype=bool)
    intersection = np.count_nonzero(reference & candidate)
    total = np.count_nonzero(reference) + np.count_nonzero(candidate)
    union = np.count_nonzero(reference | candidate)
    dice = 1.0 if total == 0 else (2.0 * intersection / total)
    iou = 1.0 if union == 0 else (intersection / union)
    return float(dice), float(iou)
