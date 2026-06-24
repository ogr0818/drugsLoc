from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "drugs.xls"
STATIC_DIR = BASE_DIR / "static"
PUBLIC_DIR = BASE_DIR / "public"
PUBLIC_DATA_DIR = PUBLIC_DIR / "data"
PUBLIC_STATIC_DIR = PUBLIC_DIR / "static"
REQUIRED_COLUMNS = ["id", "drug_name", "location"]


def load_drugs() -> list[dict[str, str]]:
    df = pd.read_excel(DATA_FILE, dtype=str)
    df = df.rename(columns={c: str(c).strip() for c in df.columns})
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"資料檔缺少必要欄位：{', '.join(missing)}")

    result = df[REQUIRED_COLUMNS].fillna("").copy()
    for col in REQUIRED_COLUMNS:
        result[col] = result[col].astype(str).str.strip()
    result["id"] = result["id"].str.upper()
    return result.to_dict(orient="records")


def render_slots() -> str:
    rows: list[str] = []
    for row_no in range(6, 0, -1):
        slots = []
        for col_no in range(8, 0, -1):
            location = f"{col_no}-{row_no}"
            slots.append(f'<div class="slot" data-location="{location}">{location}</div>')
        rows.append(f'<div class="map-row map-row-8">{"".join(slots)}</div>')
    rows.append('<div class="front-rack" data-location="層架">層架</div>')
    return "\n        ".join(rows)


def render_index() -> str:
    source_name = escape(DATA_FILE.name)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>住院儲位</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <main class="page-shell">
    <section class="card">
      <form class="query-row" autocomplete="off" id="query-form">
        <label class="bar-cord">藥品代碼：
          <input
            type="text"
            name="code"
            class="code-input"
            placeholder="請輸入藥品代碼"
            autofocus
          >
          <button type="submit" class="submit-btn">查詢</button>
        </label>
      </form>

      <div class="status-row">
        <div class="status-box neutral" id="status-box">資料來源：{source_name}</div>
      </div>

      <div class="map-wrap">
        {render_slots()}
      </div>
    </section>
  </main>
  <script src="/static/app.js"></script>
</body>
</html>
"""


def render_app_js() -> str:
    return """const validLocations = new Set([
  ...Array.from({ length: 8 }, (_, col) =>
    Array.from({ length: 6 }, (_, row) => `${col + 1}-${row + 1}`)
  ).flat(),
  "層架",
]);

const form = document.querySelector("#query-form");
const input = document.querySelector(".code-input");
const statusBox = document.querySelector("#status-box");
const locationNodes = document.querySelectorAll("[data-location]");

let drugsById = new Map();

function setStatus(kind, text) {
  statusBox.className = `status-box ${kind}`;
  statusBox.textContent = text;
}

function clearActiveLocation() {
  locationNodes.forEach((node) => node.classList.remove("active"));
}

function setActiveLocation(location) {
  clearActiveLocation();
  const target = document.querySelector(`[data-location="${CSS.escape(location)}"]`);
  if (target) target.classList.add("active");
}

function normalizeCode(value) {
  return value.trim().toUpperCase();
}

function search(code) {
  const normalized = normalizeCode(code);
  input.value = normalized;
  clearActiveLocation();

  if (!normalized) {
    setStatus("neutral", "資料來源：drugs.xls");
    return;
  }

  if (!/^[A-Z0-9]+$/.test(normalized)) {
    setStatus("error", "格式錯誤，請輸入藥品代碼。");
    return;
  }

  const result = drugsById.get(normalized);
  if (!result) {
    setStatus("error", "查無此藥品代碼。");
    return;
  }

  setStatus("success", `商品名： ${result.drug_name} ｜ 儲位： ${result.location}`);
  setActiveLocation(result.location);
}

async function init() {
  try {
    const response = await fetch("/data/drugs.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const drugs = await response.json();

    const invalid = drugs.find(
      (drug) => !drug.id || !drug.drug_name || !drug.location || !validLocations.has(drug.location)
    );
    if (invalid) {
      setStatus("error", "資料異常，請檢查藥品基本資料檔。");
      return;
    }

    drugsById = new Map(drugs.map((drug) => [drug.id, drug]));
    const params = new URLSearchParams(window.location.search);
    search(params.get("code") || "");
  } catch (error) {
    setStatus("error", `資料檔讀取失敗：${error.message}`);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const code = normalizeCode(input.value);
  const url = new URL(window.location.href);
  if (code) {
    url.searchParams.set("code", code);
  } else {
    url.searchParams.delete("code");
  }
  window.history.replaceState({}, "", url);
  search(code);
  input.value = "";
});

init();
"""


def main() -> None:
    drugs = load_drugs()
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_STATIC_DIR.mkdir(parents=True, exist_ok=True)

    (PUBLIC_DIR / "index.html").write_text(render_index(), encoding="utf-8")
    (PUBLIC_DATA_DIR / "drugs.json").write_text(
        json.dumps(drugs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (PUBLIC_STATIC_DIR / "app.js").write_text(render_app_js(), encoding="utf-8")
    shutil.copy2(STATIC_DIR / "styles.css", PUBLIC_STATIC_DIR / "styles.css")


if __name__ == "__main__":
    main()
