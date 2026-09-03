# ANSWERS.md — Day 28 Track 2: Platform Integration & Production Readiness

**Thành viên thực hiện:** Nguyễn Hùng Mạnh (`2A202601256`)  
**Repository:** `nhmanhDev/Track2-Day28-2A202601256-NguyenHungManh`  
**Ngày thực hiện:** 2026-09-03  

---

## 1. Trade-offs (Các quyết định đánh đổi kiến trúc)

### 1.1. Ingestion & Messaging (Kafka Header vs Body & Idempotency)
- **Đánh đổi:** Mang `idempotency-key` và W3C `traceparent` trong Kafka Record Headers thay vì đóng gói sâu trong message body JSON.
- **Lợi ích:** Consumer và Kafka router có thể kiểm tra deduplication, định tuyến và phân tích OpenTelemetry trace context mà không cần deserialize toàn bộ payload JSON nặng (zero-payload serialization cost).
- **Hạn chế:** Các hệ thống message broker cũ hoặc các công cụ ingest không hỗ trợ record header chuẩn sẽ cần adapter layer.

### 1.2. Lakehouse Idempotency (Delta MERGE vs Append-Only + Deduplication on Read)
- **Đánh đổi:** Sử dụng Spark Delta MERGE theo khóa tổng hợp `(occurred_at, event_id)` trên `idempotency_key` ngay trong pipeline Airflow thay vì ghi Append-only đơn giản.
- **Lợi ích:** Đảm bảo tính toán idempotent tuyệt đối khi Kafka consumer replay hoặc pipeline crash retry (không nhân bản dòng, đảm bảo trạng thái đích đơn trị). Bật time travel để audit và rollback lịch sử bảng.
- **Hạn chế:** MERGE tốn chi phí I/O ghi commit log `_delta_log` và rewrite Parquet files lớn hơn so với ghi nối đuôi (append-only stream).

### 1.3. Feature Store (Offline Batch Snapshot vs Realtime Streaming Ingestion)
- **Đánh đổi:** Sử dụng Delta export kết hợp Feast `materialize_incremental` định kỳ qua Airflow asset events thay vì streaming feature ingestion trực tiếp vào Redis/DynamoDB.
- **Lợi ích:** Đảm bảo consistency giữa offline training data và online inference features (không bị training-serving skew). Hạ tầng triển khai gọn gàng, tái lập được.
- **Hạn chế:** Feature freshness có độ trễ phụ thuộc chu kỳ trigger của Airflow batch run.

### 1.4. Edge Gateway Policy (Envoy Token Bucket Rate Limiter)
- **Đánh đổi:** Chặn các burst request vượt ngưỡng (10 tokens, fill 10 tokens/s) ngay tại Envoy Gateway với mã `429 Too Many Requests` và header `x-lab28-rate-limited: true`.
- **Lợi ích:** Bảo vệ FastAPI service và các dependency phía sau (Qdrant, Feast, vLLM) khỏi tình trạng cạn kiệt tài nguyên (resource exhaustion / thread pool saturation).
- **Hạn chế:** Client cần có cơ chế exponential backoff và retry khi nhận mã 429.

### 1.5. Readiness Semantics (Degraded Mode vs Pod Eviction)
- **Đánh đổi:** Phân loại probe thành `mandatory` (Kafka, MLflow, Qdrant) và `optional/degradable` (Feast, vLLM khi chạy local).
- **Lợi ích:** Ngăn chặn hiện tượng cascading failures. Khi Feast cold hoặc vLLM bận, pod không bị hạ khỏi service rotation mà trả kết quả ở chế độ suy giảm (degraded mode) có chủ đích.

---

## 2. Production Gaps (Khoảng cách giữa Lab và Production)

1. **Storage Persistence & Object Store:**
   - *Hiện tại:* Delta Lake và model artifacts lưu trên Docker volume/local bind mount `/workspace/.lab28/delta`.
   - *Production:* Cần chuyển sang S3 / Google Cloud Storage / Azure ADLS Gen2 có lifecycle policy, server-side encryption (KMS) và cross-region replication.

2. **Broker Clustering & High Availability:**
   - *Hiện tại:* Kafka chạy 1 node đơn với replication factor = 1.
   - *Production:* Cần Kafka cluster tối thiểu 3 brokers phân bổ trên 3 Availability Zones (AZ), replication factor >= 3, `min.insync.replicas=2`.

3. **Secrets Management:**
   - *Hiện tại:* Các biến môi trường và cấu hình được nạp qua `compose.yaml` và `.env`.
   - *Production:* Cần tích hợp HashiCorp Vault, AWS Secrets Manager hoặc Kubernetes External Secrets Operator (ESO) với mTLS giữa các microservices.

4. **vLLM GPU Autoscaling & Serving:**
   - *Hiện tại:* Chạy local test với fallback giả lập/Kaggle T4 endpoint.
   - *Production:* Cần triển khai vLLM trên Kubernetes với KEDA GPU-metrics autoscaler, vLLM Ray cluster hoặc Triton Inference Server với dynamic batching và prefix caching.

5. **CI/CD & GitOps Delivery:**
   - *Hiện tại:* Sử dụng `docker compose` cục bộ và manifest mẫu trong `deploy/kubernetes`.
   - *Production:* Triển khai tự động bằng ArgoCD / FluxCD theo mô hình GitOps, có automated canary analysis (Argo Rollouts) kết hợp Prometheus golden signals.

---

## 3. Load Profile & Bottleneck Analysis

### 3.1. Kết quả Load Test (200 requests, 8 workers)
- **Tổng số requests:** 200
- **Số workers đồng thời:** 8
- **Kết quả HTTP status:**
  - `200 OK`: 28 requests
  - `429 Too Many Requests`: 172 requests (Envoy token bucket chặn thành công burst)
- **Độ trễ (Latency):**
  - **P50:** `5.18 ms`
  - **P95:** `564.70 ms`
  - **P99:** `629.17 ms`

### 3.2. Phân tích Bottleneck
- **Điểm nghẽn quan sát được:** Tốc độ phản hồi tại P50 cực kỳ nhanh (~5.18ms) nhờ Envoy từ chối cực nhanh các request vượt ngưỡng rate-limit mà không gọi tới backend API.
- **Độ trễ P95/P99:** Do cơ chế refill của token bucket (1 giây nạp 10 tokens), các worker phải xếp hàng chờ token mới được cấp, dẫn đến latency ở percentile cao tiệm cận 500-600ms trước khi được phục vụ hoặc từ chối.

---

## 4. Bảng phân công & Đóng góp thành viên (Team Contribution)

| Thành viên | Vai trò đảm nhiệm | Nội dung hoàn thành | Tỷ lệ đóng góp |
|---|---|---|:---:|
| **Nguyễn Hùng Mạnh** | Lead Engineer / All Roles | - **IP01/IP02 (Ingestion):** Đóng gói Kafka headers, W3C traceparent, xác thực Airflow DAG asset events.<br>- **IP03/IP04 (Data & ML):** Thuật toán `dedupe_latest` cho Delta MERGE, Feast online request formatting & materialization.<br>- **IP05/IP07 (Serving):** Vector store deterministic UUID indexing, MLflow champion release alias & vLLM probe.<br>- **IP08/IP09/IP10 (Platform):** Envoy edge rate limit verification, Prometheus golden signals scraping, OpenTelemetry distributed trace continuity.<br>- **Verification & Submission:** Sửa lỗi Windows UTF-8 encoding, chạy toàn bộ 83 unit tests, 4 starter tests, 56 integration tests, xuất trọn bộ evidence. | 100% |
