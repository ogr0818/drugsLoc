# 輸入藥品代碼，查詢藥品在住院藥局的庫存儲位

## 盤點期間協助查詢庫位

## 將 app.py 部署至 Netlify 網頁

Netlify 以靜態站部署此查詢工具。更新 `data/drugs.xls` 後，先產生靜態檔案：

```bash
uv run python scripts/build_static.py
```

部署目錄為 `public/`。
