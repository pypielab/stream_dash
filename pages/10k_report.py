import streamlit as st
import os
import sys

# sec_downloader.py가 같은 디렉토리에 있다고 가정
sys.path.append(os.path.dirname(__file__))
from sec_downloader import download_10k

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="10-K Report Downloader",
    page_icon="📄",
    layout="centered",
)

# ── 스타일 ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .title-block {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        color: white;
    }
    .title-block h1 { margin: 0; font-size: 2rem; }
    .title-block p  { margin: 0.4rem 0 0; color: #a0aec0; font-size: 0.95rem; }

    .result-box {
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-top: 1.5rem;
        font-size: 0.95rem;
    }
    .result-success {
        background: #f0fff4;
        border: 1px solid #9ae6b4;
        color: #276749;
    }
    .result-error {
        background: #fff5f5;
        border: 1px solid #feb2b2;
        color: #9b2335;
    }
    .info-badge {
        display: inline-block;
        background: #ebf8ff;
        color: #2b6cb0;
        border-radius: 6px;
        padding: 0.15rem 0.55rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="title-block">
    <h1>📄 10-K Report Downloader</h1>
    <p>SEC EDGAR에서 기업의 최신 10-K 연간 보고서를 다운로드합니다.</p>
</div>
""", unsafe_allow_html=True)

# ── 안내 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<span class="info-badge">SEC EDGAR</span>
<span class="info-badge">미국 상장사</span>
<span class="info-badge">연간 보고서</span>
""", unsafe_allow_html=True)

st.caption("티커 심볼을 입력하면 SEC EDGAR에서 최신 10-K 보고서를 자동으로 찾아 다운로드합니다.")
st.divider()

# ── 입력 폼 ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    ticker = st.text_input(
        "티커 심볼 (Ticker Symbol)",
        placeholder="예: AAPL, MSFT, CRWD, TSLA",
        max_chars=10,
        help="미국 증시에 상장된 기업의 티커 심볼을 입력하세요.",
    )

with col2:
    save_dir = st.text_input(
        "저장 폴더",
        value="./reports",
        help="보고서를 저장할 경로",
    )

download_btn = st.button("📥 다운로드", type="primary", use_container_width=True)

# ── 다운로드 실행 ─────────────────────────────────────────────────────────────
if download_btn:
    if not ticker.strip():
        st.warning("⚠️ 티커 심볼을 입력해주세요.")
    else:
        with st.spinner(f"**{ticker.upper().strip()}** 10-K 보고서를 조회 중입니다..."):
            result = download_10k(ticker.strip(), save_dir=save_dir.strip())

        if result["success"]:
            st.markdown(f"""
            <div class="result-box result-success">
                ✅ <strong>다운로드 완료</strong><br>
                {result['message']}<br><br>
                📁 저장 경로: <code>{result['save_path']}</code>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**🔗 SEC EDGAR 원본 링크**")
            st.code(result["download_url"], language=None)

            # 파일 다운로드 버튼
            with open(result["save_path"], "rb") as f:
                file_bytes = f.read()

            file_ext = os.path.splitext(result["save_path"])[1]
            mime = "text/html" if file_ext == ".htm" or file_ext == ".html" else "application/octet-stream"

            st.download_button(
                label=f"💾 {ticker.upper().strip()}_10K{file_ext} 저장하기",
                data=file_bytes,
                file_name=f"{ticker.upper().strip()}_10K{file_ext}",
                mime=mime,
                use_container_width=True,
            )
        else:
            st.markdown(f"""
            <div class="result-box result-error">
                ❌ <strong>다운로드 실패</strong><br>
                {result['message']}
            </div>
            """, unsafe_allow_html=True)

# ── 하단 안내 ─────────────────────────────────────────────────────────────────
st.divider()
st.caption("📌 데이터 출처: [SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch.html)  ·  미국 상장사만 지원됩니다.")