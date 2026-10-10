import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathbot import giai  # noqa: E402


class TestSolver(unittest.TestCase):
    def check(self, cau_hoi, mong_doi):
        kq = giai(cau_hoi)
        self.assertIn(mong_doi, kq, f"{cau_hoi!r} -> {kq!r}")

    def test_bieu_thuc(self):
        self.check("(3,5 + 2,5) x 4 - 10 : 5", "= 22")
        self.check("1/2 + 1/3", "5/6")

    def test_tim_x(self):
        self.check("x + 3,5 = 8", "x = 4,5")
        self.check("12 : x = 4", "x = 3")
        self.check("x - 2 = 5", "x = 7")

    def test_phan_so(self):
        self.check("rút gọn 12/18", "2/3")
        self.check("so sánh 2/3 và 3/5", "2/3 > 3/5")
        self.check("quy đồng 1/2 và 3/4", "2/4")

    def test_ucln_bcnn(self):
        kq = giai("ƯCLN và BCNN của 12 và 18")
        self.assertIn("= 6", kq)
        self.assertIn("= 36", kq)

    def test_phan_tram(self):
        self.check("20% của 150", "= 30")
        self.check("30 là bao nhiêu phần trăm của 120", "25%")

    def test_hinh_hoc(self):
        self.check("diện tích hình tròn bán kính 5 cm", "78,5 cm²")
        self.check("chu vi hình chữ nhật dài 8 cm rộng 5 cm", "26 cm")
        self.check("thể tích hình lập phương cạnh 5 dm", "125 dm³")
        self.check("diện tích hình thang đáy lớn 8 cm đáy bé 5 cm cao 4 cm", "26 cm²")

    def test_chuyen_dong(self):
        self.check("Ô tô đi 120 km hết 2 giờ. Tính vận tốc", "60 km/giờ")
        self.check("Quãng đường 100 km, vận tốc 40 km/giờ. Tính thời gian", "2 giờ 30 phút")

    def test_doi_don_vi_va_trung_binh(self):
        self.check("đổi 2,5 km sang m", "2500 m")
        self.check("đổi 3 tấn ra kg", "3000 kg")
        self.check("trung bình cộng của 5 và 7 và 12", "= 8")

    def test_chia_cho_0_va_cau_la(self):
        self.check("5 : 0", "chia cho 0")
        self.check("xin chào", "chưa hiểu")


class TestWeb(unittest.TestCase):
    def setUp(self):
        try:
            from app import app
        except ImportError:
            self.skipTest("Chưa cài flask")
        self.c = app.test_client()

    def test_trang_chu(self):
        self.assertEqual(self.c.get("/").status_code, 200)

    def test_frontend_config(self):
        r = self.c.get("/config.js")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'assetBase: "/static"', r.data)

    def test_api(self):
        r = self.c.post("/api/giai", json={"cau_hoi": "20% của 150"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("= 30", r.get_json()["dap_an"])
        self.assertEqual(self.c.post("/api/giai", json={"cau_hoi": ""}).status_code, 400)

    def test_cors_for_github_pages(self):
        allowed = self.c.post(
            "/api/giai",
            json={"cau_hoi": "20% của 150"},
            headers={"Origin": "https://nhocsa.github.io"},
        )
        self.assertEqual(allowed.headers["Access-Control-Allow-Origin"], "https://nhocsa.github.io")

        blocked = self.c.post(
            "/api/giai",
            json={"cau_hoi": "20% của 150"},
            headers={"Origin": "https://example.com"},
        )
        self.assertNotIn("Access-Control-Allow-Origin", blocked.headers)

        preflight = self.c.options(
            "/api/voices",
            headers={
                "Origin": "https://nhocsa.github.io",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(preflight.headers["Access-Control-Allow-Origin"], "https://nhocsa.github.io")


if __name__ == "__main__":
    unittest.main()
