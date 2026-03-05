"""
stock_master_upload.py
─────────────────────
kind.krx.co.kr에서 전종목 목록을 수집해
Supabase stock_master 테이블에 저장합니다.

실행:
    python stock_master_upload.py
"""

# Streamlit 경고 억제
import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)
import os
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")

import tomllib
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from supabase import create_client

# ── secrets.toml 읽기 ─────────────────────────────────────────────────────────
_secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
with open(_secrets_path, "rb") as f:
    _secrets = tomllib.load(f)

SUPABASE_URL = _secrets["supabase"]["url"]
SUPABASE_KEY = _secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# KIND KRX 컬럼 → Supabase 컬럼 매핑
COL_MAP = {
    "회사명":   "name",
    "시장구분":  "market",
    "종목코드":  "code",
    "업종":     "sector",
    "주요제품":  "product",
    "상장일":   "listed_date",
    "결산월":   "fiscal_month",
    "대표자명":  "ceo",
    "홈페이지":  "website",
    "지역":     "region",
}


def clean(val) -> str:
    """NaN, None을 빈 문자열로 변환"""
    if val is None: return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def fetch_all_tickers() -> list[dict]:
    url = "http://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    print("  KIND KRX에서 종목 목록 다운로드 중...")
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()

    df = pd.read_html(res.text, encoding="cp949")[0]
    print(f"  원본 컬럼: {list(df.columns)}")

    # 종목코드 6자리 정규화
    df["종목코드"] = df["종목코드"].astype(str).str.zfill(6)

    now_iso = datetime.utcnow().isoformat()
    rows = []

    for _, row in df.iterrows():
        code = clean(row.get("종목코드"))
        name = clean(row.get("회사명"))
        if not code or not name:
            continue

        record = {"updated_at": now_iso}
        for krx_col, db_col in COL_MAP.items():
            record[db_col] = clean(row.get(krx_col, ""))

        rows.append(record)

    print(f"  총 {len(rows)}개 종목 수집 완료")
    return rows


def upload_to_supabase(rows: list[dict], batch_size: int = 500):
    total = len(rows)
    print(f"\nSupabase 업로드 시작 (총 {total}개, {batch_size}개씩 배치)...")
    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("stock_master").upsert(batch, on_conflict="code").execute()
        print(f"  업로드: {min(i + batch_size, total)}/{total}")
    print("✅ Supabase 업로드 완료!")


if __name__ == "__main__":
    print("=" * 40)
    print("  종목 마스터 업로드 시작 (KIND KRX)")
    print("=" * 40)
    rows = fetch_all_tickers()
    if rows:
        upload_to_supabase(rows)
    else:
        print("❌ 수집된 종목이 없습니다.")
    print("=" * 40)
    print("  완료!")
    print("=" * 40)