"""Convert the official UCI tab-separated SMS corpus to MediaTrust CSV."""
import argparse,csv,hashlib,re
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--input",required=True,type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args()
    rows=[]
    with a.input.open(encoding="utf-8",errors="replace") as f:
        for line in f:
            label,sep,text=line.rstrip("\n").partition("\t")
            if not sep or label not in {"ham","spam"}: continue
            normalized=re.sub(r"\W+"," ",text.lower()).strip()
            group=hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            rows.append({"text":text,"label":"benign" if label=="ham" else "scam_fraud","group":group})
    if not rows: raise ValueError("No ham/spam rows found. Select the UCI file named SMSSpamCollection.")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["text","label","group"]); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {a.output}; labels: ham->benign, spam->scam_fraud.")
    print("This binary SMS corpus does not train phishing-vs-impersonation categories.")
if __name__=="__main__": main()
