"""Build an image manifest from extracted CIFAKE train/test folders.

Expected folders: train/REAL, train/FAKE, test/REAL, test/FAKE.
This dataset is a limited CIFAR-10/Stable-Diffusion benchmark, not a modern
web-photo benchmark.
"""
import argparse,csv,hashlib
from pathlib import Path

EXTS={".jpg",".jpeg",".png",".webp"}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset-root",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args(); root=a.dataset_root.resolve()
    rows=[]; seen={}
    for split in ("train","test"):
        for folder,label in (("REAL","real_image"),("FAKE","ai_generated")):
            directory=root/split/folder
            if not directory.is_dir(): raise FileNotFoundError(f"Expected folder: {directory}")
            for path in directory.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in EXTS: continue
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                if digest in seen and seen[digest]!=label: raise ValueError(f"Same image has conflicting labels: {path}")
                seen[digest]=label
                rows.append({"path":str(path),"label":label,"group":digest})
    if not rows: raise ValueError("No images found.")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["path","label","group"]); w.writeheader(); w.writerows(rows)
    print(f"Manifest: {len(rows)} images. Exact byte duplicates share a group.")
    print("Source-held-out generator evaluation is still required for generalization claims.")
if __name__=="__main__": main()
