import streamlit as st
import requests
import time

st.set_page_config(page_title="국내 주식 조회", page_icon="📈", layout="wide")

# ── 스타일 ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;600;800&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #f0f2f5; }
.block-container { padding-top: 2rem !important; }

.stTextInput > div > div > input {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    border: 2px solid #e2e8f0 !important;
    padding: 0.7rem 1rem !important;
    background: #fff !important;
}
.stTextInput > div > div > input:focus { border-color: #0f172a !important; }

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 20px 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.1em !important;
    color: #94a3b8 !important;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.9rem !important;
    color: #0f172a !important;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"] > div { font-size: 0.82rem !important; font-weight: 700 !important; }

.section-label {
    font-size: 0.63rem; font-weight: 800; letter-spacing: 0.2em;
    text-transform: uppercase; color: #94a3b8; margin: 24px 0 10px 2px;
}
.stock-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    border-radius: 16px; padding: 24px 28px; margin-bottom: 8px; color: white;
}
.stock-banner .sname { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; letter-spacing: 0.04em; line-height:1; }
.stock-banner .scode { font-size: 0.78rem; color: #94a3b8; margin-top: 4px; letter-spacing: 0.1em; }
.stock-banner .sbadge {
    display: inline-block; background: rgba(255,255,255,0.12);
    border-radius: 6px; padding: 2px 10px; font-size: 0.75rem; font-weight: 700; margin-top: 10px;
}
.info-box {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 20px 22px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.info-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem;
}
.info-row:last-child { border-bottom: none; }
.info-key { color: #64748b; font-weight: 600; font-size: 0.82rem; }
.info-val { color: #0f172a; font-weight: 800; }
.up { color: #ef4444; } .down { color: #3b82f6; } .flat { color: #64748b; }

/* 힌트 박스 */
.hint-box {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 16px 20px; margin-top: 16px; font-size: 0.85rem; color: #475569;
}
.hint-box b { color: #0f172a; }

.stButton > button {
    background: #0f172a; color: white; border: none;
    border-radius: 10px; font-weight: 700; font-size: 0.9rem;
    padding: 0.55rem 1.5rem; transition: background 0.2s; width: 100%;
}
.stButton > button:hover { background: #1e3a5f; }
</style>
""", unsafe_allow_html=True)


# ── KIS API 유틸 ──────────────────────────────────────────────────────────────
@st.cache_resource(ttl=1700)
def get_access_token(app_key: str, app_secret: str) -> str:
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    res = requests.post(url, json={
        "grant_type": "client_credentials",
        "appkey":     app_key,
        "appsecret":  app_secret,
    }, timeout=10)
    res.raise_for_status()
    data = res.json()
    if "access_token" not in data:
        raise ValueError(f"토큰 발급 실패: {data.get('error_description', data)}")
    return data["access_token"]


def get_stock_price(app_key: str, app_secret: str, stock_code: str) -> dict:
    """주식현재가 시세 조회 (FHKST01010100)"""
    token = get_access_token(app_key, app_secret)
    url   = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type":  "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey":        app_key,
        "appsecret":     app_secret,
        "tr_id":         "FHKST01010100",
        "custtype":      "P",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD":         stock_code.zfill(6),
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)

    # 디버그용: 상태코드와 raw 응답을 세션에 저장
    st.session_state["_last_status"] = res.status_code
    st.session_state["_last_body"]   = res.text[:300]

    res.raise_for_status()
    data = res.json()

    if data.get("rt_cd") != "0":
        raise ValueError(f"[{data.get('msg_cd')}] {data.get('msg1', 'API 오류')}")
    return data["output"]


def fmt_num(val: str, suffix: str = "") -> str:
    try:
        n = float(val)
        if abs(n) >= 1_000_000_000_000:
            return f"{n/1_000_000_000_000:.2f}조{suffix}"
        if abs(n) >= 100_000_000:
            return f"{n/100_000_000:.0f}억{suffix}"
        return f"{int(n):,}{suffix}"
    except Exception:
        return val or "-"


def color_class(val: str) -> str:
    try:
        return "up" if float(val) > 0 else ("down" if float(val) < 0 else "flat")
    except Exception:
        return "flat"


def arrow(val: str) -> str:
    try:
        v = float(val)
        return "▲" if v > 0 else ("▼" if v < 0 else "")
    except Exception:
        return ""


# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:2.5px solid #0f172a; padding-bottom:14px; margin-bottom:20px;">
    <div style="font-size:0.7rem; font-weight:800; letter-spacing:0.25em; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">
        KIS DEVELOPERS
    </div>
    <div style="font-family:'Bebas Neue',sans-serif; font-size:2.4rem; letter-spacing:0.05em; color:#0f172a; line-height:1;">
        국내 주식 종목 조회
    </div>
</div>
""", unsafe_allow_html=True)

# ── secrets 체크 ──────────────────────────────────────────────────────────────
try:
    APP_KEY    = st.secrets["kis"]["app_key"]
    APP_SECRET = st.secrets["kis"]["app_secret"]
except Exception:
    st.error("⚠️ `.streamlit/secrets.toml`에 KIS API 키를 설정해주세요.")
    st.code("""
[kis]
app_key    = "your-app-key"
app_secret = "your-app-secret"
""", language="toml")
    st.stop()

# ── 검색창 ───────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    stock_code_input = st.text_input(
        "종목코드 입력",
        placeholder="6자리 종목코드 입력  예) 005930 (삼성전자)  /  035720 (카카오)  /  000660 (SK하이닉스)",
        max_chars=6,
        label_visibility="collapsed",
    )
with col_btn:
    search_btn = st.button("🔍 조회", use_container_width=True)

# 종목코드 힌트
st.markdown("""
<div class="hint-box">
    💡 <b>종목코드를 모르시나요?</b> &nbsp;
    <a href="https://finance.naver.com" target="_blank" style="color:#3b82f6;">네이버 금융</a> 또는
    <a href="https://www.krx.co.kr" target="_blank" style="color:#3b82f6;">KRX 홈페이지</a>에서
    종목명으로 검색하면 6자리 코드를 확인할 수 있습니다.
    <br>자주 쓰는 코드: 삼성전자 <b>005930</b> · SK하이닉스 <b>000660</b> · 카카오 <b>035720</b> · NAVER <b>035420</b> · LG에너지솔루션 <b>373220</b>
</div>
""", unsafe_allow_html=True)

# ── 조회 실행 ─────────────────────────────────────────────────────────────────
if search_btn:
    code = stock_code_input.strip()

    if not code:
        st.warning("종목코드를 입력해주세요.")
        st.stop()
    if not code.isdigit() or len(code) != 6:
        st.warning("종목코드는 숫자 6자리입니다. (예: 005930)")
        st.stop()

    with st.spinner(f"**{code}** 종목 정보를 조회 중입니다..."):
        try:
            output = get_stock_price(APP_KEY, APP_SECRET, code)
        except requests.exceptions.HTTPError as e:
            status = st.session_state.get("_last_status", "?")
            body   = st.session_state.get("_last_body", "")
            st.error(f"❌ HTTP {status} 오류")
            with st.expander("🔍 상세 오류 내용 보기"):
                st.code(body)
                st.markdown("""
**주요 원인 체크리스트**
- `401` → 앱키/앱시크릿이 잘못됐거나 토큰이 만료됨
- `403` → API 권한 없음 (KIS Developers에서 서비스 신청 필요)
- `500` → 종목코드 오류이거나 장 마감 후 일부 데이터 없음
""")
            st.stop()
        except ValueError as e:
            st.error(f"❌ {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
            st.stop()

    # ── 데이터 파싱 ──────────────────────────────────────────────────────────
    display_name = output.get("hts_kor_isnm", code)
    curr_price   = output.get("stck_prpr", "0")
    change_price = output.get("prdy_vrss", "0")
    change_pct   = output.get("prdy_ctrt", "0")
    volume       = output.get("acml_vol", "0")
    trade_amt    = output.get("acml_tr_pbmn", "0")
    high_52      = output.get("w52_hgpr", "0")
    low_52       = output.get("w52_lwpr", "0")
    open_price   = output.get("stck_oprc", "0")
    high_price   = output.get("stck_hgpr", "0")
    low_price    = output.get("stck_lwpr", "0")
    per          = output.get("per", "-")
    pbr          = output.get("pbr", "-")
    market_cap   = output.get("hts_avls", "0")    # 시가총액(억)

    cc = color_class(change_pct)
    ar = arrow(change_pct)

    # ── 종목 배너 ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="stock-banner">
        <div class="sname">{display_name}</div>
        <div class="scode">KRX &nbsp;·&nbsp; {code}</div>
        <div class="sbadge">국내주식</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 핵심 지표 3개 ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📌 핵심 지표</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        try:
            delta_str = f"{ar} {abs(float(change_pct))}% ({int(float(change_price)):+,}원)"
        except Exception:
            delta_str = "-"
        st.metric("현재가", f"{int(float(curr_price)):,}원",
                  delta=delta_str,
                  delta_color="normal" if float(change_pct) >= 0 else "inverse")
    with c2:
        st.metric("거래량", fmt_num(volume, "주"))
    with c3:
        st.metric("거래대금", fmt_num(trade_amt, "원"))

    # ── 상세 정보 2열 ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📋 상세 정보</div>', unsafe_allow_html=True)
    left, right = st.columns(2)

    def safe_int(v):
        try: return f"{int(float(v)):,}원"
        except: return "-"

    with left:
        st.markdown(f"""
        <div class="info-box">
            <div class="info-row"><span class="info-key">시가</span><span class="info-val">{safe_int(open_price)}</span></div>
            <div class="info-row"><span class="info-key">고가</span><span class="info-val up">{safe_int(high_price)}</span></div>
            <div class="info-row"><span class="info-key">저가</span><span class="info-val down">{safe_int(low_price)}</span></div>
            <div class="info-row"><span class="info-key">52주 최고</span><span class="info-val up">{safe_int(high_52)}</span></div>
            <div class="info-row"><span class="info-key">52주 최저</span><span class="info-val down">{safe_int(low_52)}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        try:
            mktcap_str = fmt_num(str(int(float(market_cap)) * 100_000_000), "원")
        except Exception:
            mktcap_str = "-"
        st.markdown(f"""
        <div class="info-box">
            <div class="info-row"><span class="info-key">시가총액</span><span class="info-val">{mktcap_str}</span></div>
            <div class="info-row"><span class="info-key">PER</span><span class="info-val">{per}배</span></div>
            <div class="info-row"><span class="info-key">PBR</span><span class="info-val">{pbr}배</span></div>
            <div class="info-row">
                <span class="info-key">전일 대비</span>
                <span class="info-val {cc}">{ar} {safe_int(change_price)}</span>
            </div>
            <div class="info-row">
                <span class="info-key">등락률</span>
                <span class="info-val {cc}">{ar} {abs(float(change_pct))}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#cbd5e1; font-size:0.72rem; margin-top:32px;
            padding-top:16px; border-top:1px solid #e2e8f0;">
    데이터 출처: 한국투자증권 KIS Developers &nbsp;·&nbsp; 투자 참고용이며 실제 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)