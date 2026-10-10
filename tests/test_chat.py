import base64
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as web  # noqa: E402


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class TestChat(unittest.TestCase):
    def setUp(self):
        self.client = web.app.test_client()
        self.messages = [
            {"role": "user", "content": "Chào cô"},
            {"role": "assistant", "content": "Cô chào em."},
            {"role": "user", "content": "2 + 3 bằng mấy?"},
        ]

    def test_gemini_maps_prompt_history_and_answer(self):
        body = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "5 em nhé."}]}}],
        }).encode()

        def urlopen(req, timeout):
            self.assertEqual(req.full_url, (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-2.5-flash:generateContent"
            ))
            self.assertEqual(req.get_header("X-goog-api-key"), "private-test-key")
            self.assertEqual(timeout, 120)
            payload = json.loads(req.data.decode())
            self.assertEqual(
                payload["systemInstruction"]["parts"][0]["text"],
                web.CHAT_SYSTEM_PROMPT,
            )
            self.assertEqual(
                payload["contents"],
                [
                    {"role": "user", "parts": [{"text": "Chào cô"}]},
                    {"role": "model", "parts": [{"text": "Cô chào em."}]},
                    {"role": "user", "parts": [{"text": "2 + 3 bằng mấy?"}]},
                ],
            )
            return FakeResponse(body)

        with mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                mock.patch.object(web.urllib.request, "urlopen", side_effect=urlopen):
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"tra_loi": "5 em nhé."})

    def test_gemini_missing_key_returns_friendly_error_without_network(self):
        with mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                mock.patch.object(web, "GEMINI_API_KEY", ""), \
                mock.patch.object(web.urllib.request, "urlopen") as urlopen:
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 503)
        self.assertIn("khóa Gemini", response.get_json()["loi"])
        urlopen.assert_not_called()

    def test_existing_render_environment_aliases_are_supported(self):
        with mock.patch.dict(os.environ, {"API_Gemmini": "test-gemini-key"}, clear=True):
            self.assertEqual(web._doc_khoa_gemini(), "test-gemini-key")
        with mock.patch.dict(os.environ, {"FPT_AI_API": "test-fpt-key"}, clear=True):
            self.assertEqual(web._doc_khoa_fpt(), "test-fpt-key")

    def test_provider_defaults_to_gemini_when_render_alias_exists(self):
        with mock.patch.dict(os.environ, {"API_Gemmini": "test-key"}, clear=True):
            with mock.patch.object(web, "GEMINI_API_KEY", web._doc_khoa_gemini()):
                provider = web._chon_chat_provider()
        self.assertEqual(provider, "gemini")

    def test_provider_defaults_to_ollama_without_gemini_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(web, "GEMINI_API_KEY", ""):
                provider = web._chon_chat_provider()
        self.assertEqual(provider, "ollama")

    def test_gemini_invalid_key_does_not_leak_value(self):
        error = urllib.error.HTTPError("url", 403, "forbidden", {}, None)
        with mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                mock.patch.object(web.urllib.request, "urlopen", side_effect=error):
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 503)
        self.assertIn("chưa hợp lệ", response.get_json()["loi"])
        self.assertNotIn("private-test-key", response.get_data(as_text=True))

    def test_gemini_failure_uses_configured_ollama_backup(self):
        gemini_error = urllib.error.HTTPError("url", 500, "server error", {}, None)
        ollama_response = FakeResponse(
            '{"message":{"content":"Ollama trả lời dự phòng."}}'.encode("utf-8")
        )
        with mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                mock.patch.object(web, "OLLAMA_FALLBACK_CONFIGURED", True), \
                mock.patch.object(
                    web.urllib.request,
                    "urlopen",
                    side_effect=[gemini_error, ollama_response],
                ):
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"tra_loi": "Ollama trả lời dự phòng."})

    def test_gemini_failure_without_ollama_backup_reports_gemini_error(self):
        error = urllib.error.HTTPError("url", 500, "server error", {}, None)
        with mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                mock.patch.object(web, "OLLAMA_FALLBACK_CONFIGURED", False), \
                mock.patch.object(web.urllib.request, "urlopen", side_effect=error):
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 502)
        self.assertIn("HTTP 500", response.get_json()["loi"])

    def test_gemini_and_ollama_failures_are_both_reported(self):
        gemini_error = urllib.error.HTTPError("url", 500, "server error", {}, None)
        with mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                mock.patch.object(web, "OLLAMA_FALLBACK_CONFIGURED", True), \
                mock.patch.object(
                    web.urllib.request,
                    "urlopen",
                    side_effect=[gemini_error, urllib.error.URLError("offline")],
                ):
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 503)
        self.assertIn("Gemini đang gặp sự cố", response.get_json()["loi"])
        self.assertIn("Ollama dự phòng", response.get_json()["loi"])

    def test_gemini_provider_http_network_and_response_errors(self):
        cases = [
            (urllib.error.HTTPError("url", 429, "quota", {}, None), 503, "hết hạn mức"),
            (urllib.error.HTTPError("url", 404, "not found", {}, None), 502, "GEMINI_MODEL"),
            (urllib.error.HTTPError("url", 500, "server error", {}, None), 502, "HTTP 500"),
            (urllib.error.URLError("offline"), 503, "Chưa kết nối"),
            (FakeResponse(b"not-json"), 502, "chưa đúng định dạng"),
            (FakeResponse(b'{"candidates": []}'), 502, "chưa tạo được"),
        ]
        for result, status, message in cases:
            with self.subTest(result=result), \
                    mock.patch.object(web, "CHAT_PROVIDER", "gemini"), \
                    mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                    mock.patch.object(
                        web.urllib.request,
                        "urlopen",
                        side_effect=result if isinstance(result, BaseException) else None,
                        return_value=result,
                    ):
                response = self.client.post("/api/chat", json={"messages": self.messages})
            self.assertEqual(response.status_code, status)
            self.assertIn(message, response.get_json()["loi"])

    def test_ollama_local_contract_is_unchanged(self):
        result = FakeResponse('{"message": {"content": "Cô chào em."}}'.encode("utf-8"))
        with mock.patch.object(web, "CHAT_PROVIDER", "ollama"), \
                mock.patch.object(web.urllib.request, "urlopen", return_value=result) as urlopen:
            response = self.client.post("/api/chat", json={"messages": self.messages})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"tra_loi": "Cô chào em."})
        self.assertIn("127.0.0.1:11434/api/chat", urlopen.call_args.args[0].full_url)

    def test_gemini_transcription_sends_audio_and_returns_text(self):
        audio = b"fake webm audio"
        result = FakeResponse(b'{"candidates":[{"content":{"parts":[{"text":"Chao co"}]}}]}')

        def urlopen(req, timeout):
            payload = json.loads(req.data.decode())
            parts = payload["contents"][0]["parts"]
            self.assertEqual(parts[0]["text"].startswith("Chép chính xác lời nói"), True)
            self.assertEqual(parts[1]["inlineData"]["mimeType"], "audio/webm")
            self.assertEqual(base64.b64decode(parts[1]["inlineData"]["data"]), audio)
            return result

        with mock.patch.object(web, "GEMINI_API_KEY", "private-test-key"), \
                mock.patch.object(web.urllib.request, "urlopen", side_effect=urlopen):
            response = self.client.post("/api/transcribe", json={
                "audio": base64.b64encode(audio).decode("ascii"),
                "mime_type": "audio/webm;codecs=opus",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"van_ban": "Chao co"})

    def test_transcription_rejects_malformed_or_unsupported_audio(self):
        malformed = self.client.post("/api/transcribe", json={
            "audio": "not base64!", "mime_type": "audio/webm",
        })
        unsupported = self.client.post("/api/transcribe", json={
            "audio": base64.b64encode(b"x").decode("ascii"), "mime_type": "audio/xyz",
        })
        self.assertEqual(malformed.status_code, 400)
        self.assertEqual(unsupported.status_code, 400)


if __name__ == "__main__":
    unittest.main()
