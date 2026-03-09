import streamlit as st
import os
import sys
from streamlit_option_menu import option_menu

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
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');

html, body, [class*="css"]  {
    color: #d1d5db; /* light grey text for readability */
    font-family: 'Manrope', 'Segoe UI', sans-serif;
    background-color: #0E1117; /* solid dark base */
}

.stApp {
    background-color: #0E1117;
}

/* apply dark container backgrounds where needed */
.block-container, .stSidebar, .stButton>button, .stDownloadButton>button {
    background-color: #131820;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(circle at 35% 25%, rgba(255, 255, 255, 0.14), transparent 22%),
        radial-gradient(circle at 65% 60%, rgba(255, 240, 180, 0.12), transparent 30%);
    filter: blur(24px);
    z-index: 0;
}

.block-container {
    position: relative;
    z-index: 1;
    padding-top: 1.1rem;
}

[data-testid="stSidebar"] {
    background: rgba(14, 21, 33, 0.56);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-right: 1px solid rgba(255, 255, 255, 0.14);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem;
}

.side-title {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 0.3px;
    margin-bottom: 18px;
}

.side-menu {
    margin: 0;
    padding: 0;
    list-style: none;
}

.side-menu li {
    padding: 10px 14px;
    margin-bottom: 8px;
    border-radius: 12px;
    color: rgba(234, 239, 245, 0.88);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.10);
}

.side-menu li.active {
    background: rgba(250, 212, 106, 0.14);
    border: 1px solid rgba(250, 212, 106, 0.38);
    color: #ffe9a9;
}

.top-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 14px;
    margin-bottom: 18px;
    border-radius: 18px;
    background: rgba(23, 30, 43, 0.80);
    backdrop-filter: blur(16px);
    border: 1px solid #0ff; /* neon border */
}

.search-box {
    flex: 1;
    padding: 10px 14px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: rgba(236, 241, 246, 0.80);
}

.toolbar-badges {
    display: flex;
    gap: 8px;
}

.pill {
    padding: 8px 14px;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    background: rgba(255, 255, 255, 0.08);
    font-size: 13px;
}

.pill.active {
    background: rgba(255, 255, 255, 0.20);
    color: #fff7d2;
    border: 1px solid rgba(255, 237, 166, 0.34);
}

/* 기존 스타일 */

/* button neon effect + hover */
.stButton>button, .stDownloadButton>button {
    border: 1px solid #0ff;
    box-shadow: 0 0 8px #0ff;
    transition: background-color 0.2s, color 0.2s;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    background-color: #0ff;
    color: #0e1117;
}

/* high contrast for charts (if any are added) */
.echarts-chart path, .echarts-chart rect, .echarts-chart polygon, .echarts-chart circle {
    stroke-width: 2 !important;
}

/* make glass cards darker to fit dark mode */
.glass-card {
    background: rgba(20, 25, 34, 0.75);
    border: 1px solid #0ff;
}
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
    border: 1px solid #0ff;
    box-shadow: 0 0 8px #0ff;
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
    background: #1f2937; /* darker for contrast */
    color: #d1d5db;
    border: 1px solid #0ff;
    border-radius: 6px;
    padding: 0.15rem 0.55rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ── 사이드바 (옵션 메뉴) ──────────────────────────────────────────────────────────
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Home", "10-K Downloader", "Reports", "Settings"],
        icons=["house", "cloud-arrow-down", "file-bar-graph", "gear"],
        menu_icon="cast",
        default_index=1,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#131820"},
            "nav-link": {"font-size": "16px", "color": "#d1d5db", "hover-color": "#0ff"},
            "nav-link-selected": {"background-color": "#0ff", "color": "#0e1117"},
        },
    )

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""<Br><Br><Br>
<div class="glass-card">
  <div class="title-block">
      <h1>📄 10-K Report Downloader</h1>
      <p>SEC EDGAR에서 기업의 최신 10-K 연간 보고서를 다운로드합니다.</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 안내 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="glass-card" style="padding:0.8rem 1.2rem;">
  <span class="info-badge">SEC EDGAR</span>
  <span class="info-badge">미국 상장사</span>
  <span class="info-badge">연간 보고서</span>
</div>
""", unsafe_allow_html=True)

st.caption("티커 심볼을 입력하면 SEC EDGAR에서 최신 10-K 보고서를 자동으로 찾아 다운로드합니다.")
st.divider()

# ── 입력 폼 ───────────────────────────────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

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