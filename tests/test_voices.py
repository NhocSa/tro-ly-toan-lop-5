import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as web  # noqa: E402


class TestGiongNu(unittest.TestCase):
    def setUp(self):
        self.c = web.app.test_client()
        p = mock.patch.object(web, "edge_tts", object())  # test không cần cài edge-tts thật
        p.start()
        self.addCleanup(p.stop)
        k = mock.patch.object(web, "FPT_API_KEY", "")  # mặc định coi như chưa có khóa FPT
        k.start()
        self.addCleanup(k.stop)

    def test_danh_sach_khong_co_fpt_khi_thieu_khoa(self):
        with mock.patch.object(web, "FPT_API_KEY", ""):
            ids = [g["id"] for g in self.c.get("/api/voices").get_json()["giong"]]
        self.assertIn("hoaimy", ids)
        self.assertFalse([i for i in ids if i.startswith("fpt_")])

    def test_co_giong_nam_bo_fpt_khi_co_khoa(self):
        with mock.patch.object(web, "FPT_API_KEY", "abc"):
            ids = [g["id"] for g in self.c.get("/api/voices").get_json()["giong"]]
        self.assertIn("fpt_lannhi", ids)
        self.assertIn("fpt_linhsan", ids)

    def test_dung_giong_da_chon(self):
        goi = []
        def gia(nd, ma):
            goi.append(ma)
            return b"mp3"
        with mock.patch.object(web, "_tao_bang_giong", gia):
            r = self.c.post("/api/tts", json={"noi_dung": "xin chào", "giong": "gtts"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(goi, ["gtts"])

    def test_loi_thi_lui_ve_hoai_my(self):
        def gia(nd, ma):
            if ma == "gtts":
                raise RuntimeError("mất mạng")
            return b"mp3"
        with mock.patch.object(web, "_tao_bang_giong", gia):
            r = self.c.post("/api/tts", json={"noi_dung": "xin chào", "giong": "gtts"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, b"mp3")

    def test_co_khoa_thi_mac_dinh_linh_san(self):
        with mock.patch.object(web, "FPT_API_KEY", "abc"):
            self.assertEqual(self.c.get("/api/voices").get_json()["mac_dinh"], "fpt_linhsan")
        self.assertEqual(self.c.get("/api/voices").get_json()["mac_dinh"], "hoaimy")

    def test_giong_la_bi_bo_qua(self):
        goi = []
        with mock.patch.object(web, "_tao_bang_giong", lambda nd, ma: goi.append(ma) or b"x"):
            self.c.post("/api/tts", json={"noi_dung": "a", "giong": "../etc"})
        self.assertEqual(goi, ["hoaimy"])


if __name__ == "__main__":
    unittest.main()
