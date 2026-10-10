#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRỢ LÝ TOÁN LỚP 5
-----------------
Giải và giải thích từng bước các dạng toán lớp 5 thường gặp.
Chỉ dùng thư viện chuẩn của Python (>= 3.9). Chạy:  python tro_ly_toan_lop5.py

Hoặc dùng như thư viện:
    from tro_ly_toan_lop5 import giai
    print(giai("Tính diện tích hình tròn bán kính 5 cm"))

Lưu ý khi gõ câu hỏi:
  - Số thập phân dùng dấu phẩy hoặc dấu chấm: 3,5 hoặc 3.5
  - Khi liệt kê nhiều số, hãy viết cách nhau bằng chữ "và" hoặc dấu cách.
"""
import ast
import math
import operator
import re
import unicodedata
from collections import Counter
from fractions import Fraction

NUM = r"(\d+(?:[.,]\d+)?)"
PI = Fraction("3.14")  # Lớp 5 dùng π ≈ 3,14


# ----------------------------------------------------------------------------
# Tiện ích
# ----------------------------------------------------------------------------
def bo_dau(s: str) -> str:
    """Chuyển về chữ thường, bỏ dấu tiếng Việt để dễ so khớp từ khóa."""
    s = s.lower().replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def to_frac(s: str) -> Fraction:
    return Fraction(s.replace(",", "."))


def so(x) -> str:
    """Định dạng số kiểu Việt Nam: 3,5 ; 2/3 (≈ 0,6667)."""
    x = Fraction(x)
    if x.denominator == 1:
        return str(x.numerator)
    d = x.denominator
    while d % 2 == 0:
        d //= 2
    while d % 5 == 0:
        d //= 5
    if d == 1:  # thập phân hữu hạn
        return f"{float(x):.10f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{x.numerator}/{x.denominator} (≈ {float(x):.4f})".replace(".", ",")


def tinh_bieu_thuc(expr: str) -> Fraction:
    """Tính biểu thức an toàn (chỉ + - * / và ngoặc), dùng phân số để chính xác."""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
                and not isinstance(n.value, bool):
            return Fraction(str(n.value))
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        raise ValueError("biểu thức không hợp lệ")

    return ev(ast.parse(expr, mode="eval"))


def phan_tich(n: int) -> Counter:
    c, d = Counter(), 2
    while d * d <= n:
        while n % d == 0:
            c[d] += 1
            n //= d
        d += 1
    if n > 1:
        c[n] += 1
    return c


def tich_tsnt(c: Counter) -> str:
    return " × ".join(f"{p}^{e}" if e > 1 else str(p)
                      for p, e in sorted(c.items())) or "1"


# ----------------------------------------------------------------------------
# 1. Tìm x
# ----------------------------------------------------------------------------
def h_phuong_trinh(t):
    e = re.sub(r"^(?:tim|tinh)\s*x\s*[:,]?\s*", "", t).strip().rstrip("?. ")
    A = r"(x|\d+(?:[.,]\d+)?)"
    m = re.fullmatch(A + r"\s*([+\-*/:×÷x])\s*" + A + r"\s*=\s*" + NUM, e)
    if not m:
        return None
    a, op, b, kv = m.groups()
    if (a == "x") == (b == "x"):  # phải có đúng một ẩn x
        return None
    op = {"×": "*", "x": "*", "÷": "/", ":": "/"}.get(op, op)
    B = to_frac(kv)
    if a == "x":
        c = to_frac(b)
        if op == "+":
            x, rule = B - c, "x là số hạng chưa biết → lấy tổng trừ số hạng đã biết"
            calc = f"x = {so(B)} - {so(c)}"
        elif op == "-":
            x, rule = B + c, "x là số bị trừ → lấy hiệu cộng số trừ"
            calc = f"x = {so(B)} + {so(c)}"
        elif op == "*":
            x, rule = B / c, "x là thừa số chưa biết → lấy tích chia thừa số đã biết"
            calc = f"x = {so(B)} : {so(c)}"
        else:
            x, rule = B * c, "x là số bị chia → lấy thương nhân số chia"
            calc = f"x = {so(B)} × {so(c)}"
    else:
        c = to_frac(a)
        if op == "+":
            x, rule = B - c, "x là số hạng chưa biết → lấy tổng trừ số hạng đã biết"
            calc = f"x = {so(B)} - {so(c)}"
        elif op == "-":
            x, rule = c - B, "x là số trừ → lấy số bị trừ trừ hiệu"
            calc = f"x = {so(c)} - {so(B)}"
        elif op == "*":
            x, rule = B / c, "x là thừa số chưa biết → lấy tích chia thừa số đã biết"
            calc = f"x = {so(B)} : {so(c)}"
        else:
            x, rule = c / B, "x là số chia → lấy số bị chia chia cho thương"
            calc = f"x = {so(c)} : {so(B)}"
    f = {"+": operator.add, "-": operator.sub, "*": operator.mul,
         "/": operator.truediv}[op]
    sym = {"+": "+", "-": "-", "*": "×", "/": ":"}[op]
    va = x if a == "x" else to_frac(a)
    vb = x if b == "x" else to_frac(b)
    thu = f(va, vb)
    return (f"Bài toán: {a} {sym} {b} = {so(B)}\n"
            f"Cách làm: {rule}\n"
            f"  {calc} = {so(x)}\n"
            f"Thử lại: {so(va)} {sym} {so(vb)} = {so(thu)} {'✓' if thu == B else '✗'}\n"
            f"Đáp số: x = {so(x)}")


# ----------------------------------------------------------------------------
# 2. Đổi đơn vị (độ dài, khối lượng)
# ----------------------------------------------------------------------------
DAI = {"km": 1000, "hm": 100, "dam": 10, "m": 1,
       "dm": Fraction(1, 10), "cm": Fraction(1, 100), "mm": Fraction(1, 1000)}
KHOI = {"tan": 10 ** 6, "ta": 10 ** 5, "yen": 10 ** 4, "kg": 1000,
        "hg": 100, "dag": 10, "g": 1}
BIET_DANH = {"met": "m", "gam": "g", "kilogam": "kg"}
HIEN_THI = {"tan": "tấn", "ta": "tạ", "yen": "yến"}


def h_doi_don_vi(t):
    m = re.search(r"doi\s*" + NUM + r"\s*([a-z]+)\s*(?:ra|sang|thanh|=)\s*([a-z]+)", t)
    if not m:
        return None
    x = to_frac(m.group(1))
    a = BIET_DANH.get(m.group(2), m.group(2))
    b = BIET_DANH.get(m.group(3), m.group(3))
    for bang in (DAI, KHOI):
        if a in bang and b in bang:
            ti_le = Fraction(bang[a]) / Fraction(bang[b])
            kq = x * ti_le
            ha, hb = HIEN_THI.get(a, a), HIEN_THI.get(b, b)
            return (f"Hai đơn vị liền kề hơn kém nhau 10 lần.\n"
                    f"1 {ha} = {so(ti_le)} {hb}\n"
                    f"{so(x)} {ha} = {so(x)} × {so(ti_le)} = {so(kq)} {hb}")
    return None


# ----------------------------------------------------------------------------
# 3. ƯCLN, BCNN
# ----------------------------------------------------------------------------
def h_ucln_bcnn(t):
    hoi_u = "ucln" in t or "uoc chung lon nhat" in t
    hoi_b = "bcnn" in t or "boi chung nho nhat" in t
    if not (hoi_u or hoi_b):
        return None
    ds = [int(x) for x in re.findall(r"\d+", t)]
    if len(ds) < 2 or any(n <= 0 or n > 10 ** 12 for n in ds):
        return "Em cho ít nhất 2 số nguyên dương nhé, ví dụ: ƯCLN của 12 và 18."
    fs = [phan_tich(n) for n in ds]
    out = ["Phân tích ra thừa số nguyên tố:"]
    out += [f"  {n} = {tich_tsnt(f)}" for n, f in zip(ds, fs)]
    if hoi_u:
        chung = set.intersection(*[set(f) for f in fs])
        kq = Counter({p: min(f[p] for f in fs) for p in chung})
        out.append("ƯCLN = tích các thừa số nguyên tố CHUNG, mỗi thừa số lấy số mũ NHỎ nhất:")
        out.append(f"  ƯCLN = {tich_tsnt(kq)} = {math.gcd(*ds)}")
    if hoi_b:
        moi = set().union(*[set(f) for f in fs])
        kq = Counter({p: max(f[p] for f in fs) for p in moi})
        out.append("BCNN = tích các thừa số nguyên tố CHUNG và RIÊNG, mỗi thừa số lấy số mũ LỚN nhất:")
        out.append(f"  BCNN = {tich_tsnt(kq)} = {math.lcm(*ds)}")
    return "\n".join(out)


# ----------------------------------------------------------------------------
# 4. Phân số: rút gọn, quy đồng, so sánh
# ----------------------------------------------------------------------------
def h_phan_so(t):
    fr = [(int(a), int(b)) for a, b in re.findall(r"(\d+)\s*/\s*(\d+)", t)]
    if any(b == 0 for _, b in fr):
        return "Mẫu số không được bằng 0 em nhé!"

    if "rut gon" in t and fr:
        a, b = fr[0]
        g = math.gcd(a, b)
        if g == 1:
            return f"{a}/{b} đã là phân số tối giản (ƯCLN({a}, {b}) = 1)."
        return (f"ƯCLN({a}, {b}) = {g}\n"
                f"Chia cả tử và mẫu cho {g}: {a}/{b} = ({a} : {g})/({b} : {g}) = {a // g}/{b // g}")

    if "quy dong" in t and len(fr) >= 2:
        m = math.lcm(*[b for _, b in fr])
        out = [f"Mẫu số chung = BCNN các mẫu = {m}"]
        for a, b in fr:
            k = m // b
            out.append(f"  {a}/{b} = ({a} × {k})/({b} × {k}) = {a * k}/{m}")
        return "\n".join(out)

    if "so sanh" in t:
        if len(fr) >= 2:
            (a1, b1), (a2, b2) = fr[:2]
            m = math.lcm(b1, b2)
            x, y = a1 * (m // b1), a2 * (m // b2)
            dau = ">" if x > y else "<" if x < y else "="
            return (f"Quy đồng mẫu số chung {m}:\n"
                    f"  {a1}/{b1} = {x}/{m}\n  {a2}/{b2} = {y}/{m}\n"
                    f"Vì {x} {dau} {y} nên {a1}/{b1} {dau} {a2}/{b2}")
        ns = [to_frac(x) for x in re.findall(NUM, t)]
        if len(ns) >= 2:
            x, y = ns[:2]
            dau = ">" if x > y else "<" if x < y else "="
            return (f"So sánh phần nguyên trước, rồi lần lượt từng hàng phần thập phân.\n"
                    f"{so(x)} {dau} {so(y)}")
    return None


# ----------------------------------------------------------------------------
# 5. Tỉ số phần trăm
# ----------------------------------------------------------------------------
def h_phan_tram(t):
    m = re.search(r"ti so phan tram cua\s*" + NUM + r"\s*(?:va|voi)\s*" + NUM, t) or \
        re.search(NUM + r"\s*(?:la\s*)?bao nhieu\s*(?:phan tram|%)\s*cua\s*(?:so\s*)?" + NUM, t)
    if m:
        a, b = to_frac(m.group(1)), to_frac(m.group(2))
        kq = a / b * 100
        return (f"Tỉ số phần trăm của {so(a)} và {so(b)}:\n"
                f"  {so(a)} : {so(b)} × 100 = {so(kq)}%")
    m = re.search(NUM + r"\s*%\s*cua\s*(?:mot\s*)?so\s*(?:nao\s*)?(?:la|bang)\s*" + NUM, t)
    if m:
        p, c = to_frac(m.group(1)), to_frac(m.group(2))
        kq = c / p * 100
        return (f"Tìm một số biết {so(p)}% của nó là {so(c)}:\n"
                f"  {so(c)} : {so(p)} × 100 = {so(kq)}")
    m = re.search(NUM + r"\s*%\s*cua\s*(?:so\s*)?" + NUM, t)
    if m:
        p, b = to_frac(m.group(1)), to_frac(m.group(2))
        kq = b * p / 100
        return (f"Tìm {so(p)}% của {so(b)}:\n"
                f"  {so(b)} × {so(p)} : 100 = {so(kq)}")
    return None


# ----------------------------------------------------------------------------
# 6. Hình học
# ----------------------------------------------------------------------------
def don_vi(t):
    m = re.search(r"\d\s*(km|dm|cm|mm|met|m)(?![a-z])", t)
    return "m" if m and m.group(1) == "met" else (m.group(1) if m else "")


def h_hinh_hoc(t):
    if not re.search(r"dien tich|chu vi|the tich|xung quanh|toan phan", t):
        return None
    ns = [to_frac(x) for x in re.findall(NUM, t)]
    u = don_vi(t)
    hs, hp = "dien tich" in t, "chu vi" in t
    thieu = "Cô chưa đọc đủ số đo của hình. Em ghi rõ các số đo giúp cô nhé."

    def L(v, mu=1):
        suf = {1: "", 2: "²", 3: "³"}[mu]
        return f"{so(v)} {u}{suf}" if u else so(v)

    out = []
    chi_dinh = any(k in t for k in ("the tich", "xung quanh", "toan phan"))

    if "lap phuong" in t:
        if not ns:
            return thieu
        a = ns[0]
        out.append(f"Hình lập phương cạnh a = {L(a)}")
        if "the tich" in t or not chi_dinh:
            out.append(f"Thể tích: V = a × a × a = {so(a)} × {so(a)} × {so(a)} = {L(a ** 3, 3)}")
        if "xung quanh" in t or not chi_dinh:
            out.append(f"Diện tích xung quanh: Sxq = a × a × 4 = {L(a * a * 4, 2)}")
        if "toan phan" in t or not chi_dinh:
            out.append(f"Diện tích toàn phần: Stp = a × a × 6 = {L(a * a * 6, 2)}")

    elif "hop chu nhat" in t:
        if len(ns) < 3:
            return thieu
        a, b, c = ns[:3]
        sxq = (a + b) * 2 * c
        out.append(f"Hình hộp chữ nhật: dài {L(a)}, rộng {L(b)}, cao {L(c)}")
        if "the tich" in t or not chi_dinh:
            out.append(f"Thể tích: V = dài × rộng × cao = {so(a)} × {so(b)} × {so(c)} = {L(a * b * c, 3)}")
        if "xung quanh" in t or not chi_dinh:
            out.append(f"Diện tích xung quanh: Sxq = (dài + rộng) × 2 × cao = "
                       f"({so(a)} + {so(b)}) × 2 × {so(c)} = {L(sxq, 2)}")
        if "toan phan" in t or not chi_dinh:
            out.append(f"Diện tích toàn phần: Stp = Sxq + 2 × S đáy = {so(sxq)} + 2 × {so(a * b)} = "
                       f"{L(sxq + 2 * a * b, 2)}")

    elif "tam giac" in t:
        if hs:
            if len(ns) < 2:
                return thieu
            d, h = ns[:2]
            out.append(f"Diện tích hình tam giác: S = đáy × chiều cao : 2 = {so(d)} × {so(h)} : 2 = {L(d * h / 2, 2)}")
        if hp:
            if len(ns) < 3:
                return thieu
            a, b, c = ns[:3]
            out.append(f"Chu vi hình tam giác: P = a + b + c = {so(a)} + {so(b)} + {so(c)} = {L(a + b + c)}")

    elif "hinh thang" in t:
        if len(ns) < 3:
            return thieu
        a, b, h = ns[:3]
        out.append(f"Diện tích hình thang: S = (đáy lớn + đáy bé) × chiều cao : 2 = "
                   f"({so(a)} + {so(b)}) × {so(h)} : 2 = {L((a + b) * h / 2, 2)}")

    elif "binh hanh" in t:
        if len(ns) < 2:
            return thieu
        a, b = ns[:2]
        if hs:
            out.append(f"Diện tích hình bình hành: S = đáy × chiều cao = {so(a)} × {so(b)} = {L(a * b, 2)}")
        if hp:
            out.append(f"Chu vi hình bình hành: P = (a + b) × 2 = ({so(a)} + {so(b)}) × 2 = {L((a + b) * 2)}")

    elif "hinh thoi" in t:
        if hs:
            if len(ns) < 2:
                return thieu
            a, b = ns[:2]
            out.append(f"Diện tích hình thoi: S = (đường chéo 1 × đường chéo 2) : 2 = "
                       f"{so(a)} × {so(b)} : 2 = {L(a * b / 2, 2)}")
        if hp:
            if not ns:
                return thieu
            out.append(f"Chu vi hình thoi: P = cạnh × 4 = {so(ns[0])} × 4 = {L(ns[0] * 4)}")

    elif "hinh tron" in t:
        if not ns:
            return thieu
        if "duong kinh" in t and "ban kinh" not in t:
            r = ns[0] / 2
            out.append(f"Bán kính: r = đường kính : 2 = {so(ns[0])} : 2 = {L(r)}")
        else:
            r = ns[0]
        if hp or not hs:
            out.append(f"Chu vi hình tròn: C = r × 2 × 3,14 = {so(r)} × 2 × 3,14 = {L(r * 2 * PI)}")
        if hs or not hp:
            out.append(f"Diện tích hình tròn: S = r × r × 3,14 = {so(r)} × {so(r)} × 3,14 = {L(r * r * PI, 2)}")

    elif "hinh vuong" in t:
        if not ns:
            return thieu
        a = ns[0]
        if hs:
            out.append(f"Diện tích hình vuông: S = cạnh × cạnh = {so(a)} × {so(a)} = {L(a * a, 2)}")
        if hp:
            out.append(f"Chu vi hình vuông: P = cạnh × 4 = {so(a)} × 4 = {L(a * 4)}")

    elif "chu nhat" in t:
        if len(ns) < 2:
            return thieu
        a, b = ns[:2]
        if hs:
            out.append(f"Diện tích hình chữ nhật: S = dài × rộng = {so(a)} × {so(b)} = {L(a * b, 2)}")
        if hp:
            out.append(f"Chu vi hình chữ nhật: P = (dài + rộng) × 2 = ({so(a)} + {so(b)}) × 2 = {L((a + b) * 2)}")

    return "\n".join(out) if out else None


# ----------------------------------------------------------------------------
# 7. Chuyển động đều: vận tốc – quãng đường – thời gian
# ----------------------------------------------------------------------------
HE = {"gio": Fraction(1), "h": Fraction(1), "phut": Fraction(1, 60),
      "giay": Fraction(1, 3600), "s": Fraction(1, 3600)}
TEN = {"gio": "giờ", "h": "giờ", "phut": "phút", "giay": "giây", "s": "giây"}
DK = {"km": 1000, "m": 1, "met": 1}


def _gio_phut(T):
    if T.denominator != 1:
        ip = int(T // 1)
        ph = (T - ip) * 60
        return f" = {ip} giờ {so(ph)} phút"
    return ""


def h_chuyen_dong(t):
    if not re.search(r"van toc|quang duong|thoi gian|km/|m/s|m/phut", t):
        return None
    mv = re.search(NUM + r"\s*(km|met|m)\s*/\s*(gio|h|phut|giay|s)(?![a-z])", t)
    ms = re.search(NUM + r"\s*(km|met|m)(?![a-z/0-9])", t)
    tp = re.findall(NUM + r"\s*(gio|h|phut|giay|s)(?![a-z])", t)
    t_gio = sum((to_frac(n) * HE[u] for n, u in tp), Fraction(0)) if tp else None

    if mv and t_gio is not None and not ms:
        v = to_frac(mv.group(1))
        ud = "m" if mv.group(2) == "met" else mv.group(2)
        ut = mv.group(3)
        tt = t_gio / HE[ut]
        S = v * tt
        return (f"Quãng đường = vận tốc × thời gian\n"
                f"  s = {so(v)} × {so(tt)} = {so(S)} {ud}")
    if mv and ms and t_gio is None:
        v = to_frac(mv.group(1))
        ud = "m" if mv.group(2) == "met" else mv.group(2)
        ut = mv.group(3)
        us = "m" if ms.group(2) == "met" else ms.group(2)
        s = to_frac(ms.group(1)) * Fraction(DK[us], DK[ud])
        T = s / v
        extra = _gio_phut(T) if TEN[ut] == "giờ" else ""
        return (f"Thời gian = quãng đường : vận tốc\n"
                f"  t = {so(s)} : {so(v)} = {so(T)} {TEN[ut]}{extra}")
    if ms and t_gio is not None and not mv:
        s = to_frac(ms.group(1))
        us = "m" if ms.group(2) == "met" else ms.group(2)
        V = s / t_gio
        return (f"Vận tốc = quãng đường : thời gian\n"
                f"  v = {so(s)} : {so(t_gio)} = {so(V)} {us}/giờ")
    return None


# ----------------------------------------------------------------------------
# 8. Trung bình cộng
# ----------------------------------------------------------------------------
def h_trung_binh(t):
    if "trung binh cong" not in t:
        return None
    ns = [to_frac(x) for x in re.findall(NUM, t)]
    if len(ns) < 2:
        return None
    tong = sum(ns, Fraction(0))
    return (f"Trung bình cộng = tổng các số : số các số hạng\n"
            f"  Tổng = {' + '.join(so(n) for n in ns)} = {so(tong)}\n"
            f"  TBC = {so(tong)} : {len(ns)} = {so(tong / len(ns))}")


# ----------------------------------------------------------------------------
# 9. Tính giá trị biểu thức
# ----------------------------------------------------------------------------
def h_bieu_thuc(t):
    e = re.sub(r"^(?:hay\s+)?(?:tinh gia tri bieu thuc|gia tri cua bieu thuc|"
               r"ket qua cua|tim ket qua|tinh)\s*:?\s*", "", t).strip()
    e = e.rstrip("=? ").strip()
    if not re.fullmatch(r"[\d\s+\-*/().:x×÷,]+", e):
        return None
    if not re.search(r"[+\-*/:x×÷]", e):
        return None
    e2 = e.replace("x", "*").replace("×", "*").replace("÷", "/").replace(":", "/")
    e2 = re.sub(r"(?<=\d),(?=\d)", ".", e2)
    kq = tinh_bieu_thuc(e2)
    return (f"{e} = {so(kq)}\n"
            f"(Nhớ: trong ngoặc làm trước, nhân chia trước, cộng trừ sau, "
            f"cùng cấp thì làm từ trái sang phải.)")


# ----------------------------------------------------------------------------
# Bộ điều phối
# ----------------------------------------------------------------------------
GOI_Y = """Cô chưa hiểu câu này. Em thử hỏi theo các dạng sau nhé:
  • Biểu thức:      (3,5 + 2,5) x 4 - 10 : 5
  • Tìm x:          x + 3,5 = 8   |   12 : x = 4
  • Phân số:        rút gọn 12/18 | quy đồng 1/2 và 3/4 | so sánh 2/3 và 3/5
  • ƯCLN, BCNN:    ƯCLN và BCNN của 12 và 18
  • Phần trăm:      20% của 150 | 30 là bao nhiêu phần trăm của 120
  • Hình học:       diện tích hình tròn bán kính 5 cm | chu vi hình chữ nhật dài 8 cm rộng 5 cm
                    thể tích hình hộp chữ nhật 6 4 3 cm | diện tích hình thang 8 5 4 cm
  • Chuyển động:    ô tô đi 120 km hết 2 giờ, tính vận tốc | vận tốc 40 km/giờ đi 3 giờ, tính quãng đường
  • Đổi đơn vị:     đổi 2,5 km sang m | đổi 3 tấn ra kg
  • Trung bình:     trung bình cộng của 5 và 7 và 12"""

HANDLERS = [h_phuong_trinh, h_doi_don_vi, h_ucln_bcnn, h_phan_so, h_phan_tram,
            h_hinh_hoc, h_chuyen_dong, h_trung_binh, h_bieu_thuc]


def giai(cau_hoi: str) -> str:
    t = bo_dau(cau_hoi).strip()
    for h in HANDLERS:
        try:
            kq = h(t)
        except ZeroDivisionError:
            return "Không thể chia cho 0 em nhé!"
        except Exception:
            kq = None
        if kq:
            return kq
    return GOI_Y


def main():
    print("=" * 60)
    print("  TRỢ LÝ TOÁN LỚP 5  –  gõ 'help' để xem ví dụ, 'thoat' để thoát")
    print("=" * 60)
    while True:
        try:
            q = input("\nCâu hỏi: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt em, chúc em học tốt!")
            break
        if not q:
            continue
        k = bo_dau(q)
        if k in {"thoat", "exit", "quit", "tam biet"}:
            print("Tạm biệt em, chúc em học tốt!")
            break
        if k in {"help", "tro giup", "huong dan", "?"}:
            print(GOI_Y)
            continue
        print("\n" + giai(q))


if __name__ == "__main__":
    main()
