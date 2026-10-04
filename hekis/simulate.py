"""Senaryo kos ve raporu yaz.

Kullanim:
    python -m hekis.simulate scenarios/baseline.json scenarios/nakit_kacis.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hekis.model import format_report, load_scenario, result_to_dict, simulate


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        root = Path(__file__).resolve().parents[1] / "scenarios"
        args = [str(root / "baseline.json"), str(root / "nakit_kacis.json")]

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    for path in args:
        units, inflation, index, params, name = load_scenario(path)
        result = simulate(units, inflation, index, params, name=name)
        text = format_report(result)
        print(text)
        print()
        target = out_dir / f"{Path(path).stem}.json"
        target.write_text(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"yazildi: {target}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
