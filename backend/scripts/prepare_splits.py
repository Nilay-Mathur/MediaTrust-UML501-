"""Group-isolated deterministic splits for a CSV manifest with label,group columns."""
import argparse,csv
from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-csv",required=True,type=Path); p.add_argument("--output-dir",required=True,type=Path); p.add_argument("--seed",type=int,default=42); a=p.parse_args()
    with a.input_csv.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f); rows=list(reader); fields=reader.fieldnames or []
    if not rows or not {"label","group"}.issubset(fields): raise ValueError("CSV must have label and group columns plus task data.")
    rows=[r for r in rows if r["label"].strip() and r["group"].strip()]
    labels=[r["label"].strip() for r in rows]; groups=[r["group"].strip() for r in rows]; classes=set(labels)
    if len(classes)<2 or len(set(groups))<10: raise ValueError("Need at least 2 classes and 10 distinct source/campaign groups.")
    parts=None
    for n in range(100):
        trainval,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=a.seed+n).split(rows,labels,groups))
        rem=[rows[i] for i in trainval]; ry=[labels[i] for i in trainval]; rg=[groups[i] for i in trainval]
        tr,va=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=a.seed+1000+n).split(rem,ry,rg))
        candidate=[[rem[i] for i in tr],[rem[i] for i in va],[rows[i] for i in test]]
        if all({r["label"].strip() for r in q}==classes for q in candidate):
            gs=[{r["group"].strip() for r in q} for q in candidate]
            if not (gs[0]&gs[1] or gs[0]&gs[2] or gs[1]&gs[2]): parts=candidate; break
    if parts is None: raise ValueError("Could not place every class in all splits. Add independent groups per class.")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for name,part in zip(("train","validation","test"),parts):
        with (a.output_dir/f"{name}.csv").open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(part)
        print(f"{name}: {len(part)} rows")
    print("Group isolation verified. Never tune on test.csv.")
if __name__=="__main__": main()
