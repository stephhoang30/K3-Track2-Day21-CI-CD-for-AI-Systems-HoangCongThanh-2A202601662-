# Báo cáo Lab Day 21 — CI/CD cho AI Systems

Hoàng Công Thành · 2A202601662 · K3 Track 2 · Cloud provider: **AWS** (S3 + EC2)

---

## 1. Siêu tham số đã chọn và lý do

Năm thí nghiệm ở Bước 1, huấn luyện trên `train_phase1.csv` (2998 mẫu), đánh giá trên `eval.csv` (500 mẫu held-out):

| Run | n_estimators | max_depth | min_samples_split | accuracy | f1_score |
|---|---|---|---|---|---|
| **4** | **200** | **20** | **2** | **0.6840** | **0.6832** |
| 5 | 300 | None | 10 | 0.6660 | 0.6641 |
| 3 | 200 | 10 | 5 | 0.6420 | 0.6394 |
| 1 | 100 | 5 | 2 | 0.5640 | 0.5534 |
| 2 | 50 | 3 | 2 | 0.5580 | 0.5185 |

Chọn run 4. `max_depth` là biến quyết định: tăng 3 → 20 kéo accuracy từ 0.558 lên 0.684, vì ranh giới giữa ba mức chất lượng rượu rất phi tuyến nên cây nông underfit. Nhưng bỏ giới hạn độ sâu mà kèm `min_samples_split=10` (run 5) lại tụt về 0.666 — ràng buộc này chặn cây tách ở vùng dữ liệu thưa, nơi chứa phần lớn mẫu lớp 2. Tăng `n_estimators` từ 200 lên 300 gần như không đổi kết quả, chỉ tốn thời gian huấn luyện.

## 2. So sánh Bước 2 và Bước 3

| Chỉ số | Bước 2 — 2998 mẫu | Bước 3 — 5996 mẫu |
|---|---|---|
| accuracy | 0.6840 | **0.7540** |
| f1_score | 0.6830 | **0.7534** |

Gấp đôi dữ liệu cho +7.0 điểm accuracy, cùng bộ siêu tham số. Xác nhận nút thắt ở giai đoạn này là lượng dữ liệu chứ không phải mô hình.

## 3. Hạ tầng đã dựng

| Thành phần | Giá trị |
|---|---|
| S3 bucket | `mlops-lab-244669245042`, đã chặn public access |
| DVC remote | `s3://mlops-lab-244669245042/dvc` |
| Model artifact | `s3://mlops-lab-244669245042/models/latest/model.pkl` |
| IAM user CI | `mlops-lab-ci` — đọc/ghi đúng một bucket |
| IAM role EC2 | `mlops-lab-ec2-role` — **chỉ đọc**, gắn qua instance profile |
| EC2 | `t3.micro`, Ubuntu 22.04, IP `3.239.208.69`, systemd `mlops-serve` |

VM không chứa bất kỳ access key nào: `boto3` lấy credentials từ IAM instance role qua instance metadata. Quyền của VM là chỉ-đọc, nên kể cả bị chiếm cũng không ghi đè được model.

## 4. Khó khăn gặp phải và cách giải quyết

**Không mô hình nào đạt ngưỡng 0.70 ở Bước 2.** Đã quét 36 cấu hình RandomForest và thử thêm ExtraTrees, HistGradientBoosting, GradientBoosting — trần trên 2998 mẫu là 0.684. Em giữ nguyên ngưỡng 0.70 theo đề thay vì hạ xuống cho vừa: kết quả là Bước 2 eval gate chặn deploy đúng như thiết kế, và Bước 3 với 5996 mẫu đạt 0.754 nên deploy tự động thành công. Đây chính là hành vi mong muốn của một quality gate.

**`mlflow 2.13` không import được.** Nó còn dùng `pkg_resources`, mà venv của pip đời mới không kèm `setuptools`. Thêm `setuptools<81` vào `requirements.txt`.

**`pytest` làm bẩn dữ liệu thí nghiệm.** Chạy test ghi run rác vào `mlflow.db` thật, và crash nếu thư mục `./mlruns` đã tồn tại từ lần chạy trước. Thêm `tests/conftest.py` trỏ MLflow vào thư mục tạm cho cả phiên test — test trở nên hermetic, chạy trên máy cá nhân và trên GitHub Actions runner cho kết quả như nhau.

**`apt` trên EC2 treo vô hạn.** DNS trả về chỉ địa chỉ IPv6 cho `us-east-1.ec2.archive.ubuntu.com` trong khi instance không có route IPv6. Ép IPv4 bằng `/etc/apt/apt.conf.d/99force-ipv4`.

**`aws login` và `boto3` không hiểu nhau.** AWS CLI v2 lưu credentials theo cơ chế `login_session` riêng, `boto3` (và do đó DVC) không đọc được nên `dvc push` báo "Unable to locate credentials". Xuất credentials tạm bằng `aws configure export-credentials --format env` trước khi chạy DVC.

**Push không kích hoạt được workflow.** Repo là một fork, GitHub chặn workflow chạy từ sự kiện `push` cho tới khi chủ repo bấm xác nhận trong tab Actions. Chẩn đoán bằng cách loại trừ: cả `src/**.py` lẫn `data/**.dvc` đều không trigger trong khi `workflow_dispatch` chạy bình thường, nên nguyên nhân không nằm ở bộ lọc `paths`. Sau khi bật, đã kiểm chứng lại bằng hai lần push liên tiếp — cả hai đều tự kích hoạt pipeline với `event=push`.

## 5. Bằng chứng

| Nội dung | Nơi kiểm chứng |
|---|---|
| 6 run MLflow, 5 cấu hình khác nhau | `mlflow ui --backend-store-uri sqlite:///mlflow.db` |
| Eval gate chặn deploy ở 0.6840, Deploy bị skip | Actions run `32452841624` — kích hoạt bởi `push` |
| Cả 4 job xanh trên 5996 mẫu, Deploy thành công | Actions run `32453084864` — kích hoạt bởi commit `c41a2a0` |
| Commit dữ liệu tự kích hoạt pipeline | Tên run `32453084864` chính là commit message `data: bổ sung 2998 mẫu dữ liệu mới (train_phase2)` |
| VM tự nạp model mới sau deploy | `journalctl -u mlops-serve` — 39.9 MB, thay cho bản 21.6 MB của 2998 mẫu |
| API trả kết quả | `curl http://3.239.208.69:8000/predict` |
