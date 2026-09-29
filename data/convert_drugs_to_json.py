"""將同資料夾的 drugs.xls 轉成 drugs.json。

執行：uv run python data/convert_drugs_to_json.py
相依套件：pandas、xlrd（已列於專案 pyproject.toml）。
"""

import json
from pathlib import Path

import pandas as pd


def main() -> None:
    data_dir = Path(__file__).resolve().parent
    columns = ["id", "drug_name", "location"]
    drugs = pd.read_excel(
        data_dir / "drugs.xls", engine="xlrd", dtype=str, keep_default_na=False
    )
    missing = [column for column in columns if column not in drugs.columns]
    if missing:
        raise ValueError(f"缺少必要欄位：{', '.join(missing)}")

    records = drugs[columns].to_dict(orient="records")
    output_file = data_dir / "drugs.json"
    output_file.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已產生 {output_file}，共 {len(records)} 筆資料。")


if __name__ == "__main__":
    main()
