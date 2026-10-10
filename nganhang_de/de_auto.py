# -*- coding: utf-8 -*-
"""Ban sinh tu dong: doc SO HOC MUC 1..4 va DAI LUONG MUC 2..4, TINH LAI dap an bang phan so."""
import re
from de_bank import docx_lines, biu_thuc, tu_so, kiem, p

DV = r"(?:km|hm|dam|met|m|dm|cm|mm|tan|ta|yen|kg|hg|dag|g)"
KH = {"+": "+", "-": "-", "*": "×", "×": "×", "x": "×", ":": ":", "/": ":"}


def _nam_theo_dong(lines):
    """Gán năm học cho từng dòng (mỗi file có nhiều 'NGÂN HÀNG')."""
    nam = "2019-2020"
    for d in lines:
        m = re.search(r"(20\d{2})\s*[-–]\s*(20\d{2})", d)
        if m:
            nam = "%s-%s" % (m.group(1), m.group(2))
        yield d, nam


DONG_DT = re.compile(r"(\d+(?:[.,]\d+)?)\s*([+\u00d7x*/:-])\s*(\d+(?:[.,]\d+)?)\s*=\s*(\d+(?:[.,]\d+)?)")
PAT_DL = re.compile(r"(\d+(?:[.,]\d+)?)(?:\s*(" + DV + r"))?\s*([+\u00d7x*/:-])\s*(\d+(?:[.,]\d+)?)\s*(" + DV + r")?(?:\s*=\s*(\d+(?:[.,]\d+)?))?")


def dat_tinh(muc, file):
    """Các phép tính số thập phân có ghi sẵn đáp án -> chỉ giữ bài tính lại thấy đúng."""
    out, thay, trong_manh = [], set(), False
    for dong, nam in _nam_theo_dong(docx_lines(file)):
        if re.search(r'đặt tính', dong, re.I):
            trong_manh = True
        elif re.search(r'bài giải|đáp số', dong, re.I):
            trong_manh = False
        if not trong_manh:
            continue
        for m in DONG_DT.finditer(dong):
            a, op, b, cu = m.group(1), m.group(2), m.group(3), m.group(4)
            toan_tu = "*" if op in "xX" else ("/" if op in "/:" else op)
            gtri = biu_thuc(a + toan_tu + b)
            if gtri is None or not kiem(tu_so(cu), gtri):
                continue
            de = "Đặt tính rồi tính: %s %s %s" % (a, KH[op], b)
            if de in thay:
                continue
            thay.add(de)
            out.append({"cd": "Số học", "muc": muc, "nam": nam, "loai": "dt", "de": de,
                        "dt": [], "tl": p(gtri), "giai": [], "kiem": None, "kiem_kq": None,
                        "nguon": "tự động"})
    return out


def dai_luong(muc, file):
    """Cộng/trừ/nhân/chia số đo đại lượng CÙNG đơn vị (bỏ bài lẫn lộn đơn vị)."""
    out, thay = [], set()
    for dong, nam in _nam_theo_dong(docx_lines(file)):
        if "Đáp án" in dong or "Đáp số" in dong:
            continue
        for m in PAT_DL.finditer(dong):
            a, dv1, op, b, dv2 = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            if dv2 is None or dv1 is not None:
                continue
            dv = {"tan": "tấn", "ta": "tạ", "yen": "yến", "met": "m"}.get(dv2, dv2)
            x, y = tu_so(a), tu_so(b)
            try:
                ket_qua = x + y if op == "+" else x - y if op == "-" else x * y if op in "*×x" else x / y
            except ZeroDivisionError:
                continue
            if ket_qua <= 0:
                continue
            de = "Tính: %s %s %s %s" % (a, KH[op], b, dv)
            if de in thay:
                continue
            thay.add(de)
            out.append({"cd": "Đại lượng", "muc": muc, "nam": nam, "loai": "dt", "de": de,
                        "dt": [], "tl": p(ket_qua) + " " + dv, "giai": [], "kiem": None, "kiem_kq": None,
                        "nguon": "tự động"})
    return out
