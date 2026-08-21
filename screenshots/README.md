# Ảnh chụp bằng chứng

Ánh xạ sang rubric chấm điểm:

| Ảnh | Nội dung | Tiêu chí | Điểm |
|---|---|---|---|
| `01-mlflow-runs.png` | MLflow UI, 8 run sắp xếp theo `accuracy` giảm dần | Bước 1 — MLflow tracking | 12 |
| `02-mlflow-compare.png` | Compare 5 run: bảng siêu tham số + `accuracy` + `f1_score` | Bước 1 — Độ đo | 8 |
| `03-actions-eval-blocked.png` | Run #5, `Triggered via push`, Eval đỏ chặn Deploy | Bước 2 — Eval gate | 4 |
| `04-actions-all-green.png` | Run #6, `Triggered via push`, cả 4 job xanh, tiêu đề là commit dữ liệu | Bước 2 — CI/CD · Bước 3 — Tự động hóa | 16 + 12 |
| `05-api-curl.png` | `GET /health`, `POST /predict` hợp lệ, và `POST /predict` sai định dạng | Bước 2 — Serving | 12 |
| `06-s3-bucket.png` | Nội dung bucket: 4 object DVC + `models/latest/model.pkl` | Bước 2 — DVC | 12 |

## Cách tạo lại

Ảnh 01 và 02 chụp từ MLflow UI cục bộ:

```bash
.venv/bin/mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Ảnh 03 và 04 chụp từ trang công khai của GitHub Actions, nên hiện nút
"Sign in to view logs" — trạng thái bốn job vẫn đọc được đầy đủ. Muốn ảnh có
cả log thì mở hai run đó trong trình duyệt đã đăng nhập và chụp lại.

Ảnh 05 và 06 là kết xuất của output thật từ `curl` và `aws s3 ls`, không phải
ảnh chụp cửa sổ terminal. Nội dung là output nguyên văn tại thời điểm chạy,
có kèm mốc thời gian UTC trong ảnh 05.

## Còn thiếu

Rubric yêu cầu ảnh **AWS S3 Console**. Ảnh `06` là bản liệt kê qua CLI, tương
đương về nội dung nhưng khác giao diện. Muốn đúng chữ của đề thì đăng nhập
console và chụp màn hình bucket:

https://s3.console.aws.amazon.com/s3/buckets/mlops-lab-244669245042
