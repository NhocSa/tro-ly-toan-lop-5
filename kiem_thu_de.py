# -*- coding: utf-8 -*-
"""Kiem thu nhanh trang de-thi.html: du lieu nhúng vao hop le, du cau, khong loi cú phap."""
import io, json, os, re, subprocess, sys

GOC = os.path.dirname(os.path.abspath(__file__))
html = io.open(os.path.join(GOC, "static", "de-thi.html"), encoding="utf-8").read()
m = re.search(r"const DS = (\[.*?\]);\n", html, re.S)
assert m, "khong tim thay du lieu DS trong de-thi.html"
ds = json.loads(m.group(1).replace("<\\/", "</"))
print("SO CAU TRONG TRANG:", len(ds))
khan = {}
for c in ds:
    khan[(c["cd"], c["muc"])] = khan.get((c["cd"], c["muc"]), 0) + 1
for k in sorted(khan):
    print("   %-14s muc %s : %2d cau" % (k[0], k[1], khan[k]))
thieu = [c["de"][:50] for c in ds if not c["tl"]]
print("CAU THIEU DAP AN:", len(thieu))
co_giai = sum(1 for c in ds if c["giai"])
print("CAU CO CACH GIAI TUNG BUOC:", co_giai)

# kiem tra phap cho toan bo file html (node --check khong doc duoc html, tach phan script ra)
js = html[html.index("<script>") + 8:html.rindex("</script>")]
io.open(os.path.join(GOC, "static", "_tmp.js"), "w", encoding="utf-8").write(js)
node = r"C:\Users\ITASUZAC\AppData\Local\Programs\OpenCowork\resources\node\node.exe"
if os.path.exists(node):
    r = subprocess.run([node, "--check", os.path.join(GOC, "static", "_tmp.js")],
                       capture_output=True, text=True)
    print("NODE --CHECK:", "OK" if r.returncode == 0 else r.stderr[:400])
os.remove(os.path.join(GOC, "static", "_tmp.js"))

# kiem tra app.py duong dan moi
sys.path.insert(0, GOC)
src = io.open(os.path.join(GOC, "app.py"), encoding="utf-8").read()
print("CO DUONG DAN /de-thi:", "/de-thi" in src)
print("TRANG CHAT CO NUM DE THI:", "deBtn" in io.open(os.path.join(GOC, "static", "index.html"), encoding="utf-8").read())
