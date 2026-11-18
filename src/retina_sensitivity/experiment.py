from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .data import iter_hrf_samples
from .features import extract_mask_features
from .perturbations import make_perturbations, overlap_metrics

FEATURES = [
    "vessel_area_pixels",
    "vessel_area_fraction",
    "skeleton_pixel_count",
    "skeleton_component_count",
    "endpoint_pixel_count",
    "junction_cluster_count",
]


def run_experiment(hrf_root: Path | str, output_dir: Path | str, sample_limit: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir = Path(output_dir)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    records = []

    for index, sample in enumerate(iter_hrf_samples(hrf_root)):
        if sample_limit is not None and index >= sample_limit:
            break
        variants = make_perturbations(sample.vessel_mask, sample.fov_mask)
        baseline = extract_mask_features(variants["original"], sample.fov_mask)
        for condition, candidate in variants.items():
            measured = baseline if condition == "original" else extract_mask_features(candidate, sample.fov_mask)
            dice, iou = overlap_metrics(variants["original"], candidate)
            row = {
                "dataset": sample.dataset,
                "image_id": sample.image_id,
                "group": sample.group,
                "condition": condition,
                "dice_vs_original": dice,
                "iou_vs_original": iou,
            }
            row.update(measured)
            for feature in FEATURES:
                denominator = baseline[feature]
                row[f"{feature}_change_pct"] = (
                    0.0 if condition == "original" else
                    (100.0 * (measured[feature] - denominator) / denominator if denominator else np.nan)
                )
            records.append(row)

    per_image = pd.DataFrame.from_records(records)
    if per_image.empty:
        raise RuntimeError("No HRF samples were processed.")
    per_image.to_csv(output_dir / "per_image_features.csv", index=False)
    change_columns = [f"{feature}_change_pct" for feature in FEATURES]
    summary = per_image.groupby("condition", sort=False).agg(
        images=("image_id", "nunique"),
        mean_dice=("dice_vs_original", "mean"),
        mean_iou=("iou_vs_original", "mean"),
        **{column: (column, "mean") for column in change_columns},
    ).reset_index()
    summary.to_csv(output_dir / "summary.csv", index=False)
    _plot_summary(summary, figures_dir)
    return per_image, summary


def _plot_summary(summary: pd.DataFrame, figures_dir: Path) -> None:
    order = ["original", "erosion_r1", "erosion_r2", "dilation_r1", "dilation_r2"]
    summary = summary.set_index("condition").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(summary["condition"], summary["mean_dice"])
    ax.set_ylabel("Dice overlap with original mask")
    ax.set_ylim(0, 1.02)
    ax.tick_params(axis="x", rotation=20)
    ax.set_title("Mask overlap under controlled morphological perturbations")
    fig.tight_layout()
    fig.savefig(figures_dir / "mask_overlap.png", dpi=180)
    plt.close(fig)

    features = ["vessel_area_pixels_change_pct", "skeleton_pixel_count_change_pct", "skeleton_component_count_change_pct", "endpoint_pixel_count_change_pct", "junction_cluster_count_change_pct"]
    labels = ["Vessel area", "Skeleton pixels", "Components", "Endpoints", "Junction clusters"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(features))
    width = 0.16
    for i, condition in enumerate(order[1:]):
        values = summary.loc[summary["condition"] == condition, features].to_numpy().ravel()
        ax.bar(x + (i - 1.5) * width, values, width, label=condition)
    ax.axhline(0, linewidth=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Mean change from original (%)")
    ax.set_title("Sensitivity of vascular measurements")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "feature_sensitivity.png", dpi=180)
    plt.close(fig)
