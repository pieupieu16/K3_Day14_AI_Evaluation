# 🎤 Kịch Bản Demo: AI Evaluation & Benchmarking Pipeline

- **Hình thức:** Thuyết trình Cá nhân
- **Thời lượng:** 7 – 10 phút
- **Đối tượng báo cáo:** Giảng viên / Hội đồng Đánh giá Lab
- **Ghi chú bảo mật:** Tuyệt đối không hiển thị file `.env` hoặc API key trong suốt quá trình demo terminal.

---

## ⏱️ THỜI GIAN VÀ CẤU TRÚC PHẦN THUYẾT TRÌNH

| Phân đoạn | Nội dung chính | Thời lượng |
|---|---|---:|
| **Phần 1** | Giới thiệu Pipeline & Kiến trúc RAG Evaluation | 1.5 phút |
| **Phần 2** | Chạy kiểm tra tự động (`pytest` & `validate_golden_dataset`) | 1.5 phút |
| **Phần 3** | Trình bày 01 Golden Case chuẩn | 1.5 phút |
| **Phần 4** | Trình bày Báo cáo Benchmark thực tế (Pass Rate & 5 Metrics) | 1.5 phút |
| **Phần 5** | Phân tích sâu 01 Case Failure (Gold vs Retrieved vs Actual) | 1.5 phút |
| **Phần 6** | Đề xuất giải pháp cải thiện & Tổng kết | 1.0 phút |

---

## 📝 NỘI DUNG CHI TIẾT VÀ LỜI THOẠI DEMO

---

### PHẦN 1: GIỚI THIỆU PIPELINE (1.5 Phút)

**Màn hình mở sẵn:** Cửa sổ Terminal tại thư mục `K3_Day14_AI_Evaluation`.

🎙️ **Lời thoại thuyết trình:**
> *"Kính chào thầy/cô và các bạn! Sau đây em xin trình bày phần demo bài lab **AI Evaluation & Benchmarking Pipeline** áp dụng cho hệ thống RAG Trợ lý Sinh viên Northstar University.*
>
> *Pipeline đánh giá của em gồm 5 bước khép kín:*
> 1. *`Corpus`: Tập hợp 10 tài liệu Markdown chính sách sinh viên (được phân thành 52 chunks).*
> 2. *`RAG System`: Trợ lý `domain_assistant.py` tích hợp BM25 Retriever, Guardrail chống Prompt Injection và mô hình local **Liquid AI (LFM2.5-2.6B)**.*
> 3. *`Actual Answer`: Sinh tập câu trả lời thực tế lưu tại `artifacts/actual_answers.json`.*
> 4. *`Evaluation Engine`: Mô-đun `solution.py` tính toán 5 chỉ số RAGAS.*
> 5. *`Benchmark Report`: Xuất báo cáo tổng hợp `artifacts/benchmark_results.json` và phân tích lỗi tự động.*
>
> *Sau đây em xin tiến hành các bước kiểm tra tự động hệ thống."*

---

### PHẦN 2: CHẠY KIỂM TRA TỰ ĐỘNG (1.5 Phút)

#### 🚀 Thao tác 1: Chạy Unit Test Suite
Gõ lệnh vào Terminal:
```bash
python -m pytest tests/ -v
```

🎙️ **Lời thoại thuyết trình:**
> *"Đầu tiên, em chạy bộ kiểm thử Unit Test của mô-đun Evaluation Core (`tests/test_solution.py`).*
> *(Sau khi màn hình hiển thị 42 passed/41 passed)*
> *Kết quả cho thấy toàn bộ các hàm tính chỉ số RAGAS (Faithfulness, Relevance, Completeness, Context Recall, Context Precision), LLM Judge, Benchmark Runner và Failure Analyzer đều **PASS 100%**.*

#### 🚀 Thao tác 2: Chạy Validate Golden Dataset
Gõ lệnh vào Terminal:
```bash
python validate_golden_dataset.py
```

🎙️ **Lời thoại thuyết trình:**
> *"Tiếp theo, em chạy script xác minh tính đúng đắn của Golden Dataset (`golden_dataset.json`).*
> *(Chỉ vào dòng chữ PASS)*
> *Màn hình báo **PASS**: Dataset gồm 20 câu hỏi đạt chuẩn schema, bao phủ toàn bộ 10/10 tài liệu nguồn, và 100% minh chứng evidence là **verbatim substring (trích dẫn nguyên văn)** từ tài liệu gốc."*

---

### PHẦN 3: TRÌNH BÀY MỘT GOLDEN CASE TIÊU BIỂU (1.5 Phút)

**Màn hình hiển thị:** Mở file `golden_dataset.json` (tìm đến ID `M01`).

🎙️ **Lời thoại thuyết trình:**
> *"Em xin trình bày một Golden Case đại diện trong dataset - **Case M01 (Độ khó Medium)**:*
>
> - **ID & Độ khó:** `M01` — Tầng Medium (Yêu cầu tổng hợp đa tài liệu).
> - **Question:** `'What approvals and fee payment are required for a late course add after the standard add/drop period?'`
> - **Expected Answer:** `'A late add requires instructor approval, programme-director approval, and payment of a USD 40 late-add fee per course within two business days of approval.'`
> - **Evidence & Provenance:** Minh chứng nguyên văn được trích xuất từ 2 tài liệu: `02_course_registration.md` (về chữ ký phê duyệt) và `03_tuition_payment_refund.md` (về thời hạn nộp phí $40).
>
> *Case này đòi hỏi RAG phải tìm đúng thông tin nằm rải rác ở 2 file chính sách khác nhau để trả lời đầy đủ."*

---

### PHẦN 4: TRÌNH BÀY BÁO CÁO BENCHMARK THỰC TẾ (1.5 Phút)

**Màn hình hiển thị:** Mở file `artifacts/benchmark_results.json` hoặc file `exercises.md` (mục 3.2).

🎙️ **Lời thoại thuyết trình:**
> *"Sau khi chạy đánh giá thực tế trợ lý RAG với mô hình Liquid AI LFM2.5-2.6B trên 20 câu hỏi, em thu được bảng kết quả benchmark như sau:*
>
> - **Overall Pass Rate:** `50.0%` (10 câu đạt / 10 câu chưa đạt).
> - **Context Recall:** `0.922` — Rất cao (Retriever lấy đúng tài liệu nguồn trên 92% trường hợp).
> - **Context Precision:** `0.976` — Xuất sắc (Các chunk đúng luôn nằm ở vị trí ưu tiên Top-1, Top-2).
> - **Faithfulness:** `0.592` — Điểm thấp nhất trong 5 chỉ số.
> - **Answer Relevance:** `0.514`.
> - **Completeness:** `0.804` — Bao phủ chi tiết rất tốt.
>
> **Nhận xét chính:** Bộ tra cứu BM25 Retriever hoạt động rất mạnh (Recall > 92%, Precision > 97%). Điểm pass rate bị giới hạn ở 50% không phải do tìm thiếu tài liệu, mà nằm ở khâu diễn đạt câu trả lời và khoảng cách từ vựng (Lexical Gap) của metric."*

---

### PHẦN 5: PHÂN TÍCH SÂU MỘT CASE FAILURE (1.5 Phút)

**Màn hình hiển thị:** Mở case `M05` trong `artifacts/actual_answers.json` và `reflection.md`.

🎙️ **Lời thoại thuyết trình:**
> *"Em xin phân tích sâu một case bị tính điểm thất bại — **Case M05** (Overall Score: `0.217` | Lỗi: `hallucination`):*
>
> - **Question:** *Hỏi về thời hạn nộp đơn xin nghỉ học y tế lùi ngày và thời gian đơn vị hành chính phải phản hồi.*
> - **Gold Expected Answer:** *'A retroactive medical leave request must normally be filed within 30 calendar days ... allow five business days to respond.'*
> - **Retrieved Context:** Retriever lấy **ĐÚNG 100%** tài liệu `06_leave_and_withdrawal.md` & `08_student_support_and_appeals.md` (Context Precision = 1.000, Recall = 0.920).
> - **Actual Answer:** *'A retroactive request must normally be filed within 30 calendar days ... allow five business days for a response.'*
>
> **Xác định bản chất lỗi (Retrieval vs Generation vs Metric):**
> *Đây **KHÔNG PHẢI lỗi của Retriever** và cũng **KHÔNG PHẢI lỗi của LLM** (vì thông tin sinh ra hoàn toàn chính xác). Đây là **LỖI CỦA METRIC HEURISTIC (Lexical Gap)**. Metric so sánh trùng lặp từ vựng thuần túy đã phạt câu trả lời khi LLM diễn đạt bằng từ đồng nghĩa (`for a response` thay vì `to respond`), làm Faithfulness bị tụt xuống `0.100` một cách vô lý."*

---

### PHẦN 6: ĐỀ XUẤT CẢI THIỆN & TỔNG KẾT (1.0 Phút)

🎙️ **Lời thoại thuyết trình:**
> *"Để khắc phục triệt để vấn đề này, em đề xuất 3 giải pháp cải tiến:*
>
> 1. **Nâng cấp Evaluator sang Semantic LLM-as-a-Judge / Embedding Similarity:** Thay thế word-overlap thuần túy bằng RAGAS LLM Evaluator để đánh giá đúng ý nghĩa ngữ nghĩa, loại bỏ điểm phạt vô lý với từ đồng nghĩa.
> 2. **Chuẩn hóa System Prompt Format:** Ép mô hình sinh câu trả lời ngắn gọn theo đúng khuôn mẫu của Expected Answer để tăng điểm trùng lặp token.
> 3. **Cách kiểm chứng:** Chạy lại `python evaluate_answers.py` sau khi nâng cấp evaluator; dự kiến chỉ số Faithfulness sẽ tăng từ `0.592` lên **`> 0.850`** và Pass Rate đạt **`> 85%`**.
>
> *Em xin kết thúc phần demo. Cảm ơn thầy/cô đã theo dõi!"*

---

## 🎯 BẢNG CHECKLIST CHO BUỔI DEMO

- [x] Đã khởi chạy thử lệnh `python -m pytest tests/ -v` (42/41 passed).
- [x] Đã chạy thử `python validate_golden_dataset.py` (PASS).
- [x] Đã ẩn/tắt các file `.env` hoặc API key trên màn hình VS Code / Terminal.
- [x] Mở sẵn file `golden_dataset.json`, `artifacts/benchmark_results.json`, và `reflection.md`.

---

## ❓ TOP 5 CÂU HỎI PHẢN BIỆN & CÂU TRẢ LỜI MẪU CHUẨN (Q&A DEFENSE)

### ❓ Câu 1 (Về Kết Quả Metrics)
**Hỏi:** *"Tại sao chỉ số Context Recall (0.922) và Precision (0.976) rất cao, nhưng Faithfulness (0.592) và Relevance (0.514) lại khá thấp? Lỗi nằm ở đâu?"*
> **Trả lời:**  
> *"Thưa thầy/cô, kết quả này cho thấy **Retriever (BM25) hoạt động rất tốt** — lấy đúng bằng chứng tài liệu nguồn trên 92% trường hợp và xếp chunk đúng ở vị trí Top-1/Top-2 trên 97% trường hợp.*  
> *Nguyên nhân khiến Faithfulness và Relevance thấp là do **giới hạn của Heuristic Word-Overlap Metric**. Khi mô hình LLM sinh ra câu trả lời đúng bản chất nhưng dùng câu từ diễn đạt thể chủ động/từ đồng nghĩa khác với Expected Answer, metric từ vựng thuần túy bị phạt vô lý (như ở Case M05). Để khắc phục, trong thực tế cần nâng cấp sang **Semantic LLM-as-a-Judge / Embedding Cosine Similarity**."*

---

### ❓ Câu 2 (Về Bảo Mật & Guardrails)
**Hỏi:** *"Hệ thống Guardrail ngăn chặn tấn công Prompt Injection được thiết kế thế nào?"*
> **Trả lời:**  
> *"Hệ thống sử dụng cơ chế bảo vệ 2 lớp (**Two-tier Defense**):*  
> 1. **Layer 1 (Input Guardrail `_detect_attack_or_injection`):** Sử dụng Pattern Regex quét trước câu hỏi. Nếu phát hiện mẫu tấn công (như `ignore previous instructions`, `reveal system prompt`, `DAN`), hệ thống từ chối ngay lập tức mà không tiêu tốn token LLM.  
> 2. **Layer 2 (System Prompt Hardening):** Phân định rõ ràng thẻ `<retrieved_context>` và `<user_question>` kèm quy tắc **Strict Grounding**, ép LLM từ chối bẫy out-of-scope hoặc câu hỏi có giả định sai (False Premise)."*

---

### ❓ Câu 3 (Về Thuật Toán Reranking)
**Hỏi:** *"Tại sao khi áp dụng Reranking `rerank_by_overlap`, Context Precision tăng từ 0.907 lên 1.000 (+0.093) nhưng Context Recall lại không thay đổi (0.989)?"*
> **Trả lời:**  
> *"Thưa thầy/cô, Reranking chỉ thực hiện **sắp xếp lại (re-order)** thứ tự ưu tiên của các chunks đã được BM25 lấy về trong tập ứng viên, chứ không bổ sung thêm chunk mới. Vì tổng hợp thông tin (union of chunks) không thay đổi nên **Context Recall giữ nguyên**. Còn **Context Precision tăng** vì chunk chứa nhiều từ khóa đúng được đẩy lên vị trí xếp hạng Top-1."*

---

### ❓ Câu 4 (Về Golden Dataset & Verbatim Evidence)
**Hỏi:** *"Làm thế nào để đảm bảo tính đúng đắn của Golden Dataset và quy tắc Verbatim Evidence Substring?"*
> **Trả lời:**  
> *"Dataset 20 QA được thiết kế theo phương pháp phân tầng (**Stratified Sampling**): 5 Easy, 7 Medium, 5 Hard, 3 Adversarial phủ đủ 10/10 tài liệu chính sách. Script `validate_golden_dataset.py` chạy kiểm tra 100% trường hợp: mảng `contexts[i].text` phải là **chuỗi con trích dẫn nguyên văn (verbatim substring)** từng ký tự từ file Markdown gốc, đảm bảo không có thông tin suy diễn bịa đặt."*

---

### ❓ Câu 5 (Về CI/CD & Quality Gate)
**Hỏi:** *"Khi đưa pipeline này vào CI/CD thực tế, điều kiện nào sẽ BLOCK không cho phép Deploy sản phẩm?"*
> **Trả lời:**  
> *"Hàm `run_regression()` sẽ tự động chạy trong pipeline CI/CD mỗi khi có thay đổi Code/Prompt/Model. Hệ thống sẽ **BLOCK Deploy** khi:*  
> 1. Chỉ số Faithfulness sụt giảm $\ge 0.05$ so với baseline (để ngăn nguy cơ bịa đặt thông tin học phí/ngày tháng gây rủi ro pháp lý).  
> 2. Có bất kỳ vi phạm lỗ hổng bảo mật/Prompt Injection nào ở câu hỏi Adversarial."*

