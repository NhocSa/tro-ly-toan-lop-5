# -*- coding: utf-8 -*-
"""Dung static/de-thi.html cho trang "Đề thi Toán lớp 5".

Chạy:  python build_de.py     (đứng trong thư mục dự án, cạnh app.py)
"""
import io, json, os, re, sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
import de_bank as B

APP = os.environ.get("DETHI_APP", GOC)   # thu muc dự án (chứa static/)


def chuuan(c):
    return {"cd": c["cd"], "muc": c["muc"], "nam": c["nam"], "loai": c["loai"],
            "de": c["de"], "dt": c["dt"], "tl": c["tl"], "giai": c["giai"],
            "luuy": c.get("luuy", "")}


def tao_html():
    loi = B.kiem_tra(B.TUYEN_CHON)
    if loi:
        raise SystemExit("Còn %d câu chưa khớp đáp án:\n%s" % (len(loi), "\n".join(loi)))
    thu_tu = {"Số học": 1, "Hình học": 2, "Đại lượng": 3, "Chuyên đề": 4}
    ds = sorted((chuuan(c) for c in B.TUYEN_CHON), key=lambda c: (thu_tu[c["cd"]], c["muc"]))
    mau = io.open(os.path.join(GOC, "de-thi.template.html"), encoding="utf-8").read()
    nhung = json.dumps(ds, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = mau.replace("@@DS@@", nhung)
    ra = os.path.join(APP, "static", "de-thi.html")
    io.open(ra, "w", encoding="utf-8").write(html)
    return ra, len(ds)


if __name__ == "__main__":
    ra, n = tao_html()
    print("Da tao %s (%d cau)" % (ra, n))
