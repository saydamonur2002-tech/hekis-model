"""main dalindaki enflasyon / doviz / kamu modulleri icin duman testi ve gerileme koruyucusu.

Bu modullerin kendi `testler()` fonksiyonlari var: bir hipotezi veriyle sinar ve `[GECTI]` / `[KALDI]` yazar. `[KALDI]` bir
kod hatasi degil, arastirma bulgusudur (ornegin "model ornek disinda naiften kotu"). Bu yuzden KALDI sayisi hata sayilmaz.
Burada iki sey sinanir:
  1. Modul calisir: cikis kodu 0, stderr'de Traceback yok.
  2. GECTI ve KALDI sayilari `tests/main_baseline.json` ile ayni. Veri, kod ya da hesap degisirse sayi degisir ve test
     kirilir: degisiklik bilincli ise taban guncellenir.

Tabani guncelle: python tests/test_main_modules.py --update
"""

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_baseline.json")
MODULES = (
    "acmaz", "atalet", "ayrisma", "beklenti", "birikim", "borc_doviz", "dezenf", "enflasyon", "entegre", "gerceklik",
    "ito", "ito_alt", "kalibre", "kamu", "kira", "kirilma", "metod", "mulkiyet", "olcum", "ovp", "reset", "rezerv",
    "sonuc", "tampon", "ucret",
)


def run(module: str) -> dict:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    p = subprocess.run([sys.executable, "-m", f"hekis.{module}"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    return {"rc": p.returncode, "err": p.stderr, "GECTI": p.stdout.count("[GECTI]"), "KALDI": p.stdout.count("[KALDI]")}


class MainModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(BASELINE, encoding="utf-8") as f:
            cls.base = json.load(f)

    def test_baseline_covers_modules(self):
        self.assertEqual(sorted(self.base), sorted(MODULES))


def _make(module: str):
    def test(self):
        r = run(module)
        self.assertEqual(r["rc"], 0, r["err"][-600:])
        self.assertNotIn("Traceback", r["err"])
        exp = self.base[module]
        self.assertEqual({"GECTI": r["GECTI"], "KALDI": r["KALDI"]}, exp,
                         f"{module}: GECTI/KALDI sayisi tabandan farkli. Bilincli ise: python tests/test_main_modules.py --update")
    return test


for _m in MODULES:
    setattr(MainModules, f"test_{_m}", _make(_m))


if __name__ == "__main__":
    if "--update" in sys.argv:
        out = {}
        for m in MODULES:
            r = run(m)
            assert r["rc"] == 0, (m, r["err"][-400:])
            out[m] = {"GECTI": r["GECTI"], "KALDI": r["KALDI"]}
        with open(BASELINE, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
        print("taban yazildi:", BASELINE)
    else:
        unittest.main()
