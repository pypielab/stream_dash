import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client

st.set_page_config(
    page_title="Market Dashboard",
    page_icon="📈",
    layout="wide",
)

# ── 전역 스타일 ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;600;800&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #f0f2f5; }
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 20px 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s;
}
[data-testid="metric-container"]:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.10); }
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.12em !important;
    color: #94a3b8 !important;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2rem !important;
    color: #0f172a !important;
    letter-spacing: 0.03em;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"] > div { font-size: 0.82rem !important; font-weight: 700 !important; }

.section-label {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #94a3b8;
    margin: 24px 0 8px 2px;
}
.stButton > button {
    background: #0f172a;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 0.5rem 1.5rem;
    transition: background 0.2s;
}
.stButton > button:hover { background: #1e3a5f; }
</style>
""", unsafe_allow_html=True)


# ── Supabase 클라이언트 ───────────────────────────────────────────────────────
# .streamlit/secrets.toml 에 아래 내용을 추가하세요:
#
#   [supabase]
#   url = "https://xxxxxxxxxxxx.supabase.co"
#   key = "your-anon-public-key"
#
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )

supabase = get_supabase()


# ── Yahoo Finance → Supabase 저장 ─────────────────────────────────────────────
ITEMS = {
    "KOSPI":   "^KS11",
    "KOSDAQ":  "^KQ11",
    "NASDAQ":  "^IXIC",
    "S&P 500": "^GSPC",
    "USD/KRW": "USDKRW=X",
    "JPY/KRW": "JPYKRW=X",
    "Gold":    "GC=F",
    "Bitcoin": "BTC-KRW",
}

# ITEMS 순서 기준 정렬 키
DISPLAY_ORDER = ["KOSPI", "KOSDAQ", "NASDAQ", "S&P 500", "USD/KRW", "JPY/KRW", "금(1돈)", "Bitcoin"]


def fetch_and_save():
    """Yahoo Finance에서 시세를 가져와 Supabase에 upsert."""
    usd_krw_ticker = yf.Ticker("USDKRW=X")
    current_exchange_rate = usd_krw_ticker.fast_info["last_price"]

    rows = []
    now_iso = datetime.utcnow().isoformat()

    for name, ticker_symbol in ITEMS.items():
        ticker  = yf.Ticker(ticker_symbol)
        info    = ticker.fast_info

        last_price  = float(info["last_price"])
        prev_close  = float(info["previous_close"])
        display_name = name

        if name == "JPY/KRW":
            last_price *= 100
            prev_close *= 100
        elif name == "Gold":
            oz_to_don    = 3.75 / 31.1035
            last_price   = last_price * oz_to_don * current_exchange_rate
            prev_close   = prev_close * oz_to_don * current_exchange_rate
            display_name = "금(1돈)"

        change_pct = round(((last_price - prev_close) / prev_close) * 100, 2)

        rows.append({
            "name":       display_name,
            "price":      round(last_price, 1) if name == "Bitcoin" else round(last_price, 2),
            "change_pct": change_pct,
            "updated_at": now_iso,
        })

    supabase.table("market_data").upsert(rows, on_conflict="name").execute()


def load_from_supabase():
    """Supabase에서 market_data 전체 조회 후 정해진 순서로 반환."""
    res  = supabase.table("market_data").select("*").execute()
    rows = res.data

    row_map = {r["name"]: r for r in rows}
    return [
        {
            "name":   name,
            "price":  row_map[name]["price"],
            "change": row_map[name]["change_pct"],
        }
        for name in DISPLAY_ORDER
        if name in row_map
    ]


# ── 헤더 ─────────────────────────────────────────────────────────────────────
days_ko  = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
now      = datetime.now()
date_str = now.strftime(f"%Y년 %m월 %d일 {days_ko[now.weekday()]}")

col_title, col_btn = st.columns([7, 1])
with col_title:
    st.markdown(f"""
    <div style="border-bottom:2.5px solid #0f172a; padding-bottom:14px; margin-bottom:4px;">
        <div style="font-size:0.7rem; font-weight:800; letter-spacing:0.25em; color:#94a3b8;
                    text-transform:uppercase; margin-bottom:4px;">MARKET REPORT</div>
        <div style="font-family:'Bebas Neue',sans-serif; font-size:2.6rem;
                    letter-spacing:0.05em; color:#0f172a; line-height:1;">{date_str}</div>
    </div>
    """, unsafe_allow_html=True)

with col_btn:
    st.write("")
    st.write("")
    refresh = st.button("🔄 시세 갱신", use_container_width=True)


# ── 새로고침: Yahoo → Supabase 저장 ──────────────────────────────────────────
if refresh:
    with st.spinner("Yahoo Finance에서 최신 시세를 가져오는 중..."):
        try:
            fetch_and_save()
            st.success("✅ 시세가 업데이트되었습니다.")
        except Exception as e:
            st.error(f"❌ 데이터 갱신 실패: {e}")
            st.stop()
    st.rerun()


# ── Supabase에서 즉시 로드 ────────────────────────────────────────────────────
try:
    all_data = load_from_supabase()
except Exception as e:
    st.error(f"❌ Supabase 데이터 로드 실패: {e}")
    st.stop()

if not all_data:
    st.warning("⚠️ 저장된 데이터가 없습니다. **🔄 시세 갱신** 버튼을 눌러 처음 데이터를 불러오세요.")
    st.stop()

# 마지막 업데이트 시각
try:
    last_updated_raw = (
        supabase.table("market_data")
        .select("updated_at")
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
        .data[0]["updated_at"]
    )
    last_dt = datetime.fromisoformat(last_updated_raw.replace("Z", "+00:00"))
    st.caption(f"🕐 마지막 업데이트: {last_dt.strftime('%Y-%m-%d %H:%M')} UTC")
except Exception:
    pass

indices = all_data[:4]
forex   = all_data[4:6]
assets  = all_data[6:]


# ── 헬퍼: metric 렌더링 ───────────────────────────────────────────────────────
def render_metrics(data_list, cols):
    for col, item in zip(cols, data_list):
        arrow = "▲" if item["change"] > 0 else "▼"
        with col:
            st.metric(
                label=item["name"],
                value=f"{item['price']:,}",
                delta=f"{arrow} {abs(item['change'])}%",
                delta_color="normal" if item["change"] > 0 else "inverse",
            )


# ── 섹션 1: 주요 지수 ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label">📊 주요 지수 현황</div>', unsafe_allow_html=True)
render_metrics(indices, st.columns(4))

# ── 섹션 2: 환율 + 대체자산 ──────────────────────────────────────────────────
col_fx, col_asset = st.columns(2)
with col_fx:
    st.markdown('<div class="section-label">💱 실시간 환율 (원)</div>', unsafe_allow_html=True)
    render_metrics(forex, st.columns(2))
with col_asset:
    st.markdown('<div class="section-label">🪙 대체 자산 (원화 기준)</div>', unsafe_allow_html=True)
    render_metrics(assets, st.columns(2))

# ── 섹션 3: 변동폭 차트 ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">📉 시장 등락 변동폭 (%)</div>', unsafe_allow_html=True)

chart_names   = [item["name"] for item in all_data]
chart_changes = [item["change"] for item in all_data]
bar_colors    = ["#ef4444" if v > 0 else "#3b82f6" for v in chart_changes]
text_labels   = [f"{'▲' if v > 0 else '▼'} {abs(v)}%" for v in chart_changes]

fig = go.Figure(go.Bar(
    x=chart_names,
    y=chart_changes,
    marker_color=bar_colors,
    text=text_labels,
    textposition="outside",
    textfont=dict(size=12, family="Noto Sans KR", color="#0f172a"),
    hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
))
fig.update_layout(
    height=340,
    margin=dict(t=30, b=10, l=0, r=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    xaxis=dict(tickfont=dict(size=12, family="Noto Sans KR", color="#334155"), showgrid=False, zeroline=False),
    yaxis=dict(ticksuffix="%", tickfont=dict(size=11, color="#94a3b8"), gridcolor="#e2e8f0",
               zeroline=True, zerolinecolor="#cbd5e1", zerolinewidth=1.5),
    bargap=0.35,
)
st.plotly_chart(fig, use_container_width=True)

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#cbd5e1; font-size:0.72rem; margin-top:8px;
            padding-top:16px; border-top:1px solid #e2e8f0;">
    데이터 출처: Yahoo Finance &nbsp;·&nbsp; Supabase &nbsp;·&nbsp;
    투자 참고용 정보이며 실제 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)