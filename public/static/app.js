const validLocations = new Set([
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
});

init();
