"""Display saved held-out reports. This script never evaluates training fixtures.

Run the text/image training commands in docs/training-guide.md to produce reports.
"""
import json
from pathlib import Path

REPORTS = {
    "text classifier": Path(__file__).resolve().parents[1] / "models/checkpoints/text_classifier_external_metrics.json",
    "image classifier": Path(__file__).resolve().parents[1] / "models/checkpoints/image_metrics.json",
}

def main():
    for name, path in REPORTS.items():
        print(f"--- {name} ---")
        if not path.is_file():
            print("No held-out evaluation report is available. Train the model first.")
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read report: {exc}")
            continue
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
