# Trợ lý Toán lớp 5

Giải và giải thích từng bước các dạng toán lớp 5. Có 3 cách dùng: trang web (nhập giọng nói, đọc đáp án), dòng lệnh và thư viện Python.

## Cấu trúc
```
tro_ly_toan_lop5/
├── app.py              # máy chủ Flask (trang web + API)
├── cli.py              # chạy trên dòng lệnh
├── mathbot/
│   ├── __init__.py
│   └── solver.py       # bộ giải toán (chỉ dùng thư viện chuẩn)
├── static/img/         # hình nhân vật trợ lý (chao, nghi, vui, giang, avatar)
├── static/index.html   # giao diện chat: gõ/nói câu hỏi, nghe đáp án
├── static/de-thi.html  # trang riêng về đề thi (ngân hàng 111 câu, có đáp án + cách giải)
├── de_bank.py          # nội dung tuyển chọn cho trang đề thi (đã đối chiếu đáp số)
├── de-thi.template.html# khuôn mẫu của trang đề thi
├── build_de.py         # dựng static/de-thi.html từ de_bank.py (chỉ ghi khi đáp số khớp)
├── kiem_thu_de.py      # kiểm tra trang đề thi (đủ câu, đủ đáp án, cú pháp JS)
├── nganhang_de/        # script + file nguồn .docx để kiểm tra lại đáp án (check_de.py)
├── tests/test_solver.py
├── requirements.txt    # Flask, Gunicorn, giọng nói
├── run.sh / run.bat    # chạy nhanh (tự tạo môi trường ảo)
└── README.md
```

## Chạy nhanh
- Linux/macOS: `./run.sh`
- Windows: bấm đúp `run.bat`

Rồi mở http://127.0.0.1:5000

## Đưa website lên Internet bằng GitHub Pages và Render

Ứng dụng có hai phần khi chạy công khai: GitHub Pages cung cấp giao diện tĩnh và OCR; Render chạy API Flask, chat, danh sách giọng và tổng hợp giọng nói. Chạy local vẫn dùng một máy chủ Flask như trước.

1. Trên Render, bấm **Deploy to Render** bên dưới, đăng nhập, chọn kho `NhocSa/tro-ly-toan-lop-5` và áp dụng Blueprint từ `render.yaml`.
2. Nếu URL Render không phải `https://tro-ly-toan-lop-5.onrender.com`, thêm repository variable `RENDER_API_URL` trong **GitHub → Settings → Secrets and variables → Actions → Variables** với URL gốc được Render cấp.
3. Trong **GitHub → Settings → Pages**, đặt **Build and deployment → Source** thành **GitHub Actions**. Sau đó workflow **Deploy GitHub Pages** sẽ tự dựng giao diện và cấp URL tại `https://nhocsa.github.io/tro-ly-toan-lop-5/`.
4. Nếu đổi URL Render, cập nhật `CORS_ALLOWED_ORIGINS` trong dịch vụ Render thành `https://nhocsa.github.io` (và lưu để triển khai lại), sau đó chạy lại workflow **Deploy GitHub Pages**.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/NhocSa/tro-ly-toan-lop-5)

Render miễn phí có thể tạm dừng dịch vụ khi ít người dùng, nên API có thể chậm ở lần truy cập đầu sau thời gian nghỉ. Chat trên Render dùng Gemini; `render.yaml` đặt `CHAT_PROVIDER=gemini`. Micro yêu cầu HTTPS và quyền truy cập micro của trình duyệt. Khi Web Speech Recognition báo lỗi mạng, trang sẽ chuyển sang ghi âm và gửi âm thanh tới Gemini để chép thành chữ.

### Cấu hình Gemini cho chat trên Render

Trong Render → dịch vụ → **Environment**, giữ biến `API_Gemmini` hiện có hoặc dùng tên chuẩn `GEMINI_API_KEY`; ứng dụng hỗ trợ cả hai tên và `render.yaml` khai báo tên chuẩn là bí mật không đồng bộ qua Git. Khi có Gemini key, Gemini luôn được ưu tiên kể cả khi `CHAT_PROVIDER` cũ đang đặt `ollama`; nếu không có key, local mặc định dùng Ollama. Tạo API key tại [Google AI Studio](https://aistudio.google.com/app/apikey), dán trực tiếp vào giá trị biến bí mật trên Render rồi lưu/redeploy. Không gửi key trong chat, commit hoặc thêm vào GitHub. Tên model mặc định là `gemini-2.5-flash`, có thể đổi bằng `GEMINI_MODEL`. Tương tự, giọng FPT chấp nhận cả `FPT_API_KEY` và tên biến Render đang dùng `FPT_AI_API`.

Ollama vẫn là mặc định khi chạy local. Muốn dùng làm máy dự phòng cho Gemini trên Render, hãy chạy Ollama trên một máy chủ có thể truy cập từ Render và đặt `OLLAMA_URL` (ví dụ `https://ollama.example.com`) trong Environment; nếu không cấu hình biến này, ứng dụng không gọi Ollama khi Gemini lỗi. Không dùng `127.0.0.1` trên Render trừ khi Ollama thật sự chạy trong cùng container. Ollama có thể chạy trên gói Render trả phí đủ RAM và dung lượng, nhưng không thực tế trên Render Free vì hạn chế bộ nhớ, ổ đĩa và tốc độ suy luận.

### Giữ khóa API riêng tư

Không commit `fpt_key.txt` hoặc dán khóa vào mã nguồn/GitHub. Trên Render, mở dịch vụ → **Environment**, thêm `FPT_API_KEY` và dán khóa mới trực tiếp vào ô giá trị bí mật rồi lưu để triển khai lại. `render.yaml` khai báo biến này là bí mật không đồng bộ qua Git. Khi chạy local, dùng biến môi trường `FPT_API_KEY` hoặc `fpt_key.txt` (tệp đã được `.gitignore` loại trừ). Nếu khóa từng được commit lên repository công khai, hãy thu hồi khóa cũ tại FPT.AI rồi mới nhập khóa mới vào Render.

## Trò chuyện Ollama khi chạy local

Ứng dụng có thể dùng Ollama để trả lời câu hỏi mở và nhớ ngữ cảnh trong vài lượt gần nhất. Nội dung trò chuyện được gửi tới Ollama đang chạy trên chính máy, không cần khóa API. Cài Ollama cho Windows từ [trang chính thức](https://ollama.com/download/windows), rồi chạy `setup_chat.bat` một lần để tải mô hình `qwen3.5:2b` (khoảng 2,7–3,1 GB). Sau đó mở Ollama và chạy `run.bat` như thường lệ.

Để thử Gemini local thay vì Ollama, đặt khóa trong biến môi trường (không dán vào mã nguồn hoặc JavaScript). Trong PowerShell:
```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
$env:CHAT_PROVIDER = "gemini"
python app.py
```
Sau đó mở `http://127.0.0.1:5000`. Có thể đặt `GEMINI_MODEL` để chọn model; mặc định là `gemini-2.5-flash`, và nếu model tùy chỉnh không tồn tại, ứng dụng sẽ thử lại model mặc định.

Nếu đã cài Ollama, có thể tự tải mô hình bằng lệnh `ollama pull qwen3.5:2b`. Ứng dụng dùng mô hình này mặc định; có thể đổi bằng biến môi trường `OLLAMA_MODEL`. Nếu Ollama chưa chạy hoặc chưa có mô hình, phần giải toán theo mẫu vẫn hoạt động và khung chat sẽ báo cách khắc phục.

Chạy thủ công:
```bash
pip install -r requirements.txt
python app.py        # web
python cli.py        # dòng lệnh
```
Cho máy khác trong mạng LAN truy cập: `HOST=0.0.0.0 python app.py` (đổi cổng bằng `PORT=8080`).

## Dùng như thư viện
```python
from mathbot import giai
print(giai("Tính diện tích hình tròn bán kính 5 cm"))
```

## API
- `POST /api/giai` với JSON `{"cau_hoi": "20% của 150"}` trả về `{"dap_an": "..."}`
- `POST /api/chat` với mảng tin nhắn `messages` để trò chuyện qua Gemini trên Render hoặc Ollama cục bộ
- `POST /api/transcribe` để chép âm thanh thành chữ bằng Gemini khi trình duyệt không nhận giọng nói trực tiếp được
- `GET /api/voices` danh sách giọng offline và giọng FPT đã cấu hình
- `POST /api/tts` với JSON `{"noi_dung": "...", "giong": "piper_vi"}` trả về WAV offline; các giọng trực tuyến trả MP3
- `GET /healthz` kiểm tra server

## Các dạng bài hỗ trợ
Biểu thức, tìm x, phân số (rút gọn, quy đồng, so sánh), ƯCLN và BCNN, phần trăm, hình học (chữ nhật, vuông, tam giác, thang, bình hành, thoi, tròn, hộp chữ nhật, lập phương), chuyển động đều, đổi đơn vị độ dài và khối lượng, trung bình cộng.

Gõ số thập phân bằng dấu phẩy (`3,5`). Khi liệt kê nhiều số, ngăn cách bằng chữ "và" hoặc dấu cách.

## Giọng nói
- **Giọng online tự nhiên:** chọn **Cô Hoài My** trong phần giọng đọc. Giọng nữ tiếng Việt được tạo liền mạch cho cả câu trả lời, phù hợp nghe cô hướng dẫn; cần Internet. Khi có mạng, đây là giọng mặc định (trừ khi đã cấu hình khóa FPT).
- **Giọng tiếng Việt offline:** chọn **Cô · giọng nữ Việt offline (Piper)**. Dùng mô hình `vi_VN-vais1000-medium` trong thư mục `models/`; không cần gửi nội dung ra dịch vụ giọng nói. Nếu giọng online bị lỗi và Piper đã cài, ứng dụng tự chuyển sang Piper.
- Lần chạy đầu, `run.bat` cài runtime Piper và ONNX Runtime từ PyPI nên cần Internet để cài thư viện. Mô hình giọng đã có sẵn trong gói; sau bước cài, phần đọc hoạt động offline và không cần cài giọng tiếng Việt trong Windows. Nếu cập nhật gói, giải nén rồi chạy lại `run.bat`.
- Mô hình giọng dựa trên bộ VAIS-1000; thẻ mô hình và giấy phép được ghi tại `models/MODEL_CARD.txt`. Giấy phép dữ liệu: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). Nguồn mô hình: [Piper Vietnamese VAIS-1000](https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/vi/vi_VN/vais1000/medium).
- **FPT.AI** (Lan Nhi, Linh San nữ miền Nam; Ban Mai, Thu Minh nữ miền Bắc; Mỹ An nữ miền Trung) là lựa chọn thêm khi có khóa tại https://console.fpt.ai. Đặt khóa trong `fpt_key.txt` cạnh `app.py` hoặc biến môi trường `FPT_API_KEY`. Khi FPT lỗi/hết hạn mức, ứng dụng chuyển sang Piper offline.
- **Google TTS** cũng có trong danh sách khi cài đủ thư viện; cần Internet để tạo âm thanh.
- Nhập giọng nói dùng Web Speech API trên Chrome/Edge và cần cho phép micro. Mục **Windows · giọng offline có sẵn** chỉ dùng các giọng đã cài sẵn trên thiết bị.
- Khi nói, hỗ trợ "cộng, trừ, nhân, chia, bằng, phẩy, phần trăm" và số bằng chữ như "mười hai", "hai mươi lăm".

## Kiểm thử
```bash
python -m unittest discover -s tests -v
```

## Hạn chế
Khi chưa cài Ollama và tải mô hình, trợ lý chỉ trả lời các câu trò chuyện mẫu; phần giải toán chạy tại chỗ cũng chỉ hỗ trợ các dạng đã liệt kê. Khi có Ollama, câu hỏi mở được gửi kèm vài lượt hội thoại gần nhất tới mô hình cục bộ.

## Chủ đề, toán có lời văn và Chương trình GDPT 2018

- **Hàng chọn chủ đề** phía trên: Tất cả, Phân số, Số thập phân, Phần trăm, Hình học, Đo lường, Toán có lời văn. Chọn chủ đề thì các gợi ý bên dưới đổi theo.
- **Nút 📘 Chương trình**: đối chiếu theo 3 mạch kiến thức của chương trình GDPT 2018 lớp 5 (Số và phép tính; Hình học và đo lường; Thống kê và xác suất), có nút "Hỏi thử" cho từng nội dung đã hỗ trợ và ghi rõ nội dung chưa có. Đối chiếu theo mạch, chưa theo từng bài của từng bộ sách.
- **Toán có lời văn** (gõ cả đề bài), trình bày từng bước và có "Đáp số":
  - tổng – hiệu, tổng – tỉ số, hiệu – tỉ số của hai số;
  - tỉ lệ thuận và tỉ lệ nghịch (rút về đơn vị);
  - phần trăm: tìm phần trăm của một số, số còn lại, giảm giá, tăng giá, tìm số ban đầu, tỉ số phần trăm;
  - chuyển động ngược chiều (gặp nhau) và cùng chiều (đuổi kịp);
  - hình chữ nhật: biết chu vi hoặc diện tích và một cạnh, tìm cạnh còn lại;
  - trung bình cộng, trung bình mỗi ...; khả năng xảy ra (tỉ số) khi lấy bi ngẫu nhiên;
  - làm tròn số thập phân (đến số nguyên, phần mười, phần trăm, phần nghìn).
- Chưa hỗ trợ: đổi đơn vị diện tích và thể tích, cộng trừ số đo thời gian, đọc biểu đồ.
- Phần giải này chạy trong trình duyệt (`static/index.html`). Bộ giải Python trong `mathbot/` (dùng cho API/dòng lệnh) chưa có các phần mới này.

## Trang riêng về đề thi (ngân hàng câu hỏi)

- Nút **📝 Đề thi** trên trang chat (hoặc vào địa chỉ `http://127.0.0.1:5000/de-thi`) mở trang **Đề thi Toán lớp 5**.
- **111 câu** tuyển chọn từ ngân hàng đề cuối kì các năm 2017–2020 (Số học, Hình học, Đại lượng — mỗi mạch có mức 1 đến 4) và hai chuyên đề bồi dưỡng: *chuyển động trên dòng nước*, *vật chuyển động có chiều dài đáng kể*.
- **20 câu trắc nghiệm** có thể chọn đáp án A/B/C/D và chấm ngay trên trang; câu trả lời đúng được đánh dấu, còn câu tự luận vẫn có đáp án và lời giải riêng.
- Lọc theo **chủ đề / mức độ / dạng bài**, tìm kiếm theo nội dung, ** xem đáp án và cách giải từng bước, **🎲 Đề ngẫu nhiên** (10 câu, mix các mức) và **🖨 In / lưu PDF** để làm phiếu học tập.
- Nút **💬 Trợ lý giải** gửi đúng câu đó sang trang chat để nghe giảng từng bước.
- Một số câu có ghi chú ⚠️: đáp án trong tài liệu gốc chưa đúng, trang đã tính lại và ghi rõ chỗ sửa.
- Muốn bổ sung câu hỏi: sửa danh sách `TUYEN_CHON` trong `de_bank.py` rồi chạy `python build_de.py`. Trình dựng trang **chỉ ghi file khi toàn bộ đáp số đối chiếu khớp** (`python check_de.py` để xem báo cáo).

## Giao diện toàn màn hình và nhận diện ảnh

- **Toàn màn hình:** giao diện tự giãn theo cỡ màn hình (chữ và khung chat lớn hơn trên màn hình lớn). Nút **⛶ Toàn màn hình** ở đầu trang (hoặc phím F11) mở toàn màn hình; trên iPhone, Safari không cho phép chế độ này.
- **Cô trợ lý ở góc:** nhân vật nằm nhỏ ở góc trên bên phải khung chat. Bấm vào để thu thành ảnh tròn hoặc mở lại; lựa chọn được nhớ. Trên màn hình nhỏ, mặc định là ảnh tròn. Nút 🎙 (điện thoại) mở phần chọn giọng đọc.
- **Nhận diện đề bài từ ảnh:** bấm **📷** để chụp (trên điện thoại) hoặc chọn ảnh, hoặc dán ảnh (Ctrl+V), hoặc kéo thả ảnh vào trang. Cô đọc chữ trong ảnh, đưa vào ô nhập để em kiểm tra, rồi bấm "Đúng rồi, giải bài này".
  - Dùng Tesseract.js, chạy ngay trên máy: ảnh không gửi đi đâu và dùng được khi không có Internet (thư viện và dữ liệu tiếng Việt nằm trong `static/ocr/`, khoảng 8 MB).
  - Chữ in rõ, đủ sáng, thẳng thì đọc tốt. Chữ viết tay, ảnh mờ hoặc nghiêng thì dễ sai, nên luôn có bước em kiểm tra và sửa lại.
  - Lần đọc đầu tiên mất thêm vài giây để nạp bộ đọc chữ.
#
