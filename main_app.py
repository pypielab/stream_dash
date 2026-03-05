import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

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


# ── 데이터 로딩 ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)  # 5분 캐시
def get_market_data():
    items = {
        "KOSPI":   "^KS11",
        "KOSDAQ":  "^KQ11",
        "NASDAQ":  "^IXIC",
        "S&P 500": "^GSPC",
        "USD/KRW": "USDKRW=X",
        "JPY/KRW": "JPYKRW=X",
        "Gold":    "GC=F",
        "Bitcoin": "BTC-KRW",
    }

    usd_krw_ticker = yf.Ticker("USDKRW=X")
    current_exchange_rate = usd_krw_ticker.fast_info["last_price"]

    results = []
    for name, ticker_symbol in items.items():
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.fast_info

        last_price = float(info["last_price"])
        prev_close = float(info["previous_close"])
        display_name = name

        if name == "JPY/KRW":
            last_price *= 100
            prev_close *= 100
        elif name == "Gold":
            oz_to_don = 3.75 / 31.1035
            last_price = last_price * oz_to_don * current_exchange_rate
            prev_close = prev_close * oz_to_don * current_exchange_rate
            display_name = "금(1돈)"

        change_pct = round(((last_price - prev_close) / prev_close) * 100, 2)

        results.append({
            "name":   display_name,
            "price":  round(last_price, 1) if name == "Bitcoin" else round(last_price, 2),
            "change": change_pct,
        })
    return results


# ── 헤더 ─────────────────────────────────────────────────────────────────────
days_ko = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
now = datetime.now()
date_str = now.strftime(f"%Y년 %m월 %d일 {days_ko[now.weekday()]}")

col_title, col_btn = st.columns([7, 1])
with col_title:
    st.markdown(f"""
    <div style="border-bottom:2.5px solid #0f172a; padding-bottom:14px; margin-bottom:4px;">
        <div style="font-size:0.7rem; font-weight:800; letter-spacing:0.25em; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">
            MARKET REPORT
        </div>
        <div style="font-family:'Bebas Neue',sans-serif; font-size:2.6rem; letter-spacing:0.05em; color:#0f172a; line-height:1;">
            {date_str}
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_btn:
    st.write("")
    st.write("")
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── 데이터 fetch ──────────────────────────────────────────────────────────────
with st.spinner("시장 데이터를 불러오는 중..."):
    all_data = get_market_data()

indices = all_data[:4]
forex   = all_data[4:6]
assets  = all_data[6:]


# ── 헬퍼: metric 렌더링 ───────────────────────────────────────────────────────
def render_metrics(data_list, cols):
    for col, item in zip(cols, data_list):
        arrow = "▲" if item["change"] > 0 else "▼"
        delta_color = "normal" if item["change"] > 0 else "inverse"
        with col:
            st.metric(
                label=item["name"],
                value=f"{item['price']:,}",
                delta=f"{arrow} {abs(item['change'])}%",
                delta_color=delta_color,
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
    yaxis=dict(ticksuffix="%", tickfont=dict(size=11, color="#94a3b8"), gridcolor="#e2e8f0", zeroline=True, zerolinecolor="#cbd5e1", zerolinewidth=1.5),
    bargap=0.35,
)
st.plotly_chart(fig, use_container_width=True)

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#cbd5e1; font-size:0.72rem; margin-top:8px; padding-top:16px; border-top:1px solid #e2e8f0;">
    데이터 출처: Yahoo Finance &nbsp;·&nbsp; 5분 자동 캐시 &nbsp;·&nbsp; 투자 참고용 정보이며 실제 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)