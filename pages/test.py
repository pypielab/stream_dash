import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="종목 상세",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 🎨 스타일 (Modern Dark Glassmorphism) ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', 'Noto Sans KR', sans-serif; 
}
.stApp {
    background-color: #03080b;
    background-image: radial-gradient(ellipse at top, #072023 0%, #03080b 80%);
    color: #f1f5f9;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(45, 212, 191, 0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(45, 212, 191, 0.4); }

.glass-panel {
    background: rgba(6, 20, 24, 0.6);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(45, 212, 191, 0.12);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.glass-title {
    font-family: 'Inter', 'Noto Sans KR', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    color: #cbd5e1;
    letter-spacing: 0.02em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.glass-metric-val {
    font-family: 'Inter', sans-serif;
    font-size: 2.1rem;
    font-weight: 600;
    color: #ffffff;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.glass-metric-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 6px;
}
.pos { color: #10b981; } /* Emerald Green */
.neg { color: #ef4444; } /* Soft Red */

.guru-bg {
    background: rgba(45, 212, 191, 0.04);
    border-left: 2px solid #2dd4bf;
    padding: 20px;
    margin-bottom: 24px;
    border-radius: 0 4px 4px 0;
}
.guru-quote {
    font-style: italic;
    font-size: 1.05rem;
    color: #e2e8f0;
    line-height: 1.6;
}
.guru-author {
    text-align: right;
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 12px;
}

.news-item {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.news-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}
.news-title {
    font-family: 'Inter', 'Noto Sans KR', sans-serif;
    font-size: 0.9rem;
    color: #f1f5f9;
    font-weight: 500;
    margin-bottom: 6px;
    cursor: pointer;
    transition: color 0.2s;
}
.news-title:hover { color: #2dd4bf; }
.news-meta {
    font-size: 0.75rem;
    color: #64748b;
    font-family: 'Inter', sans-serif;
}

/* Custom progress bar override for financials */
.stProgress > div > div > div > div { background-color: #2dd4bf; }

/* Headers override */
h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #ffffff !important; font-weight: 600 !important; }

/* Sidebar adjustments */
[data-testid="stSidebar"] {
    background-color: #03080b !important;
    border-right: 1px solid rgba(45, 212, 191, 0.08);
}

/* Input boxes inline subtle style */
.stTextInput > div > div > input, .stSelectbox > div > div {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #f8fafc !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 6px !important;
}
.stTextInput > div > div > input:focus, .stSelectbox > div > div:focus {
    border-color: #2dd4bf !important;
    box-shadow: 0 0 0 1px #2dd4bf !important;
}

</style>
""", unsafe_allow_html=True)

# ── ⚙️ 사이드바 & 종목 선택 ────────────────────────────────────────────────────────
st.sidebar.markdown("<h2 style='color:white;'>🔍 Search Option</h2>", unsafe_allow_html=True)
ticker_symbol = st.sidebar.text_input("종목 티커 (예: AAPL, TSLA, 005930.KS)", "AAPL").upper()
period = st.sidebar.selectbox("기간", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="6mo"):
    t = yf.Ticker(ticker)
    hist = t.history(period=period)
    info = t.info
    return hist, info

# 데이터 로드
try:
    with st.spinner("데이터를 불러오는 중..."):
        df, info = get_stock_data(ticker_symbol, period)
        if df.empty:
            st.error("데이터를 찾을 수 없습니다. 올바른 티커를 입력해주세요.")
            st.stop()
except Exception as e:
    st.error(f"오류 발생: {e}")
    st.stop()


# ── 📌 종목 헤더 ────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

current_price = df['Close'].iloc[-1]
prev_price = df['Close'].iloc[-2]
change = current_price - prev_price
change_pct = (change / prev_price) * 100
color_class = "pos" if change >= 0 else "neg"
arrow = "▲" if change >= 0 else "▼"

with col1:
    st.markdown(f"""
    <div style="margin-bottom: 30px;">
        <div style="font-size:1rem; color:#94a3b8; font-weight:600; letter-spacing:0.1em; margin-bottom:4px;">
            {info.get('sector', 'N/A')} • {info.get('industry', 'N/A')}
        </div>
        <div style="font-family:'Poppins', sans-serif; font-size:3.5rem; font-weight:800; color:#ffffff; line-height:1;">
            {info.get('shortName', ticker_symbol)} <span style="font-size:1.5rem; color:#64748b; font-weight:500;">{ticker_symbol}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="text-align:right; margin-bottom: 30px;">
        <div class="glass-metric-val">${current_price:,.2f}</div>
        <div class="glass-metric-sub {color_class}">
            {arrow} {abs(change):.2f} ({abs(change_pct):.2f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── 📈 캔들차트 & 📊 수급정보 레이아웃 ──────────────────────────────────────────────
col_chart, col_side = st.columns([7, 3])

with col_chart:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="glass-title">📈 Candlestick Chart</div>', unsafe_allow_html=True)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444'
    )])
    
    fig.update_layout(
        height=450,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False, 
            color='#94a3b8',
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.05)', 
            color='#94a3b8'
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_side:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="glass-title">⚖️ 수급 및 거래 정보</div>', unsafe_allow_html=True)
    
    avg_vol = info.get('averageVolume', 0)
    vol = info.get('volume', df['Volume'].iloc[-1])
    vol_pct = (vol / avg_vol * 100) if avg_vol else 0
    
    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:4px;">당일 거래량 (Volume)</div>
        <div style="color:#ffffff; font-size:1.4rem; font-weight:700;">{int(vol):,}</div>
        <div style="color:#64748b; font-size:0.75rem;">평균 거래량 대비 {vol_pct:.1f}%</div>
    </div>
    <div style="margin-bottom:20px;">
        <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:4px;">시가총액 (Market Cap)</div>
        <div style="color:#ffffff; font-size:1.4rem; font-weight:700;">${info.get('marketCap', 0) / 1e9:,.1f}B</div>
    </div>
    <div style="margin-bottom:20px;">
        <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:4px;">52주 최고/최저</div>
        <div style="color:#ffffff; font-size:1.1rem; font-weight:600;">
            <span style="color:#10b981;">{info.get('fiftyTwoWeekHigh', 'N/A')}</span> / 
            <span style="color:#ef4444;">{info.get('fiftyTwoWeekLow', 'N/A')}</span>
        </div>
    </div>
    <div style="margin-bottom:10px;">
        <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:4px;">기관 기관보유 비중</div>
        <div style="color:#ffffff; font-size:1.4rem; font-weight:700;">{info.get('heldPercentInstitutions', 0)*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(info.get('heldPercentInstitutions', 0))
    st.markdown('</div>', unsafe_allow_html=True)


# ── 💡 거장의 한줄평 & 🏢 재무/배당 정보 ──────────────────────────────────────────────
col_guru, col_fin = st.columns([1, 1])

with col_guru:
    st.markdown('<div class="glass-panel" style="height: 100%;">', unsafe_allow_html=True)
    st.markdown('<div class="glass-title">🧠 투자 거장들의 한줄평</div>', unsafe_allow_html=True)
    
    quotes = [
        {"q": "주식 시장은 인내심 없는 사람의 돈을 인내심 있는 사람에게 이동시키는 도구이다.", "a": "워런 버핏 (Warren Buffett)"},
        {"q": "당신이 약간의 상상력을 가졌다면, 당신은 시장이 내리는 가격에 동의하지 않을 것이다.", "a": "피터 린치 (Peter Lynch)"},
        {"q": "가장 중요한 투자의 원칙은 첫째, 돈을 잃지 않는 것이고, 둘째는 첫째 원칙을 잊지 않는 것이다.", "a": "워런 버핏 (Warren Buffett)"},
        {"q": "강세장은 비관 속에서 태어나 회의 속에서 자라며 낙관 속에서 성숙해 행복 속에서 죽는다.", "a": "존 템플턴 (John Templeton)"}
    ]
    selected_quote = random.choice(quotes)
    
    st.markdown(f"""
    <div class="guru-bg">
        <div class="guru-quote">"{selected_quote['q']}"</div>
        <div class="guru-author">- {selected_quote['a']}</div>
    </div>
    <div style="color:#94a3b8; font-size:0.85rem; line-height:1.5; margin-top:16px;">
        * {ticker_symbol} 종목의 현재 밸류에이션 점검: 
        현재 PER은 <b>{info.get('trailingPE', 'N/A')}</b>, PBR은 <b>{info.get('priceToBook', 'N/A')}</b> 수준으로 거래되고 있습니다. 거장들의 조언을 바탕으로 장기적인 내재 가치를 평가해 보세요.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_fin:
    st.markdown('<div class="glass-panel" style="height: 100%;">', unsafe_allow_html=True)
    st.markdown('<div class="glass-title">📊 핵심 재무 및 배당 (Financials & Dividends)</div>', unsafe_allow_html=True)
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown(f"""
        <div style="margin-bottom:16px;">
            <div style="color:#94a3b8; font-size:0.8rem;">Trailing P/E</div>
            <div style="color:#fff; font-size:1.3rem; font-weight:600;">{info.get('trailingPE', 'N/A')}</div>
        </div>
        <div style="margin-bottom:16px;">
            <div style="color:#94a3b8; font-size:0.8rem;">EPS (TTM)</div>
            <div style="color:#fff; font-size:1.3rem; font-weight:600;">${info.get('trailingEps', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_f2:
        st.markdown(f"""
        <div style="margin-bottom:16px;">
            <div style="color:#94a3b8; font-size:0.8rem;">ROE</div>
            <div style="color:#fff; font-size:1.3rem; font-weight:600;">{info.get('returnOnEquity', 0)*100:.2f}%</div>
        </div>
        <div style="margin-bottom:16px;">
            <div style="color:#94a3b8; font-size:0.8rem;">Price to Book (PBR)</div>
            <div style="color:#fff; font-size:1.3rem; font-weight:600;">{info.get('priceToBook', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr style="border-color: rgba(255,255,255,0.1); margin:16px 0;">', unsafe_allow_html=True)
    
    div_yield = info.get('dividendYield', 0)
    div_rate = info.get('dividendRate', 0)
    
    if div_yield:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#94a3b8; font-size:0.85rem; font-weight:600;">배당 수익률 (Dividend Yield)</div>
                <div style="color:#10b981; font-size:1.8rem; font-weight:800; font-family:'Poppins', sans-serif;">{div_yield*100:.2f}%</div>
                <div style="color:#64748b; font-size:0.8rem;">연간 배당금: ${div_rate}</div>
            </div>
            <div style="text-align:right;">
                <div style="padding: 8px 16px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2); color:#10b981; font-size:0.9rem; font-weight:600;">
                    배당 지급 종목
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="color:#94a3b8; font-size:0.9rem; font-weight:500; text-align:center; padding: 20px 0;">
            해당 종목은 배당을 지급하지 않거나 관련 정보가 없습니다.
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)


# ── 📰 뉴스 섹션 (종목 뉴스 & 산업 뉴스) ──────────────────────────────────────────────
col_news1, col_news2 = st.columns(2)

# 가상 뉴스 데이터 생성 함수
def generate_mock_news(ticker, is_industry=False):
    topics = ["실적 발표", "신기술 도입", "경영진 변경", "시장 점유율 확대", "M&A 이슈"] if not is_industry else ["규제 완화 논의", "글로벌 공급망 불균형", "ESG 트렌드 확산", "AI 도입 가속화", "금리 인상 여파"]
    company_name = info.get('shortName', ticker)
    news = []
    for i in range(4):
        topic = random.choice(topics)
        time_ago = random.randint(1, 24)
        if is_industry:
            title = f"[산업] {info.get('sector', '해당 산업')} 섹터, {topic}에 따른 향후 전망 분석"
            src = "글로벌 인더스트리 데일리"
        else:
            title = f"{company_name}, {topic} 소식에 주가 변동성 확대"
            src = "마켓 워치 커스텀"
        
        news.append(f"""
        <div class="news-item">
            <div class="news-title">{title}</div>
            <div class="news-meta">{src} · {time_ago}시간 전</div>
        </div>
        """)
    return "".join(news)

with col_news1:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="glass-title">🗞️ 종목 뉴스 (Company News)</div>', unsafe_allow_html=True)
    st.markdown(generate_mock_news(ticker_symbol), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_news2:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="glass-title">🏭 관련 산업 뉴스 (Industry News)</div>', unsafe_allow_html=True)
    st.markdown(generate_mock_news(ticker_symbol, is_industry=True), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top:20px; font-size:0.8rem; color:#64748b;">
    © 2026 Stream Dash. Data provided by YFinance. <br>
    This dashboard relies on simulated news and historical metrics for demonstration purposes.
</div>
""", unsafe_allow_html=True)
