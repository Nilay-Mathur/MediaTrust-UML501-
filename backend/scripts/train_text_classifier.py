"""Train/evaluate a text classifier from CSV using group-held-out splits.

CSV columns: text,label,group. Group is a campaign/source/duplicate-family ID.
"""
import argparse,csv,json
from collections import Counter
from pathlib import Path
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report,confusion_matrix,f1_score
import re


def clean(text):
    return re.sub(r"\s+"," ",text.lower()).strip()


def read(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        rows=[r for r in csv.DictReader(f) if r.get("text","").strip() and r.get("label","").strip() and r.get("group","").strip()]
    if not rows or not {"text","label","group"}.issubset(rows[0]):
        raise ValueError("CSV needs non-empty text,label,group columns")
    if len({r["label"] for r in rows})<2 or len({r["group"] for r in rows})<10:
        raise ValueError("Need at least two classes and ten independent groups")
    return rows


def model(c):
    return Pipeline([("vectorizer",TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=20000,token_pattern=r"(?u)\b\w+\b|\$|\%")),("classifier",LogisticRegression(C=c,max_iter=1500,class_weight="balanced",random_state=42))])


def split(rows,seed):
    y=[r["label"] for r in rows]; g=[r["group"] for r in rows]; classes=set(y)
    for n in range(100):
        a,b=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=seed+n).split(rows,y,g))
        rem=[rows[i] for i in a]; yr=[y[i] for i in a]; gr=[g[i] for i in a]
        c,d=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=seed+1000+n).split(rem,yr,gr))
        parts=[[rem[i] for i in c],[rem[i] for i in d],[rows[i] for i in b]]
        if all({r["label"] for r in p}==classes for p in parts):
            return parts
    raise ValueError("Could not place every class in each split; add independent groups per class")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-csv",required=True,type=Path)
    p.add_argument("--model-out",type=Path,default=Path("models/checkpoints/text_classifier_external.joblib"))
    p.add_argument("--report-out",type=Path,default=Path("models/checkpoints/text_classifier_external_metrics.json"))
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--allow-small-demo",action="store_true")
    a=p.parse_args(); rows=read(a.input_csv); train,val,test=split(rows,a.seed)
    counts=Counter(r["label"] for r in train)
    if (len(train)<200 or min(counts.values())<30) and not a.allow_small_demo:
        raise ValueError("Dataset too small for a meaningful run; add data or use --allow-small-demo for a smoke check")
    labels=sorted(counts)
    best=(-1,None)
    for c in (.25,.5,1.,2.,4.):
        m=model(c); m.fit([clean(r["text"]) for r in train],[r["label"] for r in train])
        score=f1_score([r["label"] for r in val],m.predict([clean(r["text"]) for r in val]),average="macro",zero_division=0)
        print(f"validation macro-F1 C={c}: {score:.4f}")
        if score>best[0]: best=(score,c)
    fit=train+val; final=model(best[1]); final.fit([clean(r["text"]) for r in fit],[r["label"] for r in fit])
    yt=[r["label"] for r in test]; yp=final.predict([clean(r["text"]) for r in test])
    groups=[{r["group"] for r in part} for part in (train,val,test)]
    if groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2]: raise ValueError("Group leakage in split")
    scope="small_demo_only" if len(fit)<200 or min(Counter(r["label"] for r in fit).values())<30 else "external_dataset"
    final.mediatrust_model_version_="text-tfidf-logreg-v2"
    final.mediatrust_evaluation_scope_=scope
    a.model_out.parent.mkdir(parents=True,exist_ok=True); a.report_out.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(final,a.model_out)
    report={"version":final.mediatrust_model_version_,"evaluation_scope":scope,"selected_C":best[1],"validation_macro_f1":best[0],"test":{"rows":len(test),"macro_f1":f1_score(yt,yp,average="macro",zero_division=0),"per_class":classification_report(yt,yp,output_dict=True,zero_division=0),"confusion_matrix_labels":labels,"confusion_matrix":confusion_matrix(yt,yp,labels=labels).tolist()},"rows":{k:len(v) for k,v in (("train",train),("validation",val),("test",test))},"warning":"Metrics describe only this dataset; they do not establish real-world detection quality."}
    a.report_out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("Model:",a.model_out); print("Test report:",a.report_out); print("Scope:",scope)

if __name__=="__main__": main()
