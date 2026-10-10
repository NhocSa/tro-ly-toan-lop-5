#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Máy chủ web Flask cho Trợ lý Toán lớp 5.

    python app.py            # mở http://127.0.0.1:5000
Biến môi trường tùy chọn: HOST (mặc định 127.0.0.1), PORT (mặc định 5000).
"""
import asyncio
import base64
import io
import json
import os
import threading
import time
import urllib.error
import urllib.request
import wave

from flask import Flask, Response, jsonify, request, send_from_directory

try:
    import edge_tts
except ImportError:  # Vẫn cho phép chạy phần giải toán khi chưa cài đủ phụ thuộc.
    edge_tts = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from piper import PiperVoice
except ImportError:  # Cho phép mở phần toán nếu máy chưa cài bộ đọc local.
    PiperVoice = None

from mathbot import giai

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.json.ensure_ascii = False  # trả tiếng Việt có dấu trực tiếp trong JSON
_CORS_ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "https://nhocsa.github.io").split(",")
    if origin.strip()
}
TTS_VOICE = "vi-VN-HoaiMyNeural"  # giọng nữ tiếng Việt rõ ràng (mặc định)
GIONG_DU_PHONG = "hoaimy"  # luôn dùng được, là nơi lùi về khi giọng khác lỗi
PIPER_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "models", "vi_VN-vais1000-medium.onnx")
_PIPER_VOICE = None
_PIPER_LOCK = threading.Lock()


def _piper_san_sang():
    return PiperVoice is not None and os.path.isfile(PIPER_MODEL)


def _doc_khoa_fpt():
    """Khóa FPT lấy từ biến môi trường FPT_API_KEY hoặc file fpt_key.txt cạnh app.py (không ghi vào code)."""
    khoa = (
        os.environ.get("FPT_API_KEY", "").strip()
        or os.environ.get("FPT_AI_API", "").strip()
    )
    if not khoa:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fpt_key.txt"),
                      encoding="utf-8") as f:
                khoa = f.read().strip()
        except OSError:
            khoa = ""
    return khoa


# Existing Render dashboards may use FPT_AI_API; keep the canonical name too.
FPT_API_KEY = _doc_khoa_fpt()  # tùy chọn: lấy tại console.fpt.ai
FPT_SPEED = os.environ.get("FPT_SPEED", "-1").strip() or "-1"  # -3 chậm nhất ... +3 nhanh nhất

# Ollama remains the local default; an available Gemini key selects Gemini on hosted deployments.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_FALLBACK_CONFIGURED = bool(os.environ.get("OLLAMA_URL", "").strip())
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:2b").strip() or "qwen3.5:2b"
def _doc_khoa_gemini():
    """Đọc khóa Gemini từ biến môi trường chuẩn hoặc alias đã dùng trên Render."""
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("API_Gemmini", "").strip()
    )


GEMINI_API_KEY = _doc_khoa_gemini()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def _chon_chat_provider():
    provider = os.environ.get("CHAT_PROVIDER", "").strip().lower()
    return provider or ("gemini" if GEMINI_API_KEY else "ollama")


CHAT_PROVIDER = _chon_chat_provider()
CHAT_SYSTEM_PROMPT = """Bạn là cô trợ lý học tập trong ứng dụng Toán lớp 5 của học sinh Việt Nam.
Luôn xưng là cô và gọi người dùng là em; nói như giáo viên đang hướng dẫn học sinh, rõ ràng, ngắn gọn và phù hợp với học sinh tiểu học. Không dùng từ "dạ".
Bạn có thể trò chuyện tự nhiên, ghi nhớ các tin nhắn trước trong cuộc trò chuyện hiện tại, và giúp giải thích Toán lớp 5 từng bước.
Nếu không biết câu trả lời, hãy nói thật. Không tự nhận là người thật, không yêu cầu thông tin cá nhân, mật khẩu hay địa chỉ.
Với câu hỏi ngoài khả năng, hãy nói rõ giới hạn và gợi ý em hỏi người lớn đáng tin cậy khi cần."""


class ChatProviderError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def _gemini_generate(payload):
    if not GEMINI_API_KEY:
        raise ChatProviderError(
            "Dịch vụ trò chuyện AI chưa được cấu hình khóa Gemini. Em thử lại sau nhé.",
            503,
        )
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        if status in (400, 401, 403):
            raise ChatProviderError(
                "Khóa Gemini chưa hợp lệ hoặc chưa được cấp quyền. Chủ dịch vụ cần kiểm tra API key.",
                503,
            ) from exc
        if status == 429:
            raise ChatProviderError(
                "Gemini đang quá tải hoặc đã hết hạn mức. Em thử lại sau nhé.",
                503,
            ) from exc
        raise ChatProviderError("Gemini đang gặp sự cố. Em thử lại sau nhé.", 502) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ChatProviderError(
            "Chưa kết nối được dịch vụ Gemini. Em thử lại sau nhé.",
            503,
        ) from exc
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        raise ChatProviderError(
            "Gemini trả về dữ liệu chưa đúng định dạng. Em thử lại nhé.",
            502,
        ) from exc
    if not isinstance(result, dict) or result.get("error"):
        raise ChatProviderError(
            "Gemini trả về dữ liệu chưa đúng định dạng. Em thử lại nhé.",
            502,
        )
    return result


def _gemini_text(result, fallback):
    candidates = result.get("candidates")
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise ChatProviderError(fallback, 502)
    content = candidates[0].get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    answer = "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    ).strip() if isinstance(parts, list) else ""
    if not answer:
        raise ChatProviderError(fallback, 502)
    return answer


def _tao_tra_loi_gemini(messages):
    """Gửi lịch sử chat tới Gemini; khóa API không được ghi vào log."""
    contents = [
        {
            "role": "model" if item["role"] == "assistant" else "user",
            "parts": [{"text": item["content"]}],
        }
        for item in messages
        if item["role"] in ("user", "assistant")
    ]
    result = _gemini_generate({
        "systemInstruction": {"parts": [{"text": CHAT_SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.6},
    })
    return _gemini_text(result, "Gemini chưa tạo được câu trả lời. Em thử hỏi lại nhé.")


def _tao_tra_loi_ollama(messages):
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.6},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        answer = str(result.get("message", {}).get("content", "")).strip()
        if not answer:
            raise ChatProviderError(
                "Mô hình Ollama chưa tạo được câu trả lời. Em thử hỏi lại nhé.",
                502,
            )
        return answer
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        if status == 404:
            raise ChatProviderError(
                f"Chưa tải mô hình {OLLAMA_MODEL}. Hãy chạy: ollama pull {OLLAMA_MODEL}",
                503,
            ) from exc
        raise ChatProviderError("Mô hình Ollama đang bận. Em thử lại sau nhé.", 502) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ChatProviderError(
            "Không kết nối được máy chủ Ollama dự phòng.",
            503,
        ) from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise ChatProviderError(
            "Ollama trả về dữ liệu chưa đúng định dạng. Em thử lại nhé.",
            502,
        ) from exc


def giong_mac_dinh():
    """Ưu tiên giọng nữ tự nhiên khi có mạng; giữ Piper làm lựa chọn offline."""
    if FPT_API_KEY:
        return "fpt_linhsan"
    if edge_tts is not None:
        return "hoaimy"
    if _piper_san_sang():
        return "piper_vi"
    return GIONG_DU_PHONG

# Piper đọc tiếng Việt hoàn toàn offline; giọng Microsoft cần Internet.
GIONG = {
    "piper_vi":    {"nhan": "Cô · giọng nữ Việt offline (Piper)",         "engine": "piper"},
    "hoaimy":      {"nhan": "Cô Hoài My · giọng nữ tự nhiên (cần mạng)",  "engine": "edge", "rate": "-8%"},
    "hoaimy_cham": {"nhan": "Hoài My · đọc chậm cho bé nghe rõ",         "engine": "edge", "rate": "-22%"},
    "hoaimy_cao":  {"nhan": "Hoài My · giọng tươi, cao hơn",             "engine": "edge", "rate": "-5%", "pitch": "+8Hz"},
    "gtts":        {"nhan": "Google · giọng nữ tiếng Việt",              "engine": "gtts"},
    "fpt_lannhi":  {"nhan": "FPT · Lan Nhi (nữ miền Nam)",               "engine": "fpt", "voice": "lannhi"},
    "fpt_linhsan": {"nhan": "FPT · Linh San (nữ miền Nam)",              "engine": "fpt", "voice": "linhsan"},
    "fpt_banmai":  {"nhan": "FPT · Ban Mai (nữ miền Bắc)",               "engine": "fpt", "voice": "banmai"},
    "fpt_thuminh": {"nhan": "FPT · Thu Minh (nữ miền Bắc)",              "engine": "fpt", "voice": "thuminh"},
    "fpt_myan":    {"nhan": "FPT · Mỹ An (nữ miền Trung)",               "engine": "fpt", "voice": "myan"},
}


def _giong_dung_duoc(cfg):
    if cfg["engine"] == "piper":
        return _piper_san_sang()
    if cfg["engine"] == "edge":
        return edge_tts is not None
    if cfg["engine"] == "gtts":
        return gTTS is not None
    return bool(FPT_API_KEY)


async def _tao_am_thanh(noi_dung, cfg):
    """Tạo MP3 trong bộ nhớ bằng edge-tts, không lưu câu hỏi của học sinh xuống đĩa."""
    du_lieu = bytearray()
    tts = edge_tts.Communicate(noi_dung, TTS_VOICE, rate=cfg.get("rate", "-8%"),
                               pitch=cfg.get("pitch", "+0Hz"))
    async for goi in tts.stream():
        if goi["type"] == "audio":
            du_lieu.extend(goi["data"])
    return bytes(du_lieu)


def _tao_gtts(noi_dung):
    bo_dem = io.BytesIO()
    gTTS(noi_dung, lang="vi").write_to_fp(bo_dem)
    return bo_dem.getvalue()


def _tao_piper(noi_dung):
    """Tổng hợp WAV bằng mô hình tiếng Việt đi kèm ứng dụng, không gọi mạng."""
    global _PIPER_VOICE
    if not _piper_san_sang():
        raise RuntimeError("Chưa cài Piper hoặc thiếu mô hình tiếng Việt offline")
    with _PIPER_LOCK:
        if _PIPER_VOICE is None:
            _PIPER_VOICE = PiperVoice.load(PIPER_MODEL)
        bo_dem = io.BytesIO()
        with wave.open(bo_dem, "wb") as tep_wav:
            _PIPER_VOICE.synthesize_wav(noi_dung, tep_wav)
        return bo_dem.getvalue()


def _tao_fpt(noi_dung, voice):
    """FPT.AI TTS v5: nhận liên kết MP3 bất đồng bộ rồi đợi âm thanh sẵn sàng."""
    req = urllib.request.Request(
        "https://api.fpt.ai/hmi/tts/v5", data=noi_dung.encode("utf-8"), method="POST",
        headers={"api_key": FPT_API_KEY, "voice": voice, "speed": FPT_SPEED})
    with urllib.request.urlopen(req, timeout=15) as r:
        ket_qua = json.loads(r.read().decode("utf-8"))
    if ket_qua.get("error", 0) not in (0, "0", None) or str(ket_qua.get("success", "true")).lower() == "false":
        raise RuntimeError("FPT từ chối yêu cầu TTS: " + str(ket_qua.get("message", "lỗi không xác định")))
    url = ket_qua.get("async")
    if not url:
        raise RuntimeError("FPT không trả về liên kết âm thanh")
    cho = 0.5
    for _ in range(120):  # FPT có thể cần tới khoảng 2 phút để dựng âm thanh dài
        time.sleep(cho)
        cho = 1.0
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                du_lieu = r.read()
            if du_lieu:
                return du_lieu
        except Exception:
            continue
    raise RuntimeError("FPT chưa tạo xong âm thanh")


def _tao_bang_giong(noi_dung, ma):
    cfg = GIONG[ma]
    if cfg["engine"] == "piper":
        return _tao_piper(noi_dung)
    if cfg["engine"] == "gtts":
        return _tao_gtts(noi_dung)
    if cfg["engine"] == "fpt":
        return _tao_fpt(noi_dung, cfg["voice"])
    return asyncio.run(_tao_am_thanh(noi_dung, cfg))


@app.get("/")
def index():
    # Trang chat có nhập giọng nói + đọc đáp án (giải toán chạy ngay trên trình duyệt)
    return send_from_directory(app.static_folder, "index.html")


@app.get("/config.js")
def frontend_config():
    return send_from_directory(app.static_folder, "config.js")


@app.get("/de-thi")
def de_thi():
    """Trang ngân hàng đề thi Toán lớp 5 (lọc theo chủ đề, mức độ; có đáp án và cách giải)."""
    return send_from_directory(app.static_folder, "de-thi.html")


@app.post("/api/giai")
def api_giai():
    data = request.get_json(silent=True) or {}
    cau_hoi = str(data.get("cau_hoi", "")).strip()
    if not cau_hoi:
        return jsonify(loi="Em chưa nhập câu hỏi."), 400
    if len(cau_hoi) > 500:
        return jsonify(loi="Câu hỏi quá dài (tối đa 500 ký tự)."), 400
    return jsonify(dap_an=giai(cau_hoi))


@app.post("/api/chat")
def api_chat():
    """Trò chuyện qua Gemini hoặc Ollama, theo cấu hình của máy chủ."""
    data = request.get_json(silent=True) or {}
    raw = data.get("messages", [])
    if not isinstance(raw, list):
        return jsonify(loi="Tin nhắn trò chuyện không hợp lệ."), 400

    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    for item in raw[-10:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        content = str(item.get("content", "")).strip()
        if content:
            messages.append({"role": item["role"], "content": content[:1000]})
    if len(messages) == 1 or messages[-1]["role"] != "user":
        return jsonify(loi="Em hãy nhập câu hỏi trước nhé."), 400

    if CHAT_PROVIDER == "gemini":
        try:
            return jsonify(tra_loi=_tao_tra_loi_gemini(messages))
        except ChatProviderError as exc:
            if OLLAMA_FALLBACK_CONFIGURED:
                try:
                    return jsonify(tra_loi=_tao_tra_loi_ollama(messages))
                except ChatProviderError as fallback_exc:
                    return jsonify(loi=(
                        f"{exc.message} Ollama dự phòng cũng gặp lỗi: {fallback_exc.message}"
                    )), max(exc.status, fallback_exc.status)
            return jsonify(loi=exc.message), exc.status
    if CHAT_PROVIDER != "ollama":
        return jsonify(loi="Dịch vụ trò chuyện chưa được cấu hình đúng. Em thử lại sau nhé."), 503

    try:
        return jsonify(tra_loi=_tao_tra_loi_ollama(messages))
    except ChatProviderError as exc:
        if not OLLAMA_FALLBACK_CONFIGURED and exc.status == 503:
            return jsonify(loi="Chưa kết nối được Ollama trên máy này. Cài Ollama rồi chạy setup_chat.bat trong thư mục ứng dụng để tải mô hình miễn phí."), 503
        return jsonify(loi=exc.message), exc.status


@app.post("/api/transcribe")
def api_transcribe():
    """Chuyển giọng nói thành chữ bằng Gemini cho trình duyệt không nhận giọng nói được."""
    data = request.get_json(silent=True) or {}
    audio_b64 = data.get("audio", "")
    mime_type = str(data.get("mime_type", "")).split(";", 1)[0].strip().lower()
    if not isinstance(audio_b64, str) or not audio_b64:
        return jsonify(loi="Chưa nhận được âm thanh. Em thử ghi âm lại nhé."), 400
    if len(audio_b64) > 8 * 1024 * 1024:
        return jsonify(loi="Đoạn ghi âm quá dài. Em hãy nói ngắn hơn rồi thử lại nhé."), 413
    if mime_type not in ("audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav"):
        return jsonify(loi="Định dạng ghi âm này chưa được hỗ trợ. Em thử Chrome hoặc Edge nhé."), 400
    try:
        audio = base64.b64decode(audio_b64, validate=True)
    except (ValueError, base64.binascii.Error):
        return jsonify(loi="Dữ liệu ghi âm chưa đúng định dạng. Em thử ghi âm lại nhé."), 400
    if not audio or len(audio) > 6 * 1024 * 1024:
        return jsonify(loi="Đoạn ghi âm quá dài hoặc trống. Em thử ghi âm lại nhé."), 413

    try:
        result = _gemini_generate({
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": "Chép chính xác lời nói tiếng Việt trong đoạn âm thanh thành văn bản. Chỉ trả về phần lời nói, không giải thích."},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(audio).decode("ascii"),
                        },
                    },
                ],
            }],
            "generationConfig": {"temperature": 0},
        })
        text = _gemini_text(result, "Gemini chưa nghe rõ lời nói. Em thử ghi âm lại nhé.")
        return jsonify(van_ban=text)
    except ChatProviderError as exc:
        return jsonify(loi=exc.message), exc.status


@app.get("/api/voices")
def api_voices():
    """Liệt kê giọng offline và các giọng FPT đã cấu hình."""
    ds = [{"id": k, "nhan": v["nhan"]} for k, v in GIONG.items() if _giong_dung_duoc(v)]
    return jsonify(giong=ds, mac_dinh=giong_mac_dinh())


@app.post("/api/tts")
def api_tts():
    """Tạo giọng đọc; FPT lỗi thì tự chuyển sang mô hình tiếng Việt offline."""
    data = request.get_json(silent=True) or {}
    noi_dung = str(data.get("noi_dung", "")).strip()
    if not noi_dung:
        return jsonify(loi="Chưa có nội dung cần đọc."), 400
    if len(noi_dung) > 3000:
        return jsonify(loi="Nội dung đọc quá dài (tối đa 3000 ký tự)."), 400
    ma = str(data.get("giong") or giong_mac_dinh())
    if ma not in GIONG:
        ma = giong_mac_dinh()
    elif not _giong_dung_duoc(GIONG[ma]):
        if GIONG[ma]["engine"] == "piper":
            return jsonify(loi="Chưa cài bộ đọc offline. Em chạy lại run.bat để cài nhé."), 503
        ma = giong_mac_dinh()
    if not _giong_dung_duoc(GIONG[ma]):
        return jsonify(loi="Chưa cài bộ đọc giọng đã chọn. Em chạy lại run.bat nhé."), 503

    if GIONG[ma]["engine"] == "piper":
        try:
            am_thanh = _tao_piper(noi_dung)
        except Exception:
            app.logger.exception("Không tạo được giọng Piper tiếng Việt offline")
            return jsonify(loi="Không tạo được giọng tiếng Việt offline. Em chạy lại run.bat để cài bộ đọc nhé."), 503
        return Response(am_thanh, mimetype="audio/wav",
                        headers={"Cache-Control": "no-store"})

    # Nếu FPT hết hạn mức, tạo WAV bằng mô hình nằm trên máy, không gọi dịch vụ khác.
    if GIONG[ma]["engine"] == "fpt":
        try:
            am_thanh = _tao_bang_giong(noi_dung, ma)
        except Exception:
            app.logger.warning("FPT không khả dụng (%s); chuyển sang Piper offline", ma)
            if _giong_dung_duoc(GIONG["piper_vi"]):
                try:
                    am_thanh = _tao_piper(noi_dung)
                except Exception:
                    app.logger.exception("Không tạo được giọng Piper dự phòng")
                    return jsonify(loi="FPT đang lỗi và giọng offline chưa chạy được. Em chạy lại run.bat nhé."), 502
                return Response(am_thanh, mimetype="audio/wav",
                                headers={"Cache-Control": "no-store",
                                         "X-TTS-Fallback": "piper_vi"})
            return jsonify(loi="Giọng FPT không khả dụng; ứng dụng chưa có bộ đọc tiếng Việt offline."), 502
        if not am_thanh:
            if _giong_dung_duoc(GIONG["piper_vi"]):
                try:
                    am_thanh = _tao_piper(noi_dung)
                except Exception:
                    app.logger.exception("Không tạo được giọng Piper dự phòng")
                    return jsonify(loi="FPT không trả âm thanh và giọng offline chưa chạy được."), 502
                return Response(am_thanh, mimetype="audio/wav",
                                headers={"Cache-Control": "no-store",
                                         "X-TTS-Fallback": "piper_vi"})
            return jsonify(loi="FPT không trả âm thanh; ứng dụng chưa có bộ đọc tiếng Việt offline."), 502
        return Response(am_thanh, mimetype="audio/mpeg",
                        headers={"Cache-Control": "no-store"})

    am_thanh = b""
    for thu in dict.fromkeys([ma, "piper_vi", GIONG_DU_PHONG]):
        if not _giong_dung_duoc(GIONG[thu]):
            continue
        try:
            am_thanh = _tao_bang_giong(noi_dung, thu)
        except Exception:
            app.logger.exception("Không tạo được giọng nói (%s)", thu)
            am_thanh = b""
        if am_thanh:
            break
    if not am_thanh:
        return jsonify(loi="Không tạo được âm thanh bằng giọng đã chọn."), 502
    headers = {"Cache-Control": "no-store"}
    if thu != ma:
        headers["X-TTS-Fallback"] = thu
    mimetype = "audio/wav" if GIONG[thu]["engine"] == "piper" else "audio/mpeg"
    return Response(am_thanh, mimetype=mimetype, headers=headers)

@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.after_request
def cors_for_github_pages(response):
    if request.path.startswith("/api/"):
        origin = request.headers.get("Origin")
        if origin in _CORS_ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Expose-Headers"] = "X-TTS-Fallback"
            response.vary.add("Origin")
    return response


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=False)
