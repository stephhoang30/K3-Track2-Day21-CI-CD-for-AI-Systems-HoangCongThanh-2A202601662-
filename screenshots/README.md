# Ảnh chụp bằng chứng

Ánh xạ sang rubric chấm điểm:

| Ảnh | Nội dung | Tiêu chí | Điểm |
|---|---|---|---|
| `01-mlflow-runs.png` | MLflow UI, 8 run sắp xếp theo `accuracy` giảm dần | Bước 1 — MLflow tracking | 12 |
| `02-mlflow-compare.png` | Compare 5 run: bảng siêu tham số + `accuracy` + `f1_score` | Bước 1 — Độ đo | 8 |
| `03-actions-eval-blocked.png` | Run #5, `Triggered via push`, Eval đỏ chặn Deploy | Bước 2 — Eval gate | 4 |
| `04-actions-all-green.png` | Run #6, `Triggered via push`, cả 4 job xanh, tiêu đề là commit dữ liệu | Bước 2 — CI/CD · Bước 3 — Tự động hóa | 16 + 12 |
| `05-api-curl.png` | `GET /health`, `POST /predict` hợp lệ, và `POST /predict` sai định dạng | Bước 2 — Serving | 12 |
| `06-s3-bucket.png` | Liệt kê toàn bộ bucket qua CLI: 4 object DVC + `models/latest/model.pkl`, kèm dung lượng | Bước 2 — DVC | 12 |
| `07-s3-console-model.png` | S3 Console, `models/latest/` — `model.pkl`, 39.9 MB | Bước 2 — DVC | 12 |
| `08-s3-console-dvc.png` | S3 Console, `dvc/files/md5/` — 4 thư mục băm `4b/ 64/ 97/ b5/` | Bước 2 — DVC | 12 |

## Đọc ảnh 06 và 08 thế nào

DVC lưu theo nội dung (content-addressed), nên trên S3 tên object là mã băm md5
chứ không phải `train_phase1.csv`. Đối chiếu với `data/*.dvc` trong repo:

| Băm | Ứng với |
|---|---|
| `97f98bd0…` | `train_phase1.csv` — bản 2998 mẫu (Bước 2) |
| `64c88e83…` | `train_phase1.csv` — bản 5996 mẫu (Bước 3) |
| `b5762308…` | `eval.csv` — 500 mẫu, không đổi |
| `4b1632d3…` | `train_phase2.csv` — 2998 mẫu |

Hai băm đầu là hai phiên bản của cùng một file. Đó chính là thứ DVC làm: git giữ
con trỏ, S3 giữ nội dung, mỗi lần dữ liệu đổi thì sinh một object mới mà bản cũ
vẫn còn nguyên để tái tạo lại được.

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

Ảnh 07 và 08 chụp trực tiếp từ AWS S3 Console.
