from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from retina_sensitivity.data import ensure_hrf_data

if __name__ == "__main__":
    result = ensure_hrf_data(ROOT)
    print(f"Validated HRF data: {result}")
