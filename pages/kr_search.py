import streamlit as st
import requests
from supabase import create_client

st.set_page_config(page_title="국내 주식 조회", page_icon="📈", layout="wide")

# ── 스타일 ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;600;800&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #f0f2f5; }
.block-container { padding-top: 2rem !important; }

.stTextInput > div > div > input {
    font-size: 1.1rem !important; font-weight: 600 !important;
    border-radius: 12px !important; border: 2px solid #e2e8f0 !important;
    padding: 0.7rem 1rem !important; background: #ffffff !important;
    color: #0f172a !important;
    caret-color: #0f172a !important;
}
.stTextInput > div > div > input:focus { border-color: #0f172a !important; }
.stTextInput > div > div > input::placeholder { color: #94a3b8 !important; }

[data-testid="metric-container"] {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 18px 20px 16px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important; font-weight: 800 !important;
    letter-spacing: 0.1em !important; color: #94a3b8 !important; text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.9rem !important; color: #0f172a !important;
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

.market-badge {
    display: inline-block; border-radius: 5px;
    padding: 2px 8px; font-size: 0.72rem; font-weight: 700;
}
.badge-KOSPI  { background: #dbeafe; color: #1d4ed8; }
.badge-KOSDAQ { background: #dcfce7; color: #15803d; }
.badge-KRX    { background: #f1f5f9; color: #475569; }

.sector-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    color: #e2e8f0;
    border-radius: 6px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 8px;
    margin-right: 6px;
}
.stButton > button {
    background: #0f172a; color: white; border: none;
    border-radius: 10px; font-weight: 700; font-size: 0.9rem;
    padding: 0.55rem 1.5rem; transition: background 0.2s; width: 100%;
}
.stButton > button:hover { background: #1e3a5f; }
</style>
""", unsafe_allow_html=True)


# ── 클라이언트 초기화 ─────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = get_supabase()

try:
    APP_KEY    = st.secrets["kis"]["app_key"]
    APP_SECRET = st.secrets["kis"]["app_secret"]
except Exception:
    st.error("⚠️ `.streamlit/secrets.toml`에 KIS API 키를 설정해주세요.")
    st.stop()


# ── Supabase 종목명 검색 ──────────────────────────────────────────────────────
def search_stocks(query: str, limit: int = 8) -> list[dict]:
    """
    1순위: 이름이 query로 시작하는 종목 (예: '현대차'로 시작)
    2순위: query를 포함하는 나머지 종목
    두 결과를 합쳐 limit 개수만큼 반환
    """
    # 1순위: 앞글자 일치
    starts = (
        supabase.table("stock_master")
        .select("code, name, market, sector, product")
        .ilike("name", f"{query}%")
        .order("name")
        .limit(limit)
        .execute()
    ).data

    # 2순위: 포함 (앞글자 일치 제외)
    already = {r["code"] for r in starts}
    if len(starts) < limit:
        contains = (
            supabase.table("stock_master")
            .select("code, name, market, sector, product")
            .ilike("name", f"%{query}%")
            .not_.ilike("name", f"{query}%")
            .order("name")
            .limit(limit - len(starts))
            .execute()
        ).data
        # 혹시 중복 제거
        contains = [r for r in contains if r["code"] not in already]
    else:
        contains = []

    return starts + contains


# ── KIS API ───────────────────────────────────────────────────────────────────
@st.cache_resource(ttl=1700)
def get_access_token(app_key: str, app_secret: str) -> str:
    res = requests.post(
        "https://openapi.koreainvestment.com:9443/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
        timeout=10,
    )
    res.raise_for_status()
    data = res.json()
    if "access_token" not in data:
        raise ValueError(f"토큰 발급 실패: {data.get('error_description', data)}")
    return data["access_token"]


def get_stock_price(stock_code: str) -> dict:
    token = get_access_token(APP_KEY, APP_SECRET)
    res = requests.get(
        "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price",
        headers={
            "content-type":  "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey":        APP_KEY,
            "appsecret":     APP_SECRET,
            "tr_id":         "FHKST01010100",
            "custtype":      "P",
        },
        params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code.zfill(6)},
        timeout=10,
    )
    st.session_state["_last_status"] = res.status_code
    st.session_state["_last_body"]   = res.text[:400]
    res.raise_for_status()
    data = res.json()
    if data.get("rt_cd") != "0":
        raise ValueError(f"[{data.get('msg_cd')}] {data.get('msg1', 'API 오류')}")
    return data["output"]


# ── 헬퍼 함수 ────────────────────────────────────────────────────────────────
def fmt_num(val, suffix=""):
    try:
        n = float(val)
        if abs(n) >= 1_000_000_000_000: return f"{n/1_000_000_000_000:.2f}조{suffix}"
        if abs(n) >= 100_000_000:       return f"{n/100_000_000:.0f}억{suffix}"
        return f"{int(n):,}{suffix}"
    except: return val or "-"

def color_class(val):
    try: return "up" if float(val) > 0 else ("down" if float(val) < 0 else "flat")
    except: return "flat"

def arrow(val):
    try: v = float(val); return "▲" if v > 0 else ("▼" if v < 0 else "")
    except: return ""

def safe_int(v):
    try: return f"{int(float(v)):,}원"
    except: return "-"


# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:2.5px solid #0f172a; padding-bottom:14px; margin-bottom:20px;">
    <div style="font-size:0.7rem; font-weight:800; letter-spacing:0.25em; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">KIS DEVELOPERS</div>
    <div style="font-family:'Bebas Neue',sans-serif; font-size:2.4rem; letter-spacing:0.05em; color:#0f172a; line-height:1;">국내 주식 종목 조회</div>
</div>
""", unsafe_allow_html=True)

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
if "selected_code" not in st.session_state: st.session_state["selected_code"] = None
if "selected_name" not in st.session_state: st.session_state["selected_name"] = None

# ── 검색창 ───────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input(
        "종목명",
        placeholder="종목명을 입력하세요  예) 삼성전자  /  카카오  /  SK하이닉스",
        label_visibility="collapsed",
        key="search_query",
    )
with col_btn:
    search_btn = st.button("🔍 조회", use_container_width=True)

# ── 실시간 후보 표시 ──────────────────────────────────────────────────────────
if query.strip() and not search_btn:
    candidates = search_stocks(query)
    if candidates:
        st.markdown("**검색 결과** — 선택 버튼을 눌러 시세를 조회하세요.")
        for item in candidates:
            c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
            with c1: st.write(f"**{item['name']}**")
            with c2: st.caption(item["code"])
            with c3:
                market = item.get("market", "KRX")
                badge_cls = f"badge-{market}" if market in ["KOSPI","KOSDAQ"] else "badge-KRX"
                st.markdown(f'<span class="market-badge {badge_cls}">{market}</span>', unsafe_allow_html=True)
            with c4:
                if st.button("선택", key=f"sel_{item['code']}"):
                    st.session_state["selected_code"] = item["code"]
                    st.session_state["selected_name"] = item["name"]
                    st.rerun()
    else:
        st.caption(f"**'{query}'** 에 해당하는 종목이 없습니다.")

# ── 🔍 버튼: 첫 번째 후보 자동 선택 ─────────────────────────────────────────
if search_btn and query.strip():
    candidates = search_stocks(query, limit=1)
    if candidates:
        st.session_state["selected_code"] = candidates[0]["code"]
        st.session_state["selected_name"] = candidates[0]["name"]
    else:
        st.warning(f"**'{query}'** 에 해당하는 종목을 찾을 수 없습니다.")

# ── 시세 조회 및 출력 ─────────────────────────────────────────────────────────
if st.session_state["selected_code"]:
    stock_code = st.session_state["selected_code"]
    stock_name = st.session_state["selected_name"]

    with st.spinner(f"**{stock_name} ({stock_code})** 시세를 조회 중..."):
        try:
            output = get_stock_price(stock_code)
        except requests.exceptions.HTTPError:
            status = st.session_state.get("_last_status", "?")
            body   = st.session_state.get("_last_body", "")
            st.error(f"❌ HTTP {status} 오류")
            with st.expander("🔍 상세 오류"):
                st.code(body)
            st.stop()
        except ValueError as e:
            st.error(f"❌ {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ 오류: {e}")
            st.stop()

    display_name  = output.get("hts_kor_isnm", stock_name)
    sector_name   = output.get("bstp_kor_isnm", "").strip()

    # Supabase에서 업종/주요제품 조회
    _master = supabase.table("stock_master").select("sector, product").eq("code", stock_code).limit(1).execute().data
    db_sector  = (_master[0].get("sector",  "") or "").strip() if _master else ""
    db_product = (_master[0].get("product", "") or "").strip() if _master else ""
    # KIS 업종명이 있으면 우선 사용, 없으면 Supabase 값 사용
    sector_label  = sector_name or db_sector
    product_label = db_product
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
    market_cap   = output.get("hts_avls", "0")

    cc = color_class(change_pct)
    ar = arrow(change_pct)

    sector_html = f'<span class="sector-badge">🏭 {sector_label}</span>' if sector_label else ""
    # 주요제품 쉼표 기준으로 분리해 개별 뱃지 생성
    product_badges = "".join(
        f'<span class="sector-badge">📦 {p.strip()}</span>'
        for p in product_label.split(",") if p.strip()
    ) if product_label else ""
    st.markdown(f"""
    <div class="stock-banner">
        <div class="sname">{display_name}</div>
        <div class="scode">KRX &nbsp;·&nbsp; {stock_code}</div>
        <div style="margin-top:10px;">
            <span class="sbadge">국내주식</span>
            {sector_html}
            {product_badges}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">📌 핵심 지표</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        try:   delta_str = f"{ar} {abs(float(change_pct))}% ({int(float(change_price)):+,}원)"
        except: delta_str = "-"
        st.metric("현재가", f"{int(float(curr_price)):,}원", delta=delta_str,
                  delta_color="normal" if float(change_pct) >= 0 else "inverse")
    with c2: st.metric("거래량", fmt_num(volume, "주"))
    with c3: st.metric("거래대금", fmt_num(trade_amt, "원"))

    st.markdown('<div class="section-label">📋 상세 정보</div>', unsafe_allow_html=True)
    left, right = st.columns(2)

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
        try:   mktcap_str = fmt_num(str(int(float(market_cap)) * 100_000_000), "원")
        except: mktcap_str = "-"
        st.markdown(f"""
        <div class="info-box">
            <div class="info-row"><span class="info-key">시가총액</span><span class="info-val">{mktcap_str}</span></div>
            <div class="info-row"><span class="info-key">PER</span><span class="info-val">{per}배</span></div>
            <div class="info-row"><span class="info-key">PBR</span><span class="info-val">{pbr}배</span></div>
            <div class="info-row"><span class="info-key">전일 대비</span><span class="info-val {cc}">{ar} {safe_int(change_price)}</span></div>
            <div class="info-row"><span class="info-key">등락률</span><span class="info-val {cc}">{ar} {abs(float(change_pct))}%</span></div>
        </div>
        """, unsafe_allow_html=True)

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#cbd5e1; font-size:0.72rem; margin-top:32px;
            padding-top:16px; border-top:1px solid #e2e8f0;">
    데이터 출처: 한국투자증권 KIS Developers · KIND KRX &nbsp;·&nbsp; 투자 참고용이며 실제 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)