import numpy as np
from retina_sensitivity.features import extract_mask_features
from retina_sensitivity.perturbations import make_perturbations, overlap_metrics


def test_perturbations_preserve_shape_and_fov():
    mask = np.zeros((64, 64), dtype=bool)
    mask[10:54, 30:34] = True
    mask[28:32, 10:54] = True
    fov = np.ones_like(mask)
    fov[:4] = False
    variants = make_perturbations(mask, fov)
    assert set(variants) == {"original", "erosion_r1", "erosion_r2", "dilation_r1", "dilation_r2"}
    assert all(value.shape == mask.shape for value in variants.values())
    assert all(not np.any(value & ~fov) for value in variants.values())
    assert np.count_nonzero(variants["erosion_r1"]) < np.count_nonzero(mask)
    assert np.count_nonzero(variants["dilation_r1"]) >= np.count_nonzero(mask)


def test_overlap_and_feature_metrics():
    mask = np.zeros((64, 64), dtype=bool)
    mask[8:56, 31:33] = True
    mask[30:33, 12:52] = True
    fov = np.ones_like(mask)
    dice, iou = overlap_metrics(mask, mask)
    features = extract_mask_features(mask, fov)
    assert dice == 1.0 and iou == 1.0
    assert features["vessel_area_pixels"] > 0
    assert features["skeleton_pixel_count"] > 0
    assert features["skeleton_component_count"] >= 1
