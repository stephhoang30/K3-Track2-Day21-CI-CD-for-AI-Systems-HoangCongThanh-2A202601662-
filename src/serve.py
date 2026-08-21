from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import joblib
import os

app = FastAPI()

S3_BUCKET = os.environ["S3_BUCKET"]
S3_MODEL_KEY = os.environ.get("S3_MODEL_KEY", "models/latest/model.pkl")
MODEL_PATH = os.path.expanduser("~/models/model.pkl")

LABELS = {0: "thap", 1: "trung_binh", 2: "cao"}


def download_model():
    """
    Tai file model.pkl tu S3 ve may khi server khoi dong.

    Ham nay duoc goi mot lan khi module duoc import. boto3 tu tim credentials
    theo thu tu: bien moi truong -> ~/.aws/credentials -> IAM role cua EC2
    instance. Cach sach nhat tren EC2 la gan IAM instance profile, khong can
    copy key nao len VM.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    s3 = boto3.client("s3")
    s3.download_file(S3_BUCKET, S3_MODEL_KEY, MODEL_PATH)

    size_mb = os.path.getsize(MODEL_PATH) / 1024 / 1024
    print(f"Da tai model tu s3://{S3_BUCKET}/{S3_MODEL_KEY} ({size_mb:.1f} MB)")


download_model()
model = joblib.load(MODEL_PATH)


class PredictRequest(BaseModel):
    features: list[float]


@app.get("/health")
def health():
    """
    Endpoint kiem tra suc khoe server.
    GitHub Actions goi endpoint nay sau khi deploy de xac nhan server dang chay.
    """
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    """
    Endpoint suy luan chinh.

    Dau vao : JSON {"features": [f1, f2, ..., f12]}
    Dau ra  : JSON {"prediction": <0|1|2>, "label": <"thap"|"trung_binh"|"cao">}

    Thu tu 12 dac trung:
        fixed_acidity, volatile_acidity, citric_acid, residual_sugar,
        chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density,
        pH, sulphates, alcohol, wine_type
    """
    if len(req.features) != 12:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 12 features (wine quality), got {len(req.features)}",
        )

    pred = int(model.predict([req.features])[0])
    return {"prediction": pred, "label": LABELS[pred]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
