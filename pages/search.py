import os
import json
import collections
import streamlit as st
import google.generativeai as genai
from supabase import create_client

st.set_page_config(page_title="US Index RAG", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');
:root{--bg:#0a0a0f;--surface:#111118;--surface2:#18181f;--border:#2a2a35;--accent:#00ff88;--accent2:#0088ff;--text:#e8e8f0;--muted:#6b6b80;}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;font-family:'Syne',sans-serif;color:var(--text);}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important;}
.rag-header{display:flex;align-items:baseline;gap:12px;padding:28px 0 8px;border-bottom:1px solid var(--border);margin-bottom:24px;}
.rag-title{font-size:2rem;font-weight:800;letter-spacing:-0.03em;background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.rag-sub{font-family:'DM Mono',monospace;font-size:0.75rem;color:var(--muted);letter-spacing:0.1em;}
.msg-user{background:var(--surface2);border:1px solid var(--border);border-radius:12px 12px 4px 12px;padding:14px 18px;margin:10px 0;font-size:0.95rem;line-height:1.6;max-width:80%;margin-left:auto;color:var(--text);}
.msg-assistant{background:linear-gradient(135deg,#111820,#0f1a12);border:1px solid #1a3a25;border-left:3px solid var(--accent);border-radius:4px 12px 12px 12px;padding:14px 18px;margin:10px 0;font-size:0.95rem;line-height:1.7;max-width:90%;color:var(--text);}
.query-box{background:var(--surface2);border:1px solid var(--border);border-top:2px solid var(--accent2);border-radius:8px;padding:10px 14px;margin:6px 0 14px;font-family:'DM Mono',monospace;font-size:0.72rem;color:var(--muted);}
.query-label{color:var(--accent2);font-size:0.68rem;letter-spacing:0.12em;font-weight:500;margin-bottom:6px;}
.stat-row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;}
.stat-badge{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:6px 12px;font-family:'DM Mono',monospace;font-size:0.72rem;color:var(--muted);}
.stat-badge span{color:var(--accent);font-weight:500;}
[data-testid="stChatInput"] textarea{background:var(--surface2)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:10px!important;}
[data-testid="stChatInput"] textarea:focus{border-color:var(--accent)!important;}
.stButton button{background:var(--surface2)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:8px!important;}
.stButton button:hover{border-color:var(--accent)!important;color:var(--accent)!important;}
</style>
""", unsafe_allow_html=True)

# ── 클라이언트 초기화 ─────────────────────────────────────────────────────────
@st.cache_resource
def init_clients():
    sb = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    genai.configure(api_key=st.secrets["gemini"]["key"])
    return sb

sb = init_clients()

# ── Gemini 호출 헬퍼 ──────────────────────────────────────────────────────────
def call_llm(messages: list, temperature: float = 0.4, max_tokens: int = 2048) -> str:
    model = genai.GenerativeModel(
        model_name="models/gemini-2.5-flash",
        generation_config=genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
    )
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    system_text = "\n\n".join(system_parts)
    non_system = [m for m in messages if m["role"] != "system"]

    history = []
    for m in non_system[:-1]:
        role = "model" if m["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [m["content"]]})

    last_msg = non_system[-1]["content"] if non_system else ""
    full_prompt = (system_text + "\n\n" + last_msg) if system_text else last_msg

    chat = model.start_chat(history=history)
    return chat.send_message(full_prompt).text

# ── Step 1. 쿼리 파라미터 추출 ────────────────────────────────────────────────
EXTRACT_PROMPT = """당신은 주식 DB 쿼리 파라미터 추출기입니다. JSON으로만 응답하세요.

DB 컬럼:
- exchange: "NYSE" | "Nasdaq"
- sector: Technology, Healthcare, Financials, Energy, Consumer Discretionary,
  Industrials, Communication Services, Consumer Staples, Utilities, Real Estate, Materials
- market_cap: 시가총액 USD (BIGINT)
- ceo: CEO 이름
- in_sp500 / in_ndx100 / in_dow30: BOOLEAN

응답 JSON:
{
  "sectors": [],
  "exchanges": [],
  "in_sp500": null,
  "in_ndx100": null,
  "in_dow30": null,
  "order_by": "market_cap",
  "order_desc": true,
  "limit": 20,
  "keyword": "",
  "aggregate": null
}

aggregate: "sector_count" | "exchange_count" | null
집계성 질문(섹터별/몇개/분포/전체)이면 limit=500, aggregate 설정"""

def extract_query_params(user_question: str, history: list) -> dict:
    messages = [{"role": "system", "content": EXTRACT_PROMPT}]
    for h in history[-4:]:
        if h["role"] in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_question})
    raw = call_llm(messages, temperature=0.0, max_tokens=512)
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])

# ── Step 2. Supabase 조회 ─────────────────────────────────────────────────────
def fetch_by_params(params: dict) -> list:
    q = sb.table("us_basic_info").select(
        "code,name,exchange,sector,market_cap,ceo,in_sp500,in_ndx100,in_dow30"
    ).eq("is_delisted", False)

    if params.get("sectors"):
        q = q.in_("sector", params["sectors"])
    if params.get("exchanges"):
        q = q.in_("exchange", params["exchanges"])
    if params.get("in_sp500") is True:
        q = q.eq("in_sp500", True)
    if params.get("in_ndx100") is True:
        q = q.eq("in_ndx100", True)
    if params.get("in_dow30") is True:
        q = q.eq("in_dow30", True)
    if params.get("keyword"):
        kw = params["keyword"]
        q = q.or_(f"name.ilike.%{kw}%,code.ilike.%{kw}%")

    limit = min(int(params.get("limit", 20)), 500)
    return (q.order(params.get("order_by", "market_cap"), desc=params.get("order_desc", True))
             .limit(limit).execute().data or [])

# ── Step 3. 컨텍스트 생성 ─────────────────────────────────────────────────────
def build_context(stocks: list, params: dict) -> str:
    if not stocks:
        return "조건에 맞는 종목이 없습니다."
    lines = [
        f"[필터] 섹터={params.get('sectors') or '전체'} | 결과={len(stocks)}개", "",
        f"{'티커':<8} {'회사명':<30} {'거래소':<7} {'섹터':<25} {'시총(USD)':<18} {'CEO':<22} SP5 NDX DOW",
        "-" * 120,
    ]
    for s in stocks:
        cap = f"${s['market_cap']:,.0f}" if s.get("market_cap") else "N/A"
        lines.append(
            f"{s['code']:<8} {(s['name'] or '')[:28]:<30} {(s['exchange'] or ''):<7}"
            f" {(s['sector'] or '')[:23]:<25} {cap:<18} {(s['ceo'] or '')[:20]:<22}"
            f" {'V' if s['in_sp500'] else ' '}   {'V' if s['in_ndx100'] else ' '}   {'V' if s['in_dow30'] else ' '}"
        )
    return "\n".join(lines)

def aggregate_context(stocks: list, params: dict) -> str:
    agg_type = params.get("aggregate")
    total = len(stocks)

    if agg_type == "sector_count":
        counter = collections.Counter(s.get("sector") or "Unknown" for s in stocks)
        lines = [f"[섹터별 종목 수 - 총 {total}개]"]
        for sector, cnt in sorted(counter.items(), key=lambda x: -x[1]):
            lines.append(f"  {sector}: {cnt}개")
        return "\n".join(lines)

    elif agg_type == "exchange_count":
        counter = collections.Counter(s.get("exchange") or "Unknown" for s in stocks)
        lines = [f"[거래소별 종목 수 - 총 {total}개]"]
        for ex, cnt in sorted(counter.items(), key=lambda x: -x[1]):
            lines.append(f"  {ex}: {cnt}개")
        return "\n".join(lines)

    return build_context(stocks[:30], params) + (
        f"\n\n총 {total}개 중 상위 30개만 표시" if total > 30 else ""
    )

# ── Step 4. 답변 생성 ─────────────────────────────────────────────────────────
ANSWER_PROMPT = """당신은 미국 주식 시장 전문 애널리스트입니다.
제공된 종목 데이터를 기반으로 사용자 질문에 한국어로 답변하세요.
- 데이터에 없는 정보는 추측하지 마세요
- 티커를 항상 언급하세요
- 시가총액은 $B(억 달러) 단위로 표현하세요"""

def generate_answer(user_question: str, context: str, history: list) -> str:
    messages = [{"role": "system", "content": ANSWER_PROMPT + "\n\n[종목 데이터]\n" + context}]
    for h in history[-10:]:
        if h["role"] in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_question})
    return call_llm(messages, temperature=0.4, max_tokens=2048)

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 US Index RAG")
    st.markdown("---")
    st.markdown("""
    <div style='font-family:DM Mono,monospace;font-size:0.7rem;color:#6b6b80;line-height:2'>
    LLM이 질문을 분석해<br>자동으로 DB를 조회합니다.<br><br>
    <b style='color:#e8e8f0'>💡 질문 예시</b><br>
    · 에너지 섹터 시총 상위 10개<br>
    · S&P500 섹터별 종목 수<br>
    · DOW30 중 기술주는?<br>
    · Apple CEO 알려줘<br>
    · NASDAQ 상장 헬스케어 기업
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── 메인 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='rag-header'>
    <span class='rag-title'>US INDEX RAG</span>
    <span class='rag-sub'>TEXT-TO-QUERY · SUPABASE × GEMINI</span>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='msg-user'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        if msg.get("params"):
            p = msg["params"]
            arrow = "↓" if p.get("order_desc") else "↑"
            st.markdown(f"""
            <div class='query-box'>
                <div class='query-label'>🔍 AUTO-GENERATED QUERY PARAMS</div>
                섹터: {p.get('sectors') or '전체'} &nbsp;|&nbsp;
                거래소: {p.get('exchanges') or '전체'} &nbsp;|&nbsp;
                S&P500: {p.get('in_sp500')} &nbsp;|&nbsp;
                NDX100: {p.get('in_ndx100')} &nbsp;|&nbsp;
                DOW30: {p.get('in_dow30')} &nbsp;|&nbsp;
                정렬: {p.get('order_by')} {arrow} &nbsp;|&nbsp;
                limit: {p.get('limit')}
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"<div class='msg-assistant'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

if prompt := st.chat_input("종목에 대해 질문하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='msg-user'>🧑 {prompt}</div>", unsafe_allow_html=True)

    history = [m for m in st.session_state.messages[:-1] if m["role"] in ("user", "assistant")]

    with st.spinner("질문 분석 중..."):
        params = extract_query_params(prompt, history)

    arrow = "↓" if params.get("order_desc") else "↑"
    st.markdown(f"""
    <div class='query-box'>
        <div class='query-label'>🔍 AUTO-GENERATED QUERY PARAMS</div>
        섹터: {params.get('sectors') or '전체'} &nbsp;|&nbsp;
        거래소: {params.get('exchanges') or '전체'} &nbsp;|&nbsp;
        S&P500: {params.get('in_sp500')} &nbsp;|&nbsp;
        NDX100: {params.get('in_ndx100')} &nbsp;|&nbsp;
        DOW30: {params.get('in_dow30')} &nbsp;|&nbsp;
        정렬: {params.get('order_by')} {arrow} &nbsp;|&nbsp;
        limit: {params.get('limit')}
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("DB 조회 중..."):
        stocks = fetch_by_params(params)
        context = aggregate_context(stocks, params)

    st.markdown(f"""
    <div class='stat-row'>
        <div class='stat-badge'>조회된 종목 <span>{len(stocks)}개</span></div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("답변 생성 중..."):
        answer = generate_answer(prompt, context, history)

    st.session_state.messages.append({"role": "assistant", "content": answer, "params": params})
    st.markdown(f"<div class='msg-assistant'>🤖 {answer}</div>", unsafe_allow_html=True)
    st.rerun()