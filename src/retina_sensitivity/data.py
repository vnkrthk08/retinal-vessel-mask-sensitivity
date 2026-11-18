from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request

from .network import open_verified_url
from zipfile import ZipFile, BadZipFile
import shutil
import tempfile

import numpy as np
from PIL import Image

HRF_URL = "https://www5.cs.fau.de/fileadmin/research/datasets/fundus-images/all.zip"
HRF_SOURCE = "https://www5.cs.fau.de/research/data/fundus-images/"


@dataclass
class RetinalSample:
    dataset: str
    image_id: str
    image: np.ndarray
    vessel_mask: np.ndarray
    fov_mask: np.ndarray
    group: str = "unknown"


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "retinal-feature-stability/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with open_verified_url(request, timeout=90) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if not temporary.exists() or temporary.stat().st_size == 0:
            raise RuntimeError("The dataset download returned an empty file.")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _safe_extract(archive: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    with ZipFile(archive) as zf:
        for member in zf.infolist():
            resolved = (target / member.filename).resolve()
            if root != resolved and root not in resolved.parents:
                raise RuntimeError("Unsafe path detected in dataset archive.")
        zf.extractall(target)


def _find_hrf_root(search_root: Path) -> Path | None:
    for image_dir in search_root.rglob("images"):
        parent = image_dir.parent
        if (parent / "manual1").is_dir() and (parent / "mask").is_dir():
            return parent
    return None


def _valid_hrf_root(root: Path) -> bool:
    if not all((root / name).is_dir() for name in ("images", "manual1", "mask")):
        return False
    images = [p for p in (root / "images").iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}]
    manual = [p for p in (root / "manual1").iterdir() if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}]
    return len(images) == 45 and len(manual) >= 45


def ensure_hrf_data(project_root: Path | str) -> Path:
    project_root = Path(project_root).resolve()
    root = project_root / "data" / "HRF"
    if _valid_hrf_root(root):
        return root

    raw_dir = project_root / "data" / "raw"
    archive = raw_dir / "hrf_all.zip"
    if not archive.exists() or archive.stat().st_size == 0:
        print(f"Downloading the official HRF archive from {HRF_SOURCE}")
        _download(HRF_URL, archive)

    try:
        with ZipFile(archive) as zf:
            bad_member = zf.testzip()
            if bad_member:
                raise BadZipFile(f"Corrupt archive member: {bad_member}")
    except BadZipFile as exc:
        archive.unlink(missing_ok=True)
        raise RuntimeError("The HRF archive is invalid. Run the downloader again.") from exc

    with tempfile.TemporaryDirectory(prefix="hrf_extract_", dir=raw_dir) as temp:
        extracted = Path(temp)
        _safe_extract(archive, extracted)
        found = _find_hrf_root(extracted)
        if found is None or not _valid_hrf_root(found):
            raise RuntimeError("The archive structure did not contain 45 images, manual1 vessel masks and FOV masks.")
        if root.exists():
            shutil.rmtree(root)
        shutil.copytree(found, root)

    if not _valid_hrf_root(root):
        raise RuntimeError("HRF validation failed after extraction.")
    return root


def _image_map(folder: Path, extensions: set[str]) -> dict[str, Path]:
    return {p.stem.lower(): p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in extensions}


def load_hrf_sample(root: Path | str, image_id: str) -> RetinalSample:
    root = Path(root)
    images = _image_map(root / "images", {".jpg", ".jpeg"})
    masks = _image_map(root / "manual1", {".tif", ".tiff"})
    fovs = _image_map(root / "mask", {".tif", ".tiff"})
    key = image_id.lower()
    fov_key = f"{key}_mask"
    if key not in images or key not in masks or fov_key not in fovs:
        raise FileNotFoundError(f"Missing paired HRF files for {image_id}.")
    image = np.asarray(Image.open(images[key]).convert("RGB"), dtype=np.uint8)
    vessel = np.asarray(Image.open(masks[key]).convert("L")) >= 128
    fov = np.asarray(Image.open(fovs[fov_key]).convert("L")) >= 128
    if image.shape[:2] != vessel.shape or vessel.shape != fov.shape:
        raise ValueError(f"Image, vessel mask and FOV dimensions differ for {image_id}.")
    group = "healthy" if key.endswith("_h") else "glaucoma" if key.endswith("_g") else "diabetic_retinopathy" if key.endswith("_dr") else "unknown"
    return RetinalSample("HRF", image_id, image, vessel, fov, group)


def iter_hrf_samples(root: Path | str):
    root = Path(root)
    image_dir = root / "images"
    paths = sorted(p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"})
    if len(paths) != 45:
        raise RuntimeError(f"Expected 45 HRF images, found {len(paths)}. Run scripts/download_data.py.")
    for path in paths:
        yield load_hrf_sample(root, path.stem)
