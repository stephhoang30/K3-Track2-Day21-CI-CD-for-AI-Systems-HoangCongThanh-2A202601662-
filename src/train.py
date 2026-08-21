import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
import json
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

EVAL_THRESHOLD = 0.70

# Ty le toi thieu cua mot lop truoc khi coi la lech phan phoi (Bonus 5)
MIN_CLASS_RATIO = 0.10

# Cac thuat toan duoc ho tro qua tham so model_type trong params.yaml (Bonus 2)
MODEL_REGISTRY = {
    "random_forest": RandomForestClassifier,
    "gradient_boosting": GradientBoostingClassifier,
    "logistic_regression": LogisticRegression,
}

CLASS_LABELS = {0: "thap", 1: "trung_binh", 2: "cao"}


def build_model(model_type: str, params: dict):
    """
    Khoi tao mo hinh theo model_type, chi truyen nhung tham so ma thuat toan do
    thuc su chap nhan. Nho vay doi model_type khong can sua lai params.yaml.
    """
    if model_type not in MODEL_REGISTRY:
        raise ValueError(
            f"model_type '{model_type}' khong ho tro. "
            f"Chon mot trong: {sorted(MODEL_REGISTRY)}"
        )

    cls = MODEL_REGISTRY[model_type]
    accepted = cls().get_params().keys()

    kwargs = {k: v for k, v in params.items() if k in accepted}
    ignored = sorted(set(params) - set(kwargs))
    if ignored:
        print(f"Bo qua tham so khong hop le voi {model_type}: {ignored}")

    if "random_state" in accepted:
        kwargs.setdefault("random_state", 42)

    return cls(**kwargs)


def check_label_distribution(y) -> dict:
    """
    Tinh ty le tung nhan trong tap huan luyen va canh bao neu co lop qua hiem.

    Lop qua hiem lam mo hinh gan nhu khong bao gio du doan ra lop do, trong khi
    accuracy tong the van dep - nen phai canh bao truoc khi huan luyen (Bonus 5).
    """
    ratios = y.value_counts(normalize=True).sort_index()
    dist = {str(k): round(float(v), 4) for k, v in ratios.items()}

    print(f"Phan bo nhan tap huan luyen: {dist}")
    for label, ratio in dist.items():
        if ratio < MIN_CLASS_RATIO:
            name = CLASS_LABELS.get(int(label), label)
            print(
                f"CANH BAO LECH DU LIEU: lop {label} ({name}) chi chiem "
                f"{ratio:.2%}, duoi nguong {MIN_CLASS_RATIO:.0%}."
            )
    return dist


def write_report(y_true, y_pred, params: dict, dist: dict) -> str:
    """
    Ghi bao cao hieu suat dang van ban: confusion matrix va precision/recall
    cho tung lop (Bonus 3). File nay duoc upload lam artifact trong CI.
    """
    names = [CLASS_LABELS[c] for c in sorted(CLASS_LABELS)]
    cm = confusion_matrix(y_true, y_pred, labels=sorted(CLASS_LABELS))

    lines = ["BAO CAO HIEU SUAT MO HINH", "=" * 60, "", "Sieu tham so:"]
    lines += [f"  {k}: {v}" for k, v in params.items()]
    lines += ["", "Phan bo nhan tap huan luyen:"]
    lines += [
        f"  lop {k} ({CLASS_LABELS.get(int(k), k)}): {v:.2%}"
        for k, v in dist.items()
    ]

    lines += ["", "Confusion matrix (hang = that, cot = du doan):", ""]
    header = " " * 14 + "".join(f"{n:>14}" for n in names)
    lines.append(header)
    for name, row in zip(names, cm):
        lines.append(f"{name:>14}" + "".join(f"{v:>14}" for v in row))

    lines += ["", "Precision / recall / f1 tung lop:", ""]
    lines.append(
        classification_report(
            y_true, y_pred, labels=sorted(CLASS_LABELS),
            target_names=names, digits=4, zero_division=0,
        )
    )

    os.makedirs("outputs", exist_ok=True)
    report = "\n".join(lines)
    with open("outputs/report.txt", "w") as f:
        f.write(report)
    return report


def train(
    params: dict,
    data_path: str = "data/train_phase1.csv",
    eval_path: str = "data/eval.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.

    Tham so:
        params     : dict sieu tham so. Khoa model_type (tuy chon) chon thuat
                     toan; cac khoa con lai la sieu tham so cua thuat toan do.
        data_path  : duong dan den file du lieu huan luyen.
        eval_path  : duong dan den file du lieu danh gia.

    Tra ve:
        accuracy (float): do chinh xac tren tap danh gia.
    """

    params = dict(params)
    model_type = params.pop("model_type", "random_forest")

    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    dist = check_label_distribution(y_train)

    with mlflow.start_run():

        mlflow.log_params(params)
        mlflow.log_param("model_type", model_type)

        model = build_model(model_type, params)
        model.fit(X_train, y_train)

        preds = model.predict(X_eval)
        acc = float(accuracy_score(y_eval, preds))
        f1 = float(f1_score(y_eval, preds, average="weighted"))

        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        for label, ratio in dist.items():
            mlflow.log_metric(f"train_ratio_class_{label}", ratio)
        mlflow.sklearn.log_model(model, "model")

        print(f"Accuracy: {acc:.4f} | F1: {f1:.4f} | model_type: {model_type}")

        report = write_report(y_eval, preds, {**params, "model_type": model_type}, dist)
        mlflow.log_artifact("outputs/report.txt")
        print()
        print(report)

        # File nay duoc doc boi GitHub Actions o Buoc 2
        with open("outputs/metrics.json", "w") as f:
            json.dump(
                {
                    "accuracy": acc,
                    "f1_score": f1,
                    "model_type": model_type,
                    "label_distribution": dist,
                },
                f,
            )

        # File nay duoc upload len cloud storage o Buoc 2
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.pkl")

    return acc


if __name__ == "__main__":
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)
