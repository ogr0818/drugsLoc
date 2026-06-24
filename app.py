from __future__ import annotations

import re
from pathlib import Path
from threading import Timer
import webbrowser

import pandas as pd
from bottle import Bottle, TEMPLATE_PATH, request, run, static_file, template

BASE_DIR = Path(__file__).resolve().parent
VIEWS_DIR = BASE_DIR / 'views'
STATIC_DIR = BASE_DIR / 'static'
DATA_DIR = BASE_DIR / 'data'
DATA_FILE = DATA_DIR / 'drugs.xls'
REQUIRED_COLUMNS = ['id', 'drug_name', 'location']

if str(VIEWS_DIR) not in TEMPLATE_PATH:
    TEMPLATE_PATH.insert(0, str(VIEWS_DIR))

app = Bottle()

VALID_LOCATIONS = {f'{col}-{row}' for col in range(1, 9) for row in range(1, 7)} | {'層架'}
ID_PATTERN = re.compile(r'^[A-Z0-9]+$')


def load_raw_dataframe() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f'找不到資料檔：{DATA_FILE}')
    return pd.read_excel(DATA_FILE, dtype=str)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.rename(columns={c: str(c).strip() for c in df.columns})
    missing = [col for col in REQUIRED_COLUMNS if col not in renamed.columns]
    if missing:
        raise ValueError(f'資料檔缺少必要欄位：{", ".join(missing)}')

    result = renamed[REQUIRED_COLUMNS].copy()
    result = result.fillna('')
    for col in REQUIRED_COLUMNS:
        result[col] = result[col].astype(str).str.strip()
    result['id'] = result['id'].str.upper()
    return result


def load_drug_dataframe() -> pd.DataFrame:
    return normalize_columns(load_raw_dataframe())


def validate_dataset(df: pd.DataFrame) -> str | None:
    for col in REQUIRED_COLUMNS:
        if df[col].eq('').any():
            return f'資料異常：{col} 不可空白，請檢查藥品基本資料檔。'

    duplicate_mask = df['id'].duplicated(keep=False) & df['id'].ne('')
    if duplicate_mask.any():
        duplicated_ids = sorted(df.loc[duplicate_mask, 'id'].unique())
        return f"資料異常：id 重複，請檢查藥品基本資料檔。({', '.join(duplicated_ids[:5])})"

    invalid_locations = sorted({loc for loc in df['location'].unique() if loc and loc not in VALID_LOCATIONS})
    if invalid_locations:
        return f"資料異常：location 不在儲位配置內。({', '.join(invalid_locations[:5])})"

    return None


def render_index(message: str = '', result: dict[str, str] | None = None, active_location: str = ''):
    return template(
        'index',
        code="",
        source_name=DATA_FILE.name,
        message=message,
        result=result,
        active_location=active_location,
    )


@app.route('/static/<filepath:path>')
def serve_static(filepath: str):
    return static_file(filepath, root=str(STATIC_DIR))


@app.get('/')
@app.post('/')
def index():
    code = request.forms.get('code') if request.method == 'POST' else request.query.get('code', '')
    code = (code or '').strip().upper()

    message = ''
    result = None
    active_location = ''

    try:
        df = load_drug_dataframe()
    except Exception as exc:
        return render_index(message=f'資料檔讀取失敗：{exc}')

    validation_error = validate_dataset(df)
    if validation_error:
        return render_index(message=validation_error)

    if code:
        if not ID_PATTERN.fullmatch(code):
            message = '格式錯誤，請輸入藥品代碼。'
        else:
            match = df.loc[df['id'] == code]
            if match.empty:
                message = '查無此藥品代碼。'
            else:
                row = match.iloc[0]
                active_location = row['location']
                result = {
                    'id': row['id'],
                    'drug_name': row['drug_name'],
                    'location': row['location'],
                }

    return render_index(message=message, result=result, active_location=active_location)


if __name__ == '__main__':
    Timer(1.0, lambda: webbrowser.open('http://127.0.0.1:8000/')).start()

    run(
        app=app,
        host='127.0.0.1',
        port=8000,
        debug=True,
        reloader=False,
    )
