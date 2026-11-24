"""Train EfficientNet using group-isolated manifest splits and save held-out metrics.

Each split CSV must contain path,label,group. Labels: real_image,ai_generated.
Run prepare_splits.py first. Paths in CSV may be absolute or relative to the
repository root. This script does not read the bundled toy fixtures by default.
"""
import argparse,csv,json,random
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.utils.data import Dataset,DataLoader
from torchvision import transforms
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.ml.image_detector.model import EfficientNetDeepfakeDetector
from sklearn.metrics import classification_report,confusion_matrix,roc_auc_score

ROOT=Path(__file__).resolve().parents[2]
CLASS_TO_ID={"real_image":0,"ai_generated":1}

class ManifestImages(Dataset):
    def __init__(self,path,train=False):
        with path.open(encoding="utf-8-sig",newline="") as f: self.rows=list(csv.DictReader(f))
        if not self.rows or not {"path","label","group"}.issubset(self.rows[0]): raise ValueError(f"{path} needs path,label,group.")
        if any(r["label"] not in CLASS_TO_ID for r in self.rows): raise ValueError("Image labels must be real_image or ai_generated.")
        self.transform=transforms.Compose(([transforms.RandomHorizontalFlip()] if train else [])+[transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
        self.path=path
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        r=self.rows[i]; image_path=Path(r["path"])
        if not image_path.is_absolute(): image_path=(ROOT/image_path).resolve()
        with Image.open(image_path) as im: x=self.transform(im.convert("RGB"))
        return x,CLASS_TO_ID[r["label"]]

def load_split(folder,name,train=False):
    return ManifestImages(folder/f"{name}.csv",train)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--split-dir",required=True,type=Path); p.add_argument("--output",type=Path,default=Path("models/checkpoints/efficientnet_b0_external.pt")); p.add_argument("--report",type=Path,default=Path("models/checkpoints/image_metrics.json")); p.add_argument("--epochs",type=int,default=5); p.add_argument("--batch-size",type=int,default=16); p.add_argument("--allow-small-demo",action="store_true"); a=p.parse_args()
    parts={n:load_split(a.split_dir,n,n=="train") for n in ("train","validation","test")}
    counts=Counter(r["label"] for r in parts["train"].rows)
    for n,ds in parts.items():
        if {r["label"] for r in ds.rows}!={"real_image","ai_generated"}: raise ValueError(f"{n} split must contain both classes.")
    groups=[{r["group"] for r in ds.rows} for ds in parts.values()]
    if groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2]: raise ValueError("Group leakage detected.")
    if (len(parts["train"])<200 or min(counts.values())<50) and not a.allow_small_demo: raise ValueError("Too little data for a meaningful run; add data or pass --allow-small-demo for smoke testing.")
    seed=42; random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"); print(f"Training on {device}.")
    loaders={n:DataLoader(ds,batch_size=a.batch_size,shuffle=n=="train",num_workers=0) for n,ds in parts.items()}
    net=EfficientNetDeepfakeDetector(num_classes=2,pretrained=True)
    net=net.to(device); optimizer=torch.optim.AdamW(net.parameters(),lr=1e-4,weight_decay=1e-4); loss_fn=nn.CrossEntropyLoss()
    best_loss=float("inf"); best_state=None
    for epoch in range(a.epochs):
        net.train(); total=seen=0
        for x,y in loaders["train"]:
            x,y=x.to(device),y.to(device); optimizer.zero_grad(); loss=loss_fn(net(x),y); loss.backward(); optimizer.step(); total+=loss.item()*len(y); seen+=len(y)
        net.eval(); vtotal=vseen=0
        with torch.no_grad():
            for x,y in loaders["validation"]:
                x,y=x.to(device),y.to(device); loss=loss_fn(net(x),y); vtotal+=loss.item()*len(y); vseen+=len(y)
        vloss=vtotal/max(vseen,1); print(f"epoch {epoch+1}/{a.epochs}: train_loss={total/max(seen,1):.4f} validation_loss={vloss:.4f}")
        if vloss<best_loss: best_loss=vloss; best_state={k:v.detach().cpu().clone() for k,v in net.state_dict().items()}
    net.load_state_dict(best_state); net.eval()
    val_truth=[]; val_probs=[]
    with torch.no_grad():
        for x,y in loaders["validation"]:
            scores=torch.softmax(net(x.to(device)),dim=1).cpu().numpy(); val_probs.extend(scores[:,1].tolist()); val_truth.extend(y.numpy().tolist())
    negative_count=max(1,sum(label==0 for label in val_truth))
    candidates=sorted(set(val_probs+[1.0]))
    valid_thresholds=[t for t in candidates if sum(prob>=t and label==0 for prob,label in zip(val_probs,val_truth))/negative_count<=0.05]
    ai_threshold=min(valid_thresholds) if valid_thresholds else 1.0
    val_fpr=sum(prob>=ai_threshold and label==0 for prob,label in zip(val_probs,val_truth))/negative_count
    val_recall=sum(prob>=ai_threshold and label==1 for prob,label in zip(val_probs,val_truth))/max(1,sum(label==1 for label in val_truth))
    truth=[]; probs=[]
    with torch.no_grad():
        for x,y in loaders["test"]:
            scores=torch.softmax(net(x.to(device)),dim=1).cpu().numpy(); probs.extend(scores[:,1].tolist()); truth.extend(y.numpy().tolist())
    pred=[int(prob>=ai_threshold) for prob in probs]
    scope="small_demo_only" if len(parts["train"])<200 or min(counts.values())<50 else "external_dataset"
    a.output.parent.mkdir(parents=True,exist_ok=True); a.report.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"state_dict":best_state,"architecture":"EfficientNet-B0","classes":["real_image","ai_generated"],"epochs_trained":a.epochs,"input_resolution":[224,224],"evaluation_scope":scope,"ai_threshold":ai_threshold},a.output)
    report={"evaluation_scope":scope,"test_rows":len(truth),"per_class":classification_report(truth,pred,target_names=["real_image","ai_generated"],output_dict=True,zero_division=0),"confusion_matrix":confusion_matrix(truth,pred).tolist(),"roc_auc":roc_auc_score(truth,probs),"validation_threshold_target_fpr":0.05,"selected_ai_threshold":ai_threshold,"validation_fpr_at_threshold":val_fpr,"validation_recall_at_threshold":val_recall,"best_validation_loss":best_loss,"warning":"Image-source/generator composition bounds generalization; these metrics do not prove detection of new generators."}
    a.report.write_text(json.dumps(report,indent=2),encoding="utf-8"); print(f"Saved {a.output}; metrics {a.report}; scope={scope}")
if __name__=="__main__": main()
