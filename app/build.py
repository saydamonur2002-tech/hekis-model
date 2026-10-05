"""app/index.html uretir: template.html + model.js + constants.json (tek dosya, bagimliliksiz)."""
import json, pathlib
d = pathlib.Path(__file__).parent
t = (d / "template.html").read_text()
t = t.replace("/*CONSTANTS*/", json.dumps(json.load(open(d / "constants.json")), separators=(",", ":")))
m = (d / "model.js").read_text()
t = t.replace("/*MODEL*/", m)
(d / "index.html").write_text(t)
print("index.html", len(t) // 1024, "KB")
