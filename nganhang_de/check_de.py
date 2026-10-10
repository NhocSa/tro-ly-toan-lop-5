# -*- coding: utf-8 -*-
"""Kiem tra ngan hang cau hoi (tuyen chon + tu dong) -> nganhang/check.txt"""
import glob, io, os, sys
from collections import Counter
GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
import de_bank as B
import de_auto as A

ra = io.open(os.path.join(GOC, "nganhang", "check.txt"), "w", encoding="utf-8")
loi = B.kiem_tra(B.TUYEN_CHON)
ra.write("TUY CHON: %d cau | canh bao: %d\n" % (len(B.TUYEN_CHON), len(loi)))
for x in loi:
    ra.write("  " + x + "\n")

auto = []
for muc in (1, 2, 3, 4):
    for f in glob.glob(os.path.join(GOC, "SO HOC MUC %d.docx" % muc)):
        auto += A.dat_tinh(muc, f)
for ten, muc in (("DAI LUONG MUC 2", 2), ("DAI LUONG MUC 3", 3), ("DAL LUONG MUC 4", 4)):
    for f in glob.glob(os.path.join(GOC, ten + ".docx")):
        auto += A.dai_luong(muc, f)
ra.write("TU DONG: %d cau\n" % len(auto))
ra.write("Vi du: %s\n" % " | ".join(d["de"] + " = " + d["tl"] for d in auto[:14]))
ra.write("Phan bo tuyen chon: %s\n" % sorted(Counter((c["cd"], c["muc"]) for c in B.TUYEN_CHON).items()))
ra.write("Phan bo tu dong: %s\n" % sorted(Counter((c["cd"], c["muc"]) for c in auto).items()))
ra.write("Nam (tu dong): %s\n" % sorted(Counter(c["nam"] for c in auto).items()))
ra.close()
print("ok")
