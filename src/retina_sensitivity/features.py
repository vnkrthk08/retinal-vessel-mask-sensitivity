from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import skeletonize


def extract_mask_features(vessel_mask: np.ndarray, fov_mask: np.ndarray) -> dict[str, float]:
    fov = np.asarray(fov_mask, dtype=bool)
    vessel = np.asarray(vessel_mask, dtype=bool) & fov
    skeleton = skeletonize(vessel)
    structure = np.ones((3, 3), dtype=np.uint8)
    _, component_count = ndi.label(skeleton, structure=structure)
    neighbourhood = ndi.convolve(skeleton.astype(np.uint8), structure, mode="constant") - skeleton.astype(np.uint8)
    endpoint_pixels = int(np.count_nonzero(skeleton & (neighbourhood == 1)))
    junction_pixels = skeleton & (neighbourhood >= 3)
    _, junction_clusters = ndi.label(junction_pixels, structure=structure)
    fov_area = int(np.count_nonzero(fov))
    vessel_area = int(np.count_nonzero(vessel))
    return {
        "vessel_area_pixels": float(vessel_area),
        "vessel_area_fraction": float(vessel_area / fov_area) if fov_area else float("nan"),
        "skeleton_pixel_count": float(np.count_nonzero(skeleton)),
        "skeleton_component_count": float(component_count),
        "endpoint_pixel_count": float(endpoint_pixels),
        "junction_cluster_count": float(junction_clusters),
    }
