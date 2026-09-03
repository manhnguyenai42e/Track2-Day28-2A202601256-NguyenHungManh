# CHANGELOG

Tất cả thay đổi đáng kể, sửa lỗi, quyết định kiến trúc của repo được ghi lại ở đây.
Entry mới nhất luôn nằm ở trên cùng.

---

### 2026-09-03 — Dựng Full Stack Docker, vượt qua 56/56 e2e integration tests & thu thập trọn bộ evidence

| Mục | Chi tiết |
|---|---|
| **Lỗi / Yêu cầu** | Cần khởi chạy toàn bộ 14 containers (Core + Spark Connect + Airflow), xác minh toàn bộ hành trình tích hợp end-to-end không cần GPU và thu thập đủ 10 bằng chứng integration points theo `SUBMISSION.md`. |
| **Nguyên nhân gốc** | Windows console gặp vấn đề encoding UTF-8 khi MLflow xuất ký tự unicode (runner emoji), `load-tests/run_profile.py` chưa bắt HTTPError khiến status 429 bị tính thành 0, và Airflow DAG cần thời gian khởi tạo Spark Delta connect session lần đầu. |
| **Giải pháp** | 1. Chạy CLI với `$env:PYTHONUTF8="1"` bảo đảm tương thích Unicode trên Windows.<br>2. Sửa `load-tests/run_profile.py` bắt `urllib.error.HTTPError` để ghi nhận chính xác HTTP 429 khi kích hoạt Gateway rate limit.<br>3. Chạy toàn bộ luồng checkpoint: `lab28 index`, `lab28 release`, `lab28 seed`, `lab28 ready`, `lab28 evidence`. |
| **Kiểm chứng** | - `integration-tests -m "not gpu and not langsmith"`: 56/56 passed.<br>- `load-tests/run_profile.py`: 200 requests (28 x 200 OK, 172 x 429 Rate-limited), P50 = 5.18ms, P95 = 564.7ms.<br>- Thu thập đủ 12 file trong `evidence/` (`ip01` đến `ip10` và `integration-report.json`).<br>- Kubernetes & GitOps manifests validation: Passed. |

---

### 2026-09-03 — Hoàn thiện 4 hàm integration tasks cốt lõi (IP01, IP03, IP04, IP07, IP08, IP10)

| Mục | Chi tiết |
|---|---|
| **Lỗi / Yêu cầu** | 4 hàm ban đầu trong `src/lab28_platform/integration_tasks.py` ném `NotImplementedError` khiến 4 `starter-tests` và các bài kiểm tra Delta MERGE, Feast, Readiness fail. |
| **Nguyên nhân gốc** | Scaffold khởi tạo ban đầu để trống 4 điểm kết nối quan trọng do học viên tự triển khai: (1) đóng gói Kafka headers, (2) deduplicate sự kiện cho Delta MERGE, (3) format payload Feast online request, (4) phân cấp mức độ sẵn sàng probe. |
| **Giải pháp** | 1. `event_headers`: Luôn gửi `idempotency-key` (bytes). Bổ sung `traceparent` (bytes) nếu có trace context; bỏ qua khi không có trace.<br>2. `dedupe_latest`: Nhóm các sự kiện theo `idempotency_key`, giữ bản ghi có `(occurred_at, event_id)` lớn nhất, sắp xếp kết quả theo thứ tự key tăng dần để đảm bảo tính tất định.<br>3. `feast_online_request`: Chuẩn bị request body cho `asker_activity_v1` với `entities={"asker_id": [asker_id]}`, `features=list(FEATURE_REFS)` và `full_feature_names=False`.<br>4. `readiness_status`: Ưu tiên kiểm tra thất bại: nếu có probe `mandatory=True` fail $\rightarrow$ `not_ready`; nếu chỉ có probe `mandatory=False` fail $\rightarrow$ `degraded`; ngược lại $\rightarrow$ `ready`. |
| **Kiểm chứng** | - `starter-tests`: 4/4 passed.<br>- `tests/test_delta_merge_idempotency.py`: 22/22 passed.<br>- `tests/`: 83/83 passed.<br>- `ruff check`: All checks passed.<br>- `scripts/verify_matrix.py`: 245/245 checks passed.<br>- `scripts/check_portability.py`: Passed.<br>- `scripts/validate_manifests.py`: Passed. |
