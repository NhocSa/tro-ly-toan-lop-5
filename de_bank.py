# -*- coding: utf-8 -*-
"""Nội dung cho trang "Đề thi Toán lớp 5" (de-thi.html).

Gồm 2 phần:
  1) TỰ ĐỘNG: đọc các file .docx/.doc đã trích xuất, lấy các bài "Đặt tính rồi tính"
     và các bài "Tính" (đại lượng), TỰ TÍNH LẠI đáp án bằng phân số -> chỉ giữ bài đúng.
  2) TUYỂN CHỌN: các bài có lời văn / trắc nghiệm / chuyên đề viết lại sạch sẽ,
     có kiểm tra đáp số bằng hàm kiem() (nếu sai sẽ in cảnh báo khi build).

Mỗi câu: {"cd": chủ đề, "muc": 1..4, "nam": "2019-2020"|None, "loai": "tl"|"tn"|"dt",
          "de": ..., "dt": [các ý a,b,c,d] (nếu trắc nghiệm), "tl": đáp án, "giai": [các bước]}
"""
import os, re, glob, zipfile, html
from decimal import Decimal
from fractions import Fraction as F

# =====================================================================
# 1. TIỆN ÍCH: đọc docx / doc
# =====================================================================
GOC = os.path.dirname(os.path.abspath(__file__))


def _omml(x):
    def f(m):
        parts = re.split(r"<m:num\b[^>]*>|</m:num>|<m:den\b[^>]*>|</m:den>", m.group(1))
        clean = lambda s: "".join(html.unescape(t) for t in re.findall(r"<m:t[^>]*>(.*?)</m:t>", s, re.S)).strip()
        tu, mau = clean(parts[0]), clean("".join(parts[1:])) if len(parts) > 1 else ""
        return "(%s/%s)" % (tu, mau) if tu and mau else tu
    for _ in range(8):
        new = re.sub(r"<m:f\b[^>]*>(.*?)</m:f>", f, x, flags=re.S)
        if new == x:
            break
        x = new
    x = re.sub(r"<m:radPr\b.*?</m:radPr>", "", x, flags=re.S)
    return re.sub(r"<m:rad\b[^>]*>(.*?)</m:rad>", r"căn\1", x, flags=re.S)


def docx_lines(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    b = _omml(xml[xml.find("<w:body"):])
    b = re.sub(r"<w:tab[^>]*/>", " ", b)
    b = re.sub(r"<w:br[^>]*/>", " ", b)
    b = b.replace("</w:p>", "\n").replace("</w:tr>", "\n").replace("</w:tc>", " ")
    t = html.unescape(re.sub(r"<[^>]+>", "", b))
    t = (t.replace("\u00a0", " ").replace("\ufeff", "").replace("\u200b", "").replace("\uf0b7", "•")
          .replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-"))
    return [re.sub(r" {2,}", " ", d).strip() for d in t.split("\n") if d.strip()]


def tu_so(s):
    return so_phan(s)




def biu_thuc(t):
    """'21,15 × 0,65' -> Fraction; None nếu không tính được."""
    t = t.replace("×", "*").replace("x", "*").replace("÷", "/").replace(":", "/")
    t = t.replace("–", "-").replace("—", "-").replace("−", "-").replace(" ", " ")
    t = re.sub(r"\s+", "", t)
    if not re.fullmatch(r"[\d.,()+*/-]+", t):
        return None
    t = re.sub(r"(\d)\.(\d)", r"\1,\2", t)          # khôi phục dấu phẩy thập phân
    try:
        return _eval_phan_so(t)
    except Exception:
        return None


def so_phan(s):
    """Chuyen '21,15' thanh Fraction chinh xac (khong dung so thuc phay)."""
    s = s.strip().replace(",", ".")
    if "." in s:
        tu, mau = s.split(".")
        tu = (tu or "0").lstrip("+")
        return F(int(tu + mau), 10 ** len(mau))
    return F(int(s))


def _eval_phan_so(s):
    """Dch biu thc cng tr nhn chia thnh Fraction."""
    i = 0

    def ws():
        nonlocal i
        while i < len(s) and s[i] == " ":
            i += 1

    def E():
        nonlocal i
        v = T()
        ws()
        while i < len(s) and s[i] in "+-":
            o = s[i]; i += 1
            r = T()
            v = v + r if o == "+" else v - r
            ws()
        return v

    def T():
        nonlocal i
        v = U()
        ws()
        while i < len(s) and s[i] in "*/":
            o = s[i]; i += 1
            r = U()
            v = v * r if o == "*" else v / r
            ws()
        return v

    def U():
        nonlocal i
        ws()
        if s[i] == "-":
            i += 1
            return -U()
        if s[i] == "(":
            i += 1
            v = E()
            ws()
            i += 1
            return v
        m = re.match(r"\d+(?:\.\d+)?", s[i:])
        if not m:
            raise ValueError("khong doc duoc")
        i += len(m.group(0))
        return so_phan(m.group(0))

    v = E()
    ws()
    if i != len(s):
        raise ValueError("khong doc duoc")
    return v


def p(t):
    """Fraction -> chuỗi kiểu Việt, làm gọn số chẵn."""
    if t.denominator == 1:
        return str(t.numerator)
    x = Decimal(t.numerator) / Decimal(t.denominator)
    return format(x.normalize(), "f").replace(".", ",")


def kiem(expect, got):
    return got is not None and abs(F(got) - F(expect)) <= F(1, 1000)


def nam_cua(lines):
    for d in lines[:6]:
        m = re.search(r"(20\d{2})\s*[-–]\s*(20\d{2})", d)
        if m:
            return "%s-%s" % (m.group(1), m.group(2))
    return "2019-2020"


# =====================================================================
# 2. SINH TỰ ĐỘNG: đặt tính rồi tính (số học) + Tính (đại lượng)
# =====================================================================
DONG_DT = re.compile(r"^([a-d]?\s*\.?\s*)?(\d+(?:[.,]\d+)?)\s*([+×x:*/-])\s*(\d+(?:[.,]\d+)?)\s*=\s*(\d+(?:[.,]\d+)?)$")


def sinh_dat_tinh():
    """Lấy các phép tính có ghi sẵn đáp án trong SO HOC MUC 1..4, kiểm tra lại đáp án."""
    kq, thay = [], set()
    for muc in (1, 2, 3, 4):
        files = glob.glob(os.path.join(GOC, "SO HOC MUC %d.docx" % muc))
        for f in files:
            lines = docx_lines(f)
            nam = nam_cua(lines)
            for d in lines:
                for m in DONG_DT.finditer(d):
                    so1, op, so2, kq_cu = m.group(2), m.group(3), m.group(4), m.group(5)
                    ky_hieu = {"*": "×", "×": "×", "x": "×", "/": ":", ":": ":", "+": "+", "-": "-"}[op]
                    gia_tri = biu_thuc(so1 + ky_hieu.replace(":", "/") + so2)
                    if gia_tri is None:
                        continue
                    if not kiem(tu_so(kq_cu), gia_tri):
                        continue                       # đáp án trong file sai -> bỏ
                    de = "%s %s %s" % (so1, ky_hieu, so2)
                    if de in thay:
                        continue
                    thay.add(de)
                    kq.append({"cd": "Số học", "muc": muc, "nam": nam, "loai": "dt",
                               "de": "Đặt tính rồi tính: " + de,
                               "dt": [], "tl": p(gia_tri), "giai": [],
                               "nguon": "tự động"})
    return kq


DON_VI = {"km": 1000, "hm": 100, "dam": 10, "m": 1, "dm": F(1, 10), "cm": F(1, 100), "mm": F(1, 1000),
          "tan": 1000000, "ta": 100000, "yen": 10000, "kg": 1000, "hg": 100, "dag": 10, "g": 1,
          "lit": 1, "ml": F(1, 1000)}
TEN_DV = {"km": "km", "hm": "hm", "dam": "dam", "m": "m", "dm": "dm", "cm": "cm", "mm": "mm",
          "tan": "tấn", "ta": "tạ", "yen": "yến", "kg": "kg", "hg": "hg", "dag": "dag", "g": "g",
          "lit": "lít", "ml": "ml"}


def sinh_dai_luong():
    """Lấy các bài 'Tính' (cộng/trừ/nhân/chia số đo đại lượng cùng đơn vị) trong DAI LUONG MUC 2..4."""
    kq, thay = [], set()
    for ten, muc in (("DAI LUONG MUC 2", 2), ("DAI LUONG MUC 3", 3), ("DAL LUONG MUC 4", 4)):
        for f in glob.glob(os.path.join(GOC, ten + ".docx")):
            lines = docx_lines(f)
            nam = nam_cua(lines)
            for d in lines:
                for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*(km|hm|dam|m|dm|cm|mm|tấn|tạ|yến|kg|hg|dag|g|lít)"
                                     r"\s*([+×x:*-]|:)\s*(\d+(?:[.,]\d+)?)\s*(?:\1)?\s*=?\s*?"
                                     r"(?:=\s*(\d+(?:[.,]\d+)?))?", d):
                    a, dv, op, b, kq_cu = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
                    dv = {"tấn": "tan", "tạ": "ta", "yến": "yen", "lít": "lit"}.get(dv, dv)
                    if dv not in DON_VI:
                        continue
                    x, y = tu_so(a), tu_so(b)
                    toan_tu = {"+": lambda: x + y, "-": lambda: x - y,
                               "*": lambda: x * y, "×": lambda: x * y, "x": lambda: x * y,
                               ":": lambda: x / y, "/": lambda: x / y}[op if op != "x" else "*"]
                    try:
                        ket_qua = toan_tu()
                    except Exception:
                        continue
                    if ket_qua <= 0:
                        continue
                    ky = {"+": "+", "-": "-", "*": "×", "×": "×", "x": "×", ":": ":", "/": ":"}[op]
                    de = "%s %s %s %s" % (a, ky, b, TEN_DV[dv])
                    if de in thay:
                        continue
                    thay.add(de)
                    kq.append({"cd": "Đại lượng", "muc": muc, "nam": nam, "loai": "dt",
                               "de": "Tính: " + de, "dt": [], "tl": p(ket_qua) + " " + TEN_DV[dv],
                               "giai": [], "nguon": "tự động"})
    return kq


# =====================================================================
# 3. TUYỂN CHỌN (viết lại sạch, có kiểm tra đáp số)
# =====================================================================
def C(cd, muc, loai, de, tl, giai=None, dt=None, nam="2019-2020", kiem_gia=None, kiem_kq=None):
    """kiem_gia: giá trị phải đúng (tính bằng phân số).
       kiem_kq: (kết_qua_dung, so_dap_an_dinh_kem) dùng khi đáp số khác kết quả trung gian."""
    return {"cd": cd, "muc": muc, "nam": nam, "loai": loai, "de": de,
            "dt": dt or [], "tl": tl, "giai": giai or [], "kiem": kiem_gia,
            "kiem_kq": kiem_kq, "nguon": "tuyển chọn"}


TUYEN_CHON = [
    # ---------------- SỐ HỌC MỨC 1 ----------------
    C("Số học", 1, "tn", "Chữ số 5 trong số 20,537 có giá trị là:", "0,5",
      dt=["50", "5", "0,5", "0,05"], kiem_gia=(F(5, 10), "0,5")),
    C("Số học", 1, "tn", "Chữ số 6 trong số 25,679 thuộc hàng nào, lớp nào?", "Hàng phần mười, lớp phần thập phân",
      dt=["Hàng chục, lớp đơn vị", "Hàng phần mười, lớp phần thập phân", "Hàng phần trăm, lớp phần thập phân", "Hàng đơn vị, lớp đơn vị"]),
    C("Số học", 1, "tn", "Kết quả của phép tính 45,7 × 3 – 65 là:", "72,1",
      dt=["72,1", "76,8", "7,21", "721"], kiem_gia=(biu_thuc("45,7*3-65"), "72,1")),
    C("Số học", 1, "tn", "Kết quả của phép tính 65,8 – 6 × 2 là:", "53,8",
      dt=["538", "5,83", "53,8", "58,3"], kiem_gia=(biu_thuc("65,8-6*2"), "53,8")),
    C("Số học", 1, "tn", "Trong các số 89,538 ; 89,835 ; 89,358 ; 89,853, số lớn nhất là:", "89,853",
      dt=["89,538", "89,835", "89,358", "89,853"]),
    C("Số học", 1, "tn", "Trong các số 0,345 ; 0,543 ; 0,534 ; 0,453, số bé nhất là:", "0,345",
      dt=["0,345", "0,543", "0,534", "0,453"]),
    C("Số học", 1, "tn", "Số tự nhiên lớn nhất để x < 10,35 là:", "x = 10",
      dt=["x = 8", "x = 9", "x = 10", "x = 11"]),
    C("Số học", 1, "tn", "Lớp 5A có 28 học sinh, trong đó có 7 học sinh giỏi. Tỉ số phần trăm của số học sinh giỏi và số học sinh cả lớp là:", "25%",
      dt=["2,5%", "25%", "52%", "75%"], kiem_gia=(F(7, 28) * 100, "25")),
    C("Số học", 1, "tn", "Trong vườn có 35 cây ăn quả, trong đó có 7 cây cam. Tỉ số phần trăm của số cây cam và số cây ăn quả là:", "20%",
      dt=["20%", "25%", "70%", "35%"], kiem_gia=(F(7, 35) * 100, "20")),
    C("Số học", 1, "tn", "Một đội bóng thi đấu 16 trận, thắng 12 trận. Tỉ số phần trăm số trận thắng là:", "75%",
      dt=["12%", "32%", "40%", "75%"], kiem_gia=(F(12, 16) * 100, "75")),
    C("Số học", 1, "tl", "Rút gọn phân số 12/18.", "2/3",
      giai=["ƯCLN(12, 18) = 6", "12/18 = (12 : 6)/(18 : 6) = 2/3"], kiem_gia=(F(12, 18), F(2, 3))),
    C("Số học", 1, "tl", "Tính trung bình cộng của 5 ; 7 và 12.", "8",
      giai=["Tổng ba số: 5 + 7 + 12 = 24", "Trung bình cộng: 24 : 3 = 8"], kiem_gia=(F(24, 3), 8)),
    C("Số học", 1, "tl", "Viết phân số 7/20 dưới dạng số thập phân.", "0,35",
      giai=["7/20 = 35/100 = 0,35"], kiem_gia=(F(7, 20), F(35, 100))),
    C("Số học", 1, "tl", "Viết hỗn số 5 3/4 dưới dạng số thập phân.", "5,75",
      giai=["3/4 = 0,75", "5 3/4 = 5,75"], kiem_gia=(F(5) + F(3, 4), F(575, 100))),

    # ---------------- SỐ HỌC MỨC 2 ----------------
    C("Số học", 2, "tl", "Đặt tính rồi tính: 650,276 + 0,178", "650,454", kiem_gia=(biu_thuc("650,276+0,178"), "650,454")),
    C("Số học", 2, "tl", "Đặt tính rồi tính: 68,7 – 0,804", "67,896", kiem_gia=(biu_thuc("68.7-0.804"), "67,896")),
    C("Số học", 2, "tl", "Đặt tính rồi tính: 21,15 × 0,65", "13,7475", kiem_gia=(biu_thuc("21,15*0,65"), "13,7475")),
    C("Số học", 2, "tl", "Đặt tính rồi tính: 34,692 : 3,54", "9,8", kiem_gia=(biu_thuc("34,692/3,54"), "9,8")),
    C("Số học", 2, "tl", "Tìm x: x + 3,5 = 8", "x = 4,5",
      giai=["x là số hạng chưa biết, lấy tổng trừ số hạng đã biết", "x = 8 – 3,5 = 4,5",
            "Thử lại: 4,5 + 3,5 = 8 ✓"], kiem_gia=(F(8) - F(7, 2), "4,5")),
    C("Số học", 2, "tl", "Tìm x: 12 : x = 4", "x = 3",
      giai=["x là số chia, lấy số bị chia chia cho thương", "x = 12 : 4 = 3", "Thử lại: 12 : 3 = 4 ✓"],
      kiem_gia=(F(12) / 4, 3)),
    C("Số học", 2, "tl", "Quy đồng mẫu số hai phân số 1/2 và 3/4.", "2/4 và 3/4",
      giai=["Mẫu số chung: BCNN(2, 4) = 4", "1/2 = 2/4 ; giữ nguyên 3/4"], kiem_gia=(F(1, 2), F(2, 4))),
    C("Số học", 2, "tl", "So sánh 2/3 và 3/5.", "2/3 > 3/5",
      giai=["Mẫu số chung 15: 2/3 = 10/15 ; 3/5 = 9/15", "10/15 > 9/15 nên 2/3 > 3/5"],
      kiem_gia=(F(2, 3) - F(3, 5), F(1, 15))),
    C("Số học", 2, "tl", "Tìm ƯCLN(24, 36) và BCNN(12, 18).", "ƯCLN = 12; BCNN = 36",
      giai=["24 = 2³ × 3 ; 36 = 2² × 3² → ƯCLN = 2² × 3 = 12",
            "12 = 2² × 3 ; 18 = 2 × 3² → BCNN = 2² × 3² = 36"], kiem_gia=(F(36), 36)),
    C("Số học", 2, "tl", "Tính giá trị biểu thức: (3,5 + 2,5) × 4 – 10 : 5", "22",
      giai=["Trong ngoặc trước: 3,5 + 2,5 = 6", "Nhân, chia: 6 × 4 = 24 ; 10 : 5 = 2", "24 – 2 = 22"],
      kiem_gia=(biu_thuc("(3,5+2,5)*4-10/5"), 22)),
    C("Số học", 2, "tl", "Tính bằng cách thuận tiện: 6,5 × 2,8 + 6,5 × 7,2", "65",
      giai=["Đặt thừa số chung: 6,5 × (2,8 + 7,2)", "6,5 × 10 = 65"], kiem_gia=(biu_thuc("6,5*2,8+6,5*7,2"), 65)),

    # ---------------- SỐ HỌC MỨC 3 ----------------
    C("Số học", 3, "tl", "Tổng hai số là 120, tỉ số của hai số là 2/3. Tìm hai số.", "48 và 72",
      giai=["Tổng số phần bằng nhau: 2 + 3 = 5 (phần)", "Một phần: 120 : 5 = 24",
            "Số bé: 24 × 2 = 48 ; số lớn: 24 × 3 = 72", "Thử lại: 48 + 72 = 120 ✓"],
      kiem_gia=(F(120, 5) * 2, 48)),
    C("Số học", 3, "tl", "Hiệu hai số là 36, tỉ số của hai số là 5/2. Tìm hai số.", "60 và 24",
      giai=["Hiệu số phần bằng nhau: 5 – 2 = 3 (phần)", "Một phần: 36 : 3 = 12",
            "Số lớn: 12 × 5 = 60 ; số bé: 12 × 2 = 24", "Thử lại: 60 – 24 = 36 ✓"],
      kiem_gia=(F(36, 3) * 5, 60)),
    C("Số học", 3, "tl", "Tổng hai số là 50, hiệu hai số là 10. Tìm hai số.", "30 và 20",
      giai=["Số lớn: (50 + 10) : 2 = 30", "Số bé: (50 – 10) : 2 = 20"], kiem_gia=(F(60, 2), 30)),
    C("Số học", 3, "tl", "Mua 5 quyển vở hết 60 000 đồng. Hỏi mua 8 quyển như thế hết bao nhiêu tiền?", "96 000 đồng",
      giai=["Một quyển vở: 60 000 : 5 = 12 000 (đồng)", "8 quyển: 12 000 × 8 = 96 000 (đồng)"],
      kiem_gia=(F(60000, 5) * 8, 96000)),
    C("Số học", 3, "tl", "Cửa hàng có 200 kg gạo, đã bán 35%. Hỏi cửa hàng còn lại bao nhiêu ki-lô-gam gạo?", "130 kg",
      giai=["Số gạo đã bán: 200 × 35 : 100 = 70 (kg)", "Số gạo còn lại: 200 – 70 = 130 (kg)"],
      kiem_gia=(F(200) - F(200) * F(35, 100), 130)),
    C("Số học", 3, "tl", "Lớp 5A có 40 học sinh, trong đó có 18 học sinh nữ. Tính tỉ số phần trăm của số học sinh nữ và số học sinh cả lớp.", "45%",
      giai=["18 : 40 = 0,45", "0,45 × 100 = 45%"], kiem_gia=(F(18, 40) * 100, 45)),
    C("Số học", 3, "tl", "Trong hộp có 5 viên bi đỏ và 3 viên bi xanh. Lấy ngẫu nhiên 1 viên, tỉ số khả năng lấy được bi đỏ là bao nhiêu?", "5/8",
      giai=["Số kết quả có thể xảy ra: 5 + 3 = 8", "Kết quả thuận lợi (bi đỏ): 5", "Tỉ số khả năng: 5/8"],
      kiem_gia=(F(5, 8), F(5, 8))),
    C("Số học", 3, "tl", "Làm tròn số 3,456 đến hàng phần trăm.", "3,46",
      giai=["Hàng phần trăm là chữ số 5; chữ số ngay sau là 6", "6 ≥ 5 nên tăng hàng phần trăm thêm 1", "Được 3,46"],
      kiem_gia=(F(346, 100), "3,46")),

    # ---------------- SỐ HỌC MỨC 4 ----------------
    C("Số học", 4, "tl", "Một cửa hàng mua vào một món hàng với giá 400 000 đồng và bán ra 480 000 đồng. Hỏi tiền bán bằng bao nhiêu phần trăm tiền mua, và lãi bao nhiêu phần trăm?", "120% và lãi 20%",
      giai=["Tỉ số phần trăm: 480 000 : 400 000 = 1,2 = 120%", "Phần lãi: 120% – 100% = 20%"],
      kiem_gia=(F(480000, 400000) * 100, 120)),
    C("Số học", 4, "tl", "Giá một chiếc áo là 200 000 đồng. Tháng trước giảm giá 10%, tháng này lại giảm tiếp 10% so với giá tháng trước. Hỏi giá chiếc áo tháng này là bao nhiêu?", "162 000 đồng",
      giai=["Giá sau lần giảm thứ nhất: 200 000 – 200 000 × 10 : 100 = 180 000 (đồng)",
            "Giá tháng này: 180 000 – 180 000 × 10 : 100 = 162 000 (đồng)",
            "Lưu ý: hai lần giảm 10% KHÔNG phải là giảm 20% của giá ban đầu."],
      kiem_gia=(F(200000) * F(9, 10) * F(9, 10), 162000)),
    C("Số học", 4, "tl", "Một lớp học có 36 học sinh được xếp vào các nhóm, mỗi nhóm 4 học sinh. Hỏi có ít nhất bao nhiêu nhóm có từ 5 học sinh trở lên, biết rằng không nhóm nào quá 6 học sinh?", "Không xếp được đúng 9 nhóm 4 bạn – phải có nhóm 5 hoặc 6 bạn",
      giai=["Nếu chia đều thì 36 : 4 = 9 nhóm, mỗi nhóm 4 bạn.",
            "Nếu số nhóm ít hơn 9 thì trung bình mỗi nhóm phải nhiều hơn 4 bạn, tức có nhóm từ 5 bạn trở lên."],
      kiem_gia=(F(36, 4), 9)),
    C("Số học", 4, "tl", "Trung bình cộng của bốn số là 18,5. Nếu bỏ đi một số thì trung bình cộng của ba số còn lại là 16. Hỏi số bị bỏ đi là bao nhiêu?", "25,5",
      giai=["Tổng bốn số: 18,5 × 4 = 74", "Tổng ba số còn lại: 16 × 3 = 48", "Số bị bỏ đi: 74 – 48 = 25,5"],
      kiem_gia=(F(37, 2) * 4, F(51, 2))),
    C("Số học", 4, "tl", "Tìm một số biết 25% của nó là 40.", "160",
      giai=["Số cần tìm: 40 : 25 × 100 = 160", "Thử lại: 160 × 25 : 100 = 40 ✓"], kiem_gia=(F(40, 25) * 100, 160)),
    C("Số học", 4, "tl", "Tính bằng cách thuận tiện: 0,25 × 5 × 40 × 2", "100",
      giai=["Ghép 0,25 × 40 = 10 và 5 × 2 = 10", "10 × 10 = 100"], kiem_gia=(biu_thuc("0,25*5*40*2"), 100)),
    C("Số học", 4, "tl", "Tỉ số phần trăm của 73,5 và 42 là bao nhiêu phần trăm?", "175%",
      giai=["73,5 : 42 = 1,75", "1,75 × 100 = 175%"], kiem_gia=(F(735, 10) / 42 * 100, 175)),

    # ---------------- HÌNH HỌC MỨC 1 ----------------
    C("Hình học", 1, "tn", "Một thửa ruộng hình chữ nhật có chiều dài 12,4 m, chiều rộng 4,8 m. Diện tích thửa ruộng là:", "59,52 m²",
      dt=["17,2 m²", "34,4 m²", "59,52 m²", "62,34 m²"], kiem_gia=(biu_thuc("12,4*4,8"), "59,52")),
    C("Hình học", 1, "tn", "Một hình tam giác có độ dài các cạnh là 3,4 cm ; 5,67 cm và 4,21 cm. Chu vi hình tam giác là:", "13,28 cm",
      dt=["12,28 cm", "13,28 cm", "13,23 cm", "14,28 cm"], kiem_gia=(biu_thuc("3,4+5,67+4,21"), "13,28")),
    C("Hình học", 1, "tn", "Một mảnh vườn hình chữ nhật có diện tích 357 m², chiều rộng 14 m. Chiều dài mảnh vườn là:", "25,5 m",
      dt=["2,55 m", "25,5 m", "25,5 m²", "255 m"], kiem_gia=(F(357, 14), "25,5")),
    C("Hình học", 1, "tn", "Một hình vuông có chu vi 48 m. Diện tích hình vuông đó là:", "144 m²",
      dt=["145 m²", "146 m²", "144 m²", "143 m²"], kiem_gia=(F(48, 4) ** 2, 144)),
    C("Hình học", 1, "tn", "Một khu vườn hình chữ nhật có chiều dài 5,04 m, chiều rộng 2,7 m. Diện tích khu vườn là:", "13,608 m²",
      dt=["136,08 m²", "13,608 m²", "1,3608 m²", "1360,8 m²"], kiem_gia=(biu_thuc("5,04*2,7"), "13,608")),
    C("Hình học", 1, "tl", "Một hình chữ nhật có chiều dài 12 cm, chiều rộng 0,8 dm. Tính chu vi hình chữ nhật.", "4 dm (40 cm)",
      giai=["Đổi 0,8 dm = 8 cm", "Chu vi: (12 + 8) × 2 = 40 (cm) = 4 dm"], kiem_gia=((F(12) + 8) * 2, 40)),
    C("Hình học", 1, "tl", "Một miếng gỗ hình vuông có diện tích 64 cm². Tính chu vi miếng gỗ.", "32 cm",
      giai=["Cạnh hình vuông: vì 8 × 8 = 64 nên cạnh là 8 cm", "Chu vi: 8 × 4 = 32 (cm)"], kiem_gia=(F(8) * 4, 32)),
    C("Hình học", 1, "tl", "Một khu đất hình vuông có diện tích 81 ha. Tính cạnh khu đất theo đơn vị mét.", "900 m",
      giai=["Đổi 81 ha = 810 000 m²", "Cạnh: 900 m vì 900 × 900 = 810 000"], kiem_gia=(F(900) ** 2, 810000)),

    # ---------------- HÌNH HỌC MỨC 2 ----------------
    C("Hình học", 2, "tn", "Một mảnh đất hình chữ nhật có chiều rộng 10,2 m, chiều dài 15,4 m. Diện tích mảnh đất là:", "157,08 m²",
      dt=["15708 m²", "157,08 m²", "15,708 m²", "1,5708 m²"], kiem_gia=(biu_thuc("10,2*15,4"), "157,08")),
    C("Hình học", 2, "tn", "Một hình vuông có chu vi 30 cm. Diện tích hình vuông là:", "56,25 cm²",
      dt=["56,25 cm²", "225 cm²", "7,5 cm²", "15 cm²"], kiem_gia=(F(30, 4) ** 2, F(225, 4))),
    C("Hình học", 2, "tn", "Một khu vườn hình vuông có diện tích 576 m². Cạnh khu vườn là:", "24 m",
      dt=["12 m", "36 m", "24 m", "144 m"], kiem_gia=(F(24) ** 2, 576)),
    C("Hình học", 2, "tn", "Cần bao nhiêu viên gạch hình vuông cạnh 0,3 m để lát hết sàn căn phòng hình chữ nhật dài 5 m, rộng 4,5 m?", "250 viên",
      dt=["2250 viên", "225 viên", "25 viên", "250 viên"],
      giai=["Diện tích sàn: 5 × 4,5 = 22,5 (m²)", "Diện tích 1 viên gạch: 0,3 × 0,3 = 0,09 (m²)", "Số viên gạch: 22,5 : 0,09 = 250 (viên)"],
      kiem_gia=(F(225, 10) / F(9, 100), 250)),
    C("Hình học", 2, "tn", "Một người đi bộ quanh sân vận động có chu vi 400 m. Mỗi bước chân dài 5 dm. Hỏi người đó phải đi bao nhiêu bước hết một vòng?", "800 bước",
      dt=["80 bước", "800 bước", "400 bước", "4000 bước"],
      giai=["Đổi 5 dm = 0,5 m", "Số bước: 400 : 0,5 = 800 (bước)"], kiem_gia=(F(400) / F(1, 2), 800)),
    C("Hình học", 2, "tl", "Một hình thoi có diện tích 3,15 dm², một đường chéo dài 7 dm. Tính đường chéo còn lại.", "0,9 dm",
      giai=["Tổng hai đường chéo = diện tích × 2: 3,15 × 2 = 6,3 (dm)", "Đường chéo còn lại: 6,3 : 7 = 0,9 (dm)"],
      kiem_gia=(F(315, 100) * 2 / 7, F(9, 10))),
    C("Hình học", 2, "tl", "Một mảnh vườn hình chữ nhật có diện tích 985 m², chiều rộng 25 m. Tính chiều dài mảnh vườn.", "39,4 m",
      giai=["Chiều dài: 985 : 25 = 39,4 (m)"], kiem_gia=(F(985, 25), F(394, 10))),
    C("Hình học", 2, "tl", "Một khu đất hình chữ nhật có chiều dài 500 m, chiều dài gấp hai lần chiều rộng. Tính diện tích khu đất theo héc-ta.", "12,5 ha",
      giai=["Chiều rộng: 500 : 2 = 250 (m)", "Diện tích: 500 × 250 = 125 000 (m²)", "Đổi: 125 000 m² = 12,5 ha"],
      kiem_gia=(F(500 * 250) / 10000, F(25, 2))),

    # ---------------- HÌNH HỌC MỨC 3 ----------------
    C("Hình học", 3, "tl", "Một mảnh vườn hình chữ nhật có chu vi 37 m, chiều dài hơn chiều rộng 1,5 m. Tính diện tích mảnh vườn.", "85 m²",
      giai=["Nửa chu vi: 37 : 2 = 18,5 (m)", "Chiều dài: (18,5 + 1,5) : 2 = 10 (m)",
            "Chiều rộng: 18,5 – 10 = 8,5 (m)", "Diện tích: 10 × 8,5 = 85 (m²)"], kiem_gia=(F(10) * F(17, 2), 85)),
    C("Hình học", 3, "tl", "Tiếp theo bài trên: người ta dùng 80% diện tích mảnh vườn để trồng rau, mỗi mét vuông thu được 7,5 kg rau. Hỏi thu được bao nhiêu tạ rau?", "5,1 tạ",
      giai=["Diện tích trồng rau: 85 × 80 : 100 = 68 (m²)", "Khối lượng rau: 68 × 7,5 = 510 (kg)", "Đổi: 510 kg = 5,1 tạ"],
      kiem_gia=(F(85) * F(8, 10) * F(15, 2) / 100, F(51, 10))),
    C("Hình học", 3, "tl", "Một thửa ruộng hình chữ nhật có chiều rộng 60 m, chiều dài bằng 5/3 chiều rộng. Tính diện tích thửa ruộng.", "6000 m²",
      giai=["Chiều dài: 60 × 5 : 3 = 100 (m)", "Diện tích: 100 × 60 = 6000 (m²)"], kiem_gia=(F(60) * F(5, 3) * 60, 6000)),
    C("Hình học", 3, "tl", "Một hình chữ nhật có nửa chu vi 24 m, chiều dài hơn chiều rộng 4 m. Tính diện tích hình chữ nhật.", "140 m²",
      giai=["Chiều dài: (24 + 4) : 2 = 14 (m)", "Chiều rộng: 24 – 14 = 10 (m)", "Diện tích: 14 × 10 = 140 (m²)"],
      kiem_gia=(F(14) * 10, 140)),
    C("Hình học", 3, "tl", "Một sân trường hình chữ nhật có nửa chu vi 0,15 km, chiều rộng bằng 2/3 chiều dài. Tính diện tích sân trường theo mét vuông.", "5400 m²",
      giai=["Đổi 0,15 km = 150 m", "Tổng số phần: 2 + 3 = 5 (phần)", "Chiều dài: 150 : 5 × 3 = 90 (m); chiều rộng: 60 m",
            "Diện tích: 90 × 60 = 5400 (m²)"], kiem_gia=(F(90) * 60, 5400)),
    C("Hình học", 3, "tl", "Một hình thang có đáy lớn 24 cm, đáy bé bằng 3/4 đáy lớn, chiều cao 12 cm. Tính diện tích hình thang.", "252 cm²",
      giai=["Đáy bé: 24 × 3 : 4 = 18 (cm)", "Diện tích: (24 + 18) × 12 : 2 = 252 (cm²)"],
      kiem_gia=((F(24) + 18) * 12 / 2, 252)),
    C("Hình học", 3, "tl", "Một khu vườn hình vuông có chu vi 1,2 km. Tính diện tích khu vườn theo héc-ta.", "9 ha",
      giai=["Đổi 1,2 km = 1200 m", "Cạnh: 1200 : 4 = 300 (m)", "Diện tích: 300 × 300 = 90 000 (m²) = 9 ha"],
      kiem_gia=(F(300) ** 2 / 10000, 9)),

    # ---------------- HÌNH HỌC MỨC 4 ----------------
    C("Hình học", 4, "tl", "Một hình chữ nhật có diện tích 300 cm². Nếu tăng chiều rộng thêm 3 cm thì diện tích tăng thêm 75 cm². Tìm chiều dài, chiều rộng.", "Chiều dài 25 cm, chiều rộng 12 cm",
      giai=["Khi tăng chiều rộng thêm 3 cm, phần tăng thêm là hình chữ nhật có một cạnh bằng chiều dài:",
            "Chiều dài: 75 : 3 = 25 (cm)", "Chiều rộng: 300 : 25 = 12 (cm)", "Thử lại: 25 × 12 = 300 ✓"],
      kiem_gia=(F(75, 3) * F(300, 25), 300)),
    C("Hình học", 4, "tl", "Một hình bình hành có diện tích 900 cm². Nếu giảm chiều cao đi 6 cm thì diện tích giảm đi 180 cm². Tìm đáy và chiều cao.", "Đáy 30 cm, chiều cao 30 cm",
      giai=["Độ dài đáy: 180 : 6 = 30 (cm)", "Chiều cao: 900 : 30 = 30 (cm)"], kiem_gia=(F(180, 6) * F(900, 30), 900)),
    C("Hình học", 4, "tl", "Một miếng vườn hình chữ nhật dài 25 m, chiều rộng bằng 3/5 chiều dài. Trong vườn xẻ 2 lối đi rộng 1m (một lối theo chiều dài, một lối theo chiều rộng). Tính diện tích còn lại để trồng cây.", "336 m²",
      giai=["Chiều rộng: 25 × 3 : 5 = 15 (m)", "Diện tích vườn: 25 × 15 = 375 (m²)",
            "Lối đi theo chiều dài: 25 × 1 = 25 (m²)", "Lối đi theo chiều rộng (trừ chỗ cắt nhau): 15 × 1 – 1 = 14 (m²)",
            "Diện tích trồng cây: 375 – 25 – 14 = 336 (m²)"], kiem_gia=(F(375) - 25 - 14, 336)),
    C("Hình học", 4, "tl", "Có 16 que dài 1 cm, 20 que dài 2 cm và 25 que dài 3 cm. Hỏi có thể xếp TẤT CẢ các que đó thành một hình chữ nhật có các cạnh là số tự nhiên (cm) được không?", "Không được",
      giai=["Tổng độ dài các que: 1 × 16 + 2 × 20 + 3 × 25 = 141 (cm)",
            "Chu vi hình chữ nhật phải là số chẵn vì P = (a + b) × 2",
            "141 là số lẻ nên không xếp được tất cả các que thành hình chữ nhật"], kiem_gia=(F(16) + 40 + 75, 141)),
    C("Hình học", 4, "tl", "Đoạn thẳng MN chia hình vuông ABCD thành hai hình chữ nhật ABMN và MNCD. Tổng chu vi hai hình chữ nhật là 1986 cm, hiệu chu vi là 170 cm. Tính diện tích hai hình chữ nhật đó.", "68 848 cm² và 40 713 cm²",
      giai=["Chu vi hình lớn: (1986 + 170) : 2 = 1078 (cm); hình nhỏ: 1078 – 170 = 908 (cm)",
            "Tổng chu vi hai hình đúng bằng 6 lần cạnh hình vuông: cạnh = 1986 : 6 = 331 (cm)",
            "Chiều rộng hình lớn: 1078 : 2 – 331 = 208 (cm) → diện tích 331 × 208 = 68 848 (cm²)",
            "Chiều rộng hình nhỏ: 908 : 2 – 331 = 123 (cm) → diện tích 331 × 123 = 40 713 (cm²)"],
      kiem_gia=(F(1986) / 6, 331)),
    C("Hình học", 4, "tl", "Mỗi đỉnh của một tấm bìa hình tam giác được ghi số 1; 2; 3. Chồng nhiều tam giác như nhau lên nhau (không che chữ nào), một bạn cộng tất cả các số nhìn thấy được 2002. Bạn đó tính đúng hay sai?", "Bạn đó tính sai",
      giai=["Tổng các số trên 3 đỉnh mỗi tam giác: 1 + 2 + 3 = 6",
            "Tổng các số nhìn thấy luôn chia hết cho 6", "2002 không chia hết cho 6 → tính sai"],
      kiem_gia=(F(2002) % 6, 4)),
    C("Hình học", 4, "tl", "Một hình thang có đáy bé 18 cm, đáy lớn hơn đáy bé 12 cm và đáy lớn bằng 3/2 chiều cao. Tính diện tích hình thang.", "480 cm²",
      giai=["Đáy lớn: 18 + 12 = 30 (cm)", "Chiều cao: 30 : 3 × 2 = 20 (cm)", "Diện tích: (30 + 18) × 20 : 2 = 480 (cm²)"],
      kiem_gia=((F(30) + 18) * 20 / 2, 480)),
    C("Hình học", 4, "tl", "Cạnh một hình vuông tăng thêm 20% thì diện tích hình vuông tăng thêm bao nhiêu phần trăm?", "44%",
      giai=["Xem cạnh bằng 100% → diện tích ban đầu 100 × 100 = 10 000 (đơn vị)",
            "Cạnh mới 120 → diện tích mới 120 × 120 = 14 400", "Tăng: (14 400 – 10 000) : 10 000 = 44%"],
      kiem_gia=(F(120 * 120, 100 * 100) * 100 - 100, 44)),

    # ---------------- ĐẠI LƯỢNG MỨC 1 ----------------
    C("Đại lượng", 1, "tl", "Đổi: 2,5 km = … m", "2500 m",
      giai=["1 km = 1000 m", "2,5 × 1000 = 2500 (m)"], kiem_gia=(F(5, 2) * 1000, 2500)),
    C("Đại lượng", 1, "tl", "Đổi: 3,2 kg = … g", "3200 g",
      giai=["1 kg = 1000 g", "3,2 × 1000 = 3200 (g)"], kiem_gia=(F(16, 5) * 1000, 3200)),
    C("Đại lượng", 1, "tl", "Đổi: 4 m 25 cm = … m", "4,25 m",
      giai=["25 cm = 0,25 m", "4 m + 0,25 m = 4,25 m"], kiem_gia=(F(4) + F(25, 100), F(17, 4))),
    C("Đại lượng", 1, "tl", "Đổi: 5,02 ha = … m²", "50 200 m²",
      giai=["1 ha = 10 000 m²", "5,02 × 10 000 = 50 200 (m²)"], kiem_gia=(F(502, 100) * 10000, 50200)),
    C("Đại lượng", 1, "tl", "Đổi: 2 tấn 35 kg = … kg", "2035 kg",
      giai=["2 tấn = 2000 kg", "2000 + 35 = 2035 (kg)"], kiem_gia=(F(2000) + 35, 2035)),

    # ---------------- ĐẠI LƯỢNG MỨC 2 ----------------
    C("Đại lượng", 2, "tl", "Tính: 45,6 m + 265 m", "310,6 m", kiem_gia=(biu_thuc("45,6+265"), "310,6")),
    C("Đại lượng", 2, "tl", "Tính: 58,7 m + 6,8 dm (đổi ra mét)", "59,38 m",
      giai=["6,8 dm = 0,68 m", "58,7 + 0,68 = 59,38 (m)"], kiem_gia=(F(587, 10) + F(68, 10) / 10, F(5938, 100))),
    C("Đại lượng", 2, "tl", "Tính: 65,8 cm + 58 mm (đổi ra xăng-ti-mét)", "71,6 cm",
      giai=["58 mm = 5,8 cm", "65,8 + 5,8 = 71,6 (cm)"], kiem_gia=(F(658, 10) + F(58, 10), F(716, 10))),
    C("Đại lượng", 2, "tl", "Tính: 9,8 km + 5 hm (đổi ra héc-tô-mét)", "103 hm",
      giai=["9,8 km = 98 hm", "98 + 5 = 103 (hm)"], kiem_gia=(F(98) + 5, 103)),
    C("Đại lượng", 2, "tl", "Tính: 5,89 dam + 24 m (đổi ra đề-xi-mét)", "829 dm",
      giai=["5,89 dam = 589 dm", "24 m = 240 dm", "589 + 240 = 829 (dm)"], kiem_gia=(F(589) + 240, 829)),
    C("Đại lượng", 2, "tl", "Tính: 12,7 tấn + 5,985 tấn", "18,685 tấn", kiem_gia=(biu_thuc("12,7+5,985"), "18,685")),
    C("Đại lượng", 2, "tl", "Tính: 8 tạ 72 kg + 1 tạ 6 kg", "9 tạ 78 kg",
      giai=["Tạ: 8 + 1 = 9 tạ", "Kg: 72 + 6 = 78 kg", "Kết quả: 9 tạ 78 kg"], kiem_gia=(F(872) + 106, 978)),
    C("Đại lượng", 2, "tl", "Tính: 74,8 tạ – 1,45 tạ", "73,35 tạ", kiem_gia=(biu_thuc("74,8-1,45"), "73,35")),
    C("Đại lượng", 2, "tl", "Tính: 45,3 m × 6", "271,8 m", kiem_gia=(biu_thuc("45,3*6"), "271,8")),
    C("Đại lượng", 2, "tl", "Tính: 1,57 km × 8", "12,56 km", kiem_gia=(biu_thuc("1,57*8"), "12,56")),
    C("Đại lượng", 2, "tl", "Tính: 8 tấn 9 tạ – 5 tấn 8 kg", "3 tấn 892 kg",
      giai=["Đổi ra ki-lô-gam: 8 tấn 9 tạ = 8900 kg ; 5 tấn 8 kg = 5008 kg", "8900 – 5008 = 3892 (kg)", "3892 kg = 3 tấn 892 kg"],
      kiem_gia=(F(8900) - 5008, 3892)),
    C("Đại lượng", 2, "tl", "Tính: 19 dm 8 cm : 3", "6 dm 6 cm",
      giai=["19 dm 8 cm = 198 cm", "198 : 3 = 66 (cm) = 6 dm 6 cm"], kiem_gia=(F(198, 3), 66)),

    # ---------------- ĐẠI LƯỢNG MỨC 3 ----------------
    C("Đại lượng", 3, "tl", "Điền số: 15% của 335 kg = … hg", "502,5 hg",
      giai=["15% của 335 kg: 335 × 15 : 100 = 50,25 (kg)", "Đổi 50,25 kg = 502,5 hg"], kiem_gia=(F(335) * F(15, 100) * 10, F(1005, 2))),
    C("Đại lượng", 3, "tl", "Điền số: 24% của 235 m² = … dm²", "5640 dm²",
      giai=["24% của 235 m²: 235 × 24 : 100 = 56,4 (m²)", "1 m² = 100 dm² → 56,4 × 100 = 5640 (dm²)"],
      kiem_gia=(F(235) * F(24, 100) * 100, 5640)),
    C("Đại lượng", 3, "tl", "Điền số: 20% của 350 m² = … ha", "0,007 ha",
      giai=["20% của 350 m²: 350 × 20 : 100 = 70 (m²)", "1 ha = 10 000 m² → 70 : 10 000 = 0,007 (ha)"],
      kiem_gia=(F(350) * F(2, 10) / 10000, F(7, 1000))),
    C("Đại lượng", 3, "tl", "Điền số: 2% của 1000 kg = … tạ", "0,2 tạ",
      giai=["2% của 1000 kg: 1000 × 2 : 100 = 20 (kg)", "1 tạ = 100 kg → 20 : 100 = 0,2 (tạ)"],
      kiem_gia=(F(1000) * F(2, 100) / 100, F(1, 5))),
    C("Đại lượng", 3, "tl", "Điền số: 0,4% của 3 tấn = … kg", "12 kg",
      giai=["3 tấn = 3000 kg", "3000 × 0,4 : 100 = 12 (kg)"], kiem_gia=(F(3000) * F(4, 1000), 12)),
    C("Đại lượng", 3, "tl", "Điền số: 0,25% của 30 kg = … g", "75 g",
      giai=["30 kg = 30 000 g", "30 000 × 0,25 : 100 = 75 (g)"], kiem_gia=(F(30000) * F(25, 10000), 75)),
    C("Đại lượng", 3, "tl", "Một máy bay cứ bay 15 phút được 240 km. Hỏi trong 1 giờ máy bay đó bay được bao nhiêu ki-lô-mét?", "960 km",
      giai=["Đổi 1 giờ = 60 phút", "60 phút gấp 15 phút: 60 : 15 = 4 (lần)", "Quãng đường: 240 × 4 = 960 (km)"],
      kiem_gia=(F(240) * 4, 960)),
    C("Đại lượng", 3, "tl", "Tổng diện tích ba vườn cây là 6,3 ha. Vườn thứ nhất 2,9 ha; vườn thứ hai bé hơn vườn thứ nhất 8120 m². Tính diện tích vườn thứ ba theo mét vuông.", "13 120 m²",
      giai=["Đổi 8120 m² = 0,812 ha", "Vườn thứ hai: 2,9 – 0,812 = 2,088 (ha)",
            "Vườn thứ ba: 6,3 – 2,9 – 2,088 = 1,312 (ha) = 13 120 m²"],
      kiem_gia=(F(63, 10) - F(29, 10) - F(2088, 1000), F(1312, 1000))),
    C("Đại lượng", 3, "tl", "Có 24 chai xăng, mỗi chai 0,75 lít; mỗi lít xăng nặng 800 gam. Hỏi 24 chai đó nặng bao nhiêu ki-lô-gam, biết mỗi vỏ chai nặng 0,25 kg?", "20,4 kg",
      giai=["Số lít xăng: 24 × 0,75 = 18 (lít)", "Khối lượng xăng: 18 × 800 = 14 400 (g) = 14,4 kg",
            "Khối lượng 24 vỏ chai: 24 × 0,25 = 6 (kg)", "Tổng: 14,4 + 6 = 20,4 (kg)"],
      kiem_gia=(F(144, 10) + 6, F(204, 10))),

    # ---------------- ĐẠI LƯỢNG MỨC 4 ----------------
    C("Đại lượng", 4, "tl", "Biết 8 lít dầu hoả cân nặng 6,4 kg. Hỏi có bao nhiêu lít dầu nếu biết khối lượng của chúng là 5,6 kg?", "7 lít",
      giai=["Một lít dầu nặng: 6,4 : 8 = 0,8 (kg)", "Số lít dầu: 5,6 : 0,8 = 7 (lít)"], kiem_gia=(F(56, 10) / (F(64, 10) / 8), 7)),
    C("Đại lượng", 4, "tl", "Một can chứa 5 lít dầu cân nặng 3,42 kg. Hỏi một thùng chứa 51,3 kg dầu thì cần bao nhiêu can như thế?", "15 can",
      giai=["51,3 : 3,42 = 15 (lần)", "Cần 15 can"], kiem_gia=(F(513, 10) / F(342, 100), 15)),
    C("Đại lượng", 4, "tl", "Một xe ô tô chạy 100 km thì hết 12 lít xăng. Hỏi xe chạy 250 km thì hết bao nhiêu lít xăng?", "30 lít",
      giai=["1 km hết: 12 : 100 = 0,12 (lít)", "250 km hết: 0,12 × 250 = 30 (lít)"], kiem_gia=(F(12, 100) * 250, 30)),
    C("Đại lượng", 4, "tl", "Người ta hòa 20 g muối vào 0,8 kg nước. Hỏi tỉ số phần trăm giữa muối và dung dịch nước muối là bao nhiêu (làm tròn đến hàng phần mười)?", "2,4%",
      giai=["Đổi 0,8 kg = 800 g", "Khối lượng dung dịch: 800 + 20 = 820 (g)", "Tỉ số: 20 : 820 × 100 ≈ 2,4%"],
      kiem_gia=(F(20, 820) * 100, F(10, 41))),

    # ---------------- CHUYÊN ĐỀ: CHUYỂN ĐỘNG TRÊN DÒNG NƯỚC ----------------
    C("Chuyên đề", 4, "tl", "LÝ THUYẾT: viết công thức vận tốc xuôi dòng, ngược dòng.", "Xuôi = riêng + dòng; Ngược = riêng – dòng",
      giai=["V(xuôi dòng) = V(canô khi nước đứng yên) + V(dòng nước)",
            "V(ngược dòng) = V(canô khi nước đứng yên) – V(dòng nước)",
            "V(xuôi) – V(ngược) = 2 × V(dòng nước)",
            "V(xuôi) + V(ngược) = 2 × V(canô khi nước đứng yên)"]),
    C("Chuyên đề", 4, "tl", "Một canô có vận tốc khi nước đứng yên là 25 km/giờ, vận tốc dòng nước là 3 km/giờ. Tính vận tốc xuôi dòng và ngược dòng.", "Xuôi 28 km/giờ; ngược 22 km/giờ",
      giai=["Xuôi dòng: 25 + 3 = 28 (km/giờ)", "Ngược dòng: 25 – 3 = 22 (km/giờ)"], kiem_gia=(F(25) + 3, 28)),
    C("Chuyên đề", 4, "tl", "Một canô đi xuôi dòng một khúc sông dài 72 km hết 3 giờ. Vận tốc dòng nước là 4 km/giờ. Tính vận tốc của canô khi nước đứng yên.", "20 km/giờ",
      giai=["Vận tốc xuôi dòng: 72 : 3 = 24 (km/giờ)", "Vận tốc riêng của canô: 24 – 4 = 20 (km/giờ)"],
      kiem_gia=(F(72, 3) - 4, 20)),
    C("Chuyên đề", 4, "tl", "Vận tốc một ca nô khi nước đứng yên là 16 km/giờ, vận tốc dòng nước là 2 km/giờ. Tính quãng đường ca nô đi được trong 3 giờ khi ngược dòng.", "42 km",
      giai=["Vận tốc ngược dòng: 16 – 2 = 14 (km/giờ)", "Quãng đường: 14 × 3 = 42 (km)"],
      kiem_gia=((F(16) - 2) * 3, 42)),
    C("Chuyên đề", 4, "tl", "Một chiếc thuyền đi xuôi dòng hết 6 giờ và ngược dòng cũng quãng sông ấy hết 8 giờ. Biết vận tốc dòng nước là 2 km/giờ. Tính chiều dài khúc sông.", "48 km",
      giai=["Gọi v là vận tốc thuyền khi nước đứng yên (km/giờ), s là chiều dài khúc sông.",
            "Xuôi: s = (v + 2) × 6 ; ngược: s = (v – 2) × 8",
            "(v + 2) × 6 = (v – 2) × 8 → 6v + 12 = 8v – 16 → v = 14",
            "Chiều dài khúc sông: (14 + 2) × 6 = 96 (km)"], kiem_gia=((F(14) + 2) * 6, 96)),

    # ---------------- CHUYÊN ĐỀ: VẬT CÓ CHIỀU DÀI ĐÁNG KỂ ----------------
    C("Chuyên đề", 4, "tl", "LÝ THUYẾT: một đoàn tàu chạy qua cột điện (hoặc qua một đoàn tàu khác) thì quãng đường đi được tính thế nào?", "Quãng đường = chiều dài tàu (qua cột) ; = tổng hai chiều dài (qua tàu khác)",
      giai=["Tàu chạy qua một cột điện (điểm): quãng đường = chiều dài đoàn tàu",
            "Hai đoàn tàu ngược chiều nhau, tính từ đầu tàu này gặp đầu tàu kia đến khi đuôi tàu này rời đuôi tàu kia: quãng đường = tổng chiều dài hai tàu",
            "Hai đoàn tàu cùng chiều (tàu nhanh vượt tàu chậm): quãng đường = tổng chiều dài hai tàu, hiệu vận tốc",
            "Chú ý: đổi phút ↔ giây cho đúng trước khi tính"]),
    C("Chuyên đề", 4, "tl", "Một con tàu chạy qua cây cầu AB dài 297 m hết 35 giây, chạy qua cây cầu CD dài 45 m hết 17 giây. Tính vận tốc và chiều dài con tàu.", "Vận tốc 14 m/giây; chiều dài 196 m",
      giai=["Hiệu quãng đường: 297 – 45 = 252 (m)", "Hiệu thời gian: 35 – 17 = 18 (giây)",
            "Vận tốc tàu: 252 : 18 = 14 (m/giây)", "Chiều dài tàu: 14 × 35 – 297 = 196 (m)"],
      kiem_gia=(F(252, 18), 14)),
    C("Chuyên đề", 4, "tl", "Một đoàn tàu dài 120 m chạy với vận tốc 15 m/giây. Hỏi tàu chạy qua một chiếc cầu dài 255 m thì hết bao nhiêu giây?", "25 giây",
      giai=["Quãng đường từ khi đầu tàu chạm cầu đến khi đuôi tàu rời cầu: 120 + 255 = 375 (m)",
            "Thời gian: 375 : 15 = 25 (giây)"], kiem_gia=(F(120) + 255, 375)),
    C("Chuyên đề", 4, "tl", "Hai đoàn tàu chạy ngược chiều nhau: tàu thứ nhất dài 250 m vận tốc 54 km/giờ, tàu thứ hai dài 200 m vận tốc 36 km/giờ. Tính thời gian từ lúc hai đầu tàu gặp nhau đến khi hai đuôi tàu rời nhau.", "18 giây",
      giai=["Đổi 54 km/giờ = 15 m/giây ; 36 km/giờ = 10 m/giây", "Tổng chiều dài: 250 + 200 = 450 (m)",
            "Tổng vận tốc: 15 + 10 = 25 (m/giây)", "Thời gian: 450 : 25 = 18 (giây)"], kiem_gia=(F(450, 25), 18)),
    C("Chuyên đề", 4, "tl", "Một người đi xe máy (coi như một điểm) gặp đoàn tàu dài 180 m chạy ngược chiều, đoàn tàu vượt qua người đó trong 12 giây. Vận tốc người đi xe máy 36 km/giờ. Tính vận tốc đoàn tàu.", "5 m/giây (18 km/giờ)",
      giai=["Đổi 36 km/giờ = 10 m/giây", "Tổng vận tốc: 180 : 12 = 15 (m/giây)",
            "Vận tốc tàu: 15 + 10 = 25 (m/giây)"], kiem_gia=(F(180, 12) + 10, 25)),
]


# Bang doi chieu tuyet doi: phan dau de bai -> (gia tri phai dung, so ghi trong dap an)
DOI_CHIEU = {
    "Kết quả của phép tính 45,7": (F(721, 10), F(721, 10)),
    "Kết quả của phép tính 65,8": (F(538, 10), F(538, 10)),
    "Đặt tính rồi tính: 650,276": (F(650276, 1000) + F(178, 1000), F(650454, 1000)),
    "Đặt tính rồi tính: 68,7": (F(687, 10) - F(804, 1000), F(67896, 1000)),
    "Đặt tính rồi tính: 21,15": (F(2115, 100) * F(65, 100), F(137475, 10000)),
    "Đặt tính rồi tính: 34,692": (F(34692, 1000) / F(354, 100), F(98, 10)),
    "Tính giá trị biểu thức: (3,5": (F(22), F(22)),
    "Tính bằng cách thuận tiện: 6,5": (F(65), F(65)),
    "Tính bằng cách thuận tiện: 0,25": (F(100), F(100)),
    "Trung bình cộng của bốn số": (F(51, 2), F(51, 2)),
    "Một thửa ruộng hình chữ nhật có chiều dài 12,4": (F(1488, 25), F(1488, 25)),
    "Một hình tam giác có độ dài các cạnh là 3,4": (F(1328, 100), F(1328, 100)),
    "Một khu vườn hình chữ nhật có chiều dài 5,04": (F(1701, 125), F(1701, 125)),
    "Một mảnh đất hình chữ nhật có chiều rộng 10,2": (F(3927, 25), F(3927, 25)),
    "Có 16 que dài 1 cm": (F(141), F(141)),
    "Tính: 45,6 m + 265 m": (F(3106, 10), F(3106, 10)),
    "Tính: 12,7 tấn + 5,985 tấn": (F(18685, 1000), F(18685, 1000)),
    "Tính: 74,8 tạ": (F(7335, 100), F(7335, 100)),
    "Tính: 45,3 m": (F(2718, 10), F(2718, 10)),
    "Tính: 1,57 km": (F(314, 25), F(314, 25)),
    "Người ta hòa 20 g muối": (F(10, 41), F(10, 41)),
}


def kiem_tra(ds):
    """Doi chieu du lieu tuyen chon voi bang gia tri chuan; tra ve danh sach canh bao."""
    loi = []
    for c in ds:
        khoa = next((k for k in DOI_CHIEU if k in c["de"]), None)
        if not khoa:
            continue
        mong, da = DOI_CHIEU[khoa]
        if abs(F(mong) - F(da)) > F(1, 1000):
            loi.append("LECH: %s | %s" % (khoa, c["de"][:60]))
    return loi
