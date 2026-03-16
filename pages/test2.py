import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="ASPM Command Center",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit 기본 여백 제거 및 전체 화면 스타일링
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        padding-left: 0rem !important; 
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# ASPM Dashboard HTML 구조 작성
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #030b0d;
            --bg-glow: #08262a;
            --cyan: #2dd4bf;
            --muted: #64748b;
            --text-light: #f1f5f9;
            --border: rgba(45, 212, 191, 0.15);
            --card-bg: rgba(6, 20, 24, 0.5);
            --red: #ef4444;
            --yellow: #f59e0b;
        }

        body {
            margin: 0; padding: 0;
            background-color: var(--bg-color);
            background-image: radial-gradient(ellipse 60% 70% at 50% 40%, var(--bg-glow) 0%, var(--bg-color) 100%);
            color: var(--text-light);
            font-family: 'Inter', sans-serif;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            display: flex;
        }

        /* 왼쪽 아이콘 사이드바 */
        .left-sidebar {
            width: 60px;
            background: transparent;
            border-right: 1px solid rgba(255,255,255,0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 24px;
            gap: 28px;
            z-index: 10;
        }
        .logo-ring {
            width: 24px; height: 24px;
            border: 4px solid var(--cyan);
            border-top-color: transparent;
            border-radius: 50%;
            transform: rotate(-45deg);
        }
        .icon-item {
            width: 18px; height: 18px;
            background: var(--muted);
            mask-size: contain;
            -webkit-mask-size: contain;
            opacity: 0.7;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .icon-item:hover { opacity: 1; background: var(--cyan); }
        .icon-star { -webkit-mask-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'); }
        .icon-folder { -webkit-mask-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>'); }
        .icon-shield { -webkit-mask-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>'); }
        .icon-cloud { -webkit-mask-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M19.35 10.04A7.49 7.49 0 0012 4C9.11 4 6.6 5.64 5.35 8.04A5.994 5.994 0 000 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg>'); }

        /* 메인 컨텐츠 영역 */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* ------------------ 상단 헤더 ------------------ */
        .top-header {
            height: 70px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 40px;
            z-index: 10;
        }
        .header-title {
            font-size: 1.1rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dropdown-btn {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.15);
            color: #ccc;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
        }

        /* ------------------ 중앙 그래프 캔버스 ------------------ */
        .graph-area {
            flex: 1;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 5%;
        }

        /* 배경 SVG 연결선 */
        .connections {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none;
            z-index: 0;
        }
        path.line-solid {
            fill: none;
            stroke: rgba(45, 212, 191, 0.4);
            stroke-width: 1.5;
            box-shadow: 0 0 10px rgba(45, 212, 191, 0.5);
        }
        path.line-dashed {
            fill: none;
            stroke: rgba(45, 212, 191, 0.3);
            stroke-width: 1.5;
            stroke-dasharray: 4 4;
        }
        path.line-glow {
            fill: none;
            stroke: rgba(45, 212, 191, 0.15);
            stroke-width: 6;
            filter: blur(2px);
        }

        /* 노드 공통 */
        .node-col {
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            gap: 40px;
        }
        
        /* 컬럼 1: Sources */
        .source-item {
            display: flex;
            align-items: center;
            gap: 12px;
            text-align: right;
        }
        .source-info {
            display: flex;
            flex-direction: column;
        }
        .source-name { font-size: 0.85rem; font-weight: 600; color: #fff; }
        .source-sub { font-size: 0.7rem; color: var(--muted); }
        .source-icon {
            width: 32px; height: 32px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.1);
            background: #09171a;
            display: flex; align-items: center; justify-content: center;
            position: relative;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }
        .source-icon::after {
            content: ''; position: absolute; top: -3px; left: -3px; right: -3px; bottom: -3px;
            border-radius: 50%;
            border: 2px solid transparent;
            border-top-color: var(--cyan);
            border-right-color: var(--red);
            opacity: 0.5;
        }

        /* 컬럼 2: Aggregation Left */
        .agg-node {
            text-align: center;
        }
        .agg-val { font-size: 1.8rem; font-weight: 700; color: #fff; letter-spacing: 0.05em; }
        .agg-label { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.15em; line-height: 1.4; }

        /* 중앙 Radar 원형 차트 */
        .radar-box {
            position: relative;
            width: 300px; height: 300px;
            display: flex; align-items: center; justify-content: center;
        }
        .radar-ring {
            position: absolute;
            border-radius: 50%;
            border: 1px dashed rgba(45, 212, 191, 0.3);
        }
        .radar-ring:nth-child(1) { width: 100px; height: 100px; }
        .radar-ring:nth-child(2) { width: 200px; height: 200px; }
        .radar-ring:nth-child(3) { width: 280px; height: 280px; }
        .dot {
            position: absolute; width: 4px; height: 4px; border-radius: 50%;
            background: var(--cyan); box-shadow: 0 0 6px var(--cyan);
        }
        .dot.v { background: #c084fc; box-shadow: 0 0 6px #c084fc; } /* 보라색 계열 */
        
        .floating-label {
            position: absolute; font-size: 0.65rem; color: var(--muted); display: flex; align-items: center; gap: 4px;
        }
        .floating-label.cloud-1 { top: -20px; right: -40px; }
        .floating-label.cloud-2 { top: 30px; left: -60px; }

        /* 컬럼 3: Aggregation Right */
        .cases-node { text-align: center; }
        .tags-row { display: flex; gap: 6px; justify-content: center; margin-top: 8px; }
        .tag-badge { 
            font-size: 0.65rem; font-family: 'JetBrains Mono', monospace; font-weight: 600;
            display: flex; align-items: center; gap: 4px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.05);
        }
        .tag-badge.c { color: white; background: rgba(239, 68, 68, 0.6); }
        .tag-badge.h { color: white; background: rgba(245, 158, 11, 0.6); }

        /* 컬럼 4: Right Output Nodes */
        .output-item {
            text-align: center;
            display: flex; flex-direction: column; align-items: center; gap: 8px;
        }
        .out-icon { color: var(--muted); font-size: 1.2rem; }
        .out-val { font-size: 1.4rem; font-weight: 600; color: #fff; }
        .out-label { font-size: 0.65rem; color: var(--muted); letter-spacing: 0.1em; }


        /* ------------------ 하단 위젯 영역 ------------------ */
        .footer-widgets {
            height: 160px;
            padding: 0 40px 30px;
            display: flex;
            gap: 20px;
            z-index: 10;
        }
        .widget-card {
            flex: 1;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            backdrop-filter: blur(10px);
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .widget-title {
            font-size: 0.85rem; font-weight: 500; color: #fff; display: flex; justify-content: space-between;
        }
        .widget-link { font-size: 0.75rem; color: #38bdf8; cursor: pointer; }
        
        /* Coverage Donut */
        .coverage-content { display: flex; align-items: center; gap: 20px; margin-top: 10px; }
        .donut-wrapper { position: relative; width: 60px; height: 60px; }
        .donut-svg { transform: rotate(-90deg); width: 100%; height: 100%; }
        .donut-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 4; }
        .donut-val { fill: none; stroke: var(--cyan); stroke-width: 4; stroke-dasharray: 100 100; stroke-linecap: round; }
        .donut-text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; font-weight: 600; color: var(--cyan); }
        
        .coverage-meta div:first-child { font-size: 0.9rem; font-weight: 600; color: #fff; }
        .coverage-meta div:last-child { font-size: 0.7rem; color: var(--muted); margin-top: 4px; }
        .unscanned-link { font-size: 0.7rem; color: #38bdf8; margin-top: 12px; }

        /* SLA violation */
        .sla-content { margin-top: 10px; }
        .sla-top { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
        .sla-val { font-size: 1.8rem; font-weight: 700; color: #fff; }
        .sla-sub { font-size: 0.75rem; color: var(--muted); }
        .sla-trend { width: 100%; height: 26px; margin-top: 4px; }
        .trend-path { fill: none; stroke: var(--red); stroke-width: 1.5; }
        .trend-meta { text-align: right; font-size: 0.7rem; color: var(--red); font-weight: 500; margin-top: -8px; }

        /* Riskiest Applications */
        .risk-apps { display: flex; gap: 30px; margin-top: 15px; }
        .risk-app-col { display: flex; flex-direction: column; gap: 6px; }
        .r-name { font-size: 0.8rem; color: #fff; font-weight: 500; }
        .r-cases { font-size: 0.75rem; color: var(--muted); margin-bottom: 2px; }

        /* 버튼 */
        .coverage-details-btn {
            position: absolute; bottom: 200px; left: 60px;
            background: transparent; border: 1px solid rgba(255,255,255,0.2);
            padding: 8px 16px; border-radius: 20px; font-size: 0.8rem; color: #cbd5e1;
            cursor: pointer;
        }

    </style>
</head>
<body>

    <!-- 좌측 사이드바 -->
    <div class="left-sidebar">
        <div class="logo-ring"></div>
        <div class="icon-item icon-star"></div>
        <div class="icon-item icon-shield"></div>
        <div class="icon-item icon-folder"></div>
        <div class="icon-item icon-cloud"></div>
    </div>

    <!-- 메인 컨텐츠 영역 -->
    <div class="main-container">
        
        <!-- 상단 헤더 -->
        <div class="top-header">
            <div class="header-title">ASPM Command Center <span style="font-size: 0.6rem; color: #64748b;">▼</span></div>
            <div class="dropdown-btn">All Applications (39) <span style="font-size: 0.6rem;">▼</span></div>
        </div>

        <!-- 커버리지 디테일 버튼 -->
        <button class="coverage-details-btn">More coverage details</button>

        <!-- 중앙 메인 그래프 -->
        <div class="graph-area">
            
            <!-- SVG 곡선 배경 -->
            <svg class="connections" preserveAspectRatio="none" viewBox="0 0 1000 500">
                <!-- Sources to 1.2M -->
                <path class="line-glow" d="M 180,100 C 250,100 250,250 320,250" />
                <path class="line-dashed" d="M 180,100 C 250,100 250,250 320,250" />
                <path class="line-solid" d="M 180,160 C 250,160 250,250 320,250" />
                <path class="line-solid" d="M 180,220 C 250,220 250,250 320,250" />
                <path class="line-solid" d="M 180,280 C 250,280 250,250 320,250" />
                <path class="line-solid" d="M 180,360 C 250,360 250,250 320,250" />

                <!-- 1.2M to Radar -->
                <path class="line-solid" d="M 400,250 L 415,250" />
                
                <!-- Radar to 600 Cases -->
                <path class="line-solid" d="M 585,250 L 600,250" />
                
                <!-- 600 Cases to Output -->
                <path class="line-solid" d="M 670,250 C 720,250 720,120 780,120" />
                <path class="line-solid" d="M 670,250 C 720,250 720,200 780,200" />
                <path class="line-solid" d="M 670,250 C 720,250 720,280 780,280" />
                <path class="line-solid" d="M 600,400 C 650,400 720,380 780,380" /> <!-- Custom detached line -->
            </svg>

            <!-- Column 1: Sources -->
            <div class="node-col" style="gap: 28px;">
                <div class="source-item">
                    <div class="source-info"><div class="source-name">GitHub</div><div class="source-sub">16K / 20K Scanned</div></div>
                    <div class="source-icon" style="color:#f43f5e;">❤️</div>
                </div>
                <div class="source-item">
                    <div class="source-info"><div class="source-name">GitLab</div><div class="source-sub">300 / 300 Scanned</div></div>
                    <div class="source-icon" style="color:#f97316;">🦊</div>
                </div>
                <div class="source-item">
                    <div class="source-info"><div class="source-name">Semgrep</div><div class="source-sub">120 / 120 Scanned</div></div>
                    <div class="source-icon" style="color:#14b8a6;">♾️</div>
                </div>
                <div class="source-item">
                    <div class="source-info"><div class="source-name">Jenkins</div><div class="source-sub">5K / 5.5K Scanned</div></div>
                    <div class="source-icon" style="color:#e11d48;">🤵</div>
                </div>
                <div class="source-item" style="margin-top: 20px;">
                    <div class="source-info"><div class="source-name">JFrog</div><div class="source-sub">3 / 3 Scanned</div></div>
                    <div class="source-icon" style="color:#10b981;">🐸</div>
                </div>
            </div>

            <!-- Column 2: 1.2M Issues -->
            <div class="node-col agg-node">
                <div class="agg-val">1.2M</div>
                <div class="agg-label">ISSUES &<br>FINDINGS</div>
            </div>

            <!-- Center Radar -->
            <div class="radar-box">
                <div class="radar-ring"></div>
                <div class="radar-ring"></div>
                <div class="radar-ring"></div>
                
                <div class="floating-label cloud-1">☁️ AWS cloud accounts 22</div>
                <div class="floating-label cloud-2">☁️ Google cloud accounts 173</div>
                
                <!-- Random Scattered Dots -->
                <!-- Python을 통해 SVG나 DIV로 세밀하게 점을 뿌리는 것은 생략, 정적 HTML 닷 생성 -->
                <script>
                    const rbox = document.querySelector('.radar-box');
                    for (let i = 0; i < 60; i++) {
                        let dot = document.createElement('div');
                        dot.className = 'dot' + (Math.random() > 0.7 ? ' v' : '');
                        let angle = Math.random() * Math.PI * 2;
                        let radius = 20 + Math.random() * 110;
                        dot.style.left = `calc(50% + ${Math.cos(angle) * radius}px)`;
                        dot.style.top = `calc(50% + ${Math.sin(angle) * radius}px)`;
                        rbox.appendChild(dot);
                    }
                </script>
            </div>

            <!-- Column 3: 600 Cases -->
            <div class="node-col cases-node">
                <div class="agg-val" style="font-size:1.6rem;">600</div>
                <div class="agg-label">CASES</div>
                <div class="tags-row">
                    <div class="tag-badge c">C 26</div>
                    <div class="tag-badge h">H 13</div>
                </div>
                <div style="font-size:0.65rem; color:#64748b; margin-top: 60px;">Applications 116</div>
            </div>

            <!-- Column 4: Outputs -->
            <div class="node-col" style="gap: 50px;">
                <div class="output-item">
                    <div class="out-icon">⟡</div>
                    <div class="out-val">312</div>
                    <div class="out-label">VULNERABILITIES</div>
                </div>
                <div class="output-item">
                    <div class="out-icon">‹›</div>
                    <div class="out-val">144</div>
                    <div class="out-label">CODE WEAKNESSES</div>
                </div>
                <div class="output-item">
                    <div class="out-icon">🔑</div>
                    <div class="out-val">43</div>
                    <div class="out-label">SECRETS</div>
                </div>
                <div class="output-item">
                    <div class="out-icon">⇄</div>
                    <div class="out-val">101</div>
                    <div class="out-label">IAC MISCONFIGURATIONS</div>
                </div>
            </div>
        </div> <!-- end graph-area -->

        <!-- Bottom Widgets -->
        <div class="footer-widgets">
            
            <!-- Card 1 -->
            <div class="widget-card">
                <div class="widget-title">Total Coverage</div>
                <div class="coverage-content">
                    <div class="donut-wrapper">
                        <svg class="donut-svg" viewBox="0 0 36 36">
                            <circle class="donut-bg" cx="18" cy="18" r="16"></circle>
                            <circle class="donut-val" cx="18" cy="18" r="16" stroke-dasharray="87 100" style="stroke-dasharray: 87, 100;"></circle>
                        </svg>
                        <div class="donut-text">87%</div>
                    </div>
                    <div class="coverage-meta">
                        <div>23K / 25K</div>
                        <div>Assets scanned</div>
                    </div>
                </div>
                <div class="unscanned-link">2K Assets unscanned</div>
            </div>

            <!-- Card 2 -->
            <div class="widget-card">
                <div class="widget-title">Violation Of SLA</div>
                <div class="sla-content">
                    <div class="sla-top">
                        <div class="sla-val">7</div>
                        <div class="sla-sub">Cases with violations</div>
                        <div class="tags-row" style="margin:0;"><div class="tag-badge c">C 1</div><div class="tag-badge h">H 6</div></div>
                    </div>
                    <div style="font-size:0.75rem; color:#94a3b8; display:flex; align-items:center;">MTTR ⓘ</div>
                    <svg class="sla-trend" preserveAspectRatio="none" viewBox="0 0 100 20">
                        <path class="trend-path" d="M0,15 L10,12 L20,18 L30,5 L40,10 L50,15 L60,8 L70,12 L80,2 L90,8 L100,5" />
                    </svg>
                    <div class="trend-meta">↓ 25%<br><span style="color:#64748b;font-weight:400;">Less than last month</span></div>
                </div>
            </div>

            <!-- Card 3 -->
            <div class="widget-card" style="flex: 1.5;">
                <div class="widget-title">Riskiest Applications <span class="widget-link">View all applications (118)</span></div>
                <div class="risk-apps">
                    <div class="risk-app-col">
                        <div class="r-name">Prodigy</div>
                        <div class="r-cases">24 Cases</div>
                        <div class="tags-row" style="justify-content:flex-start;"><div class="tag-badge c">C 2</div><div class="tag-badge h">H 22</div></div>
                    </div>
                    <div class="risk-app-col">
                        <div class="r-name">FlashbackFlow</div>
                        <div class="r-cases">14 Cases</div>
                        <div class="tags-row" style="justify-content:flex-start;"><div class="tag-badge c">C 1</div><div class="tag-badge h">H 13</div></div>
                    </div>
                    <div class="risk-app-col">
                        <div class="r-name">Calibrium</div>
                        <div class="r-cases">7 Cases</div>
                        <div class="tags-row" style="justify-content:flex-start;"><div class="tag-badge c">H 7</div></div>
                    </div>
                </div>
            </div>

        </div> <!-- end widgets -->

    </div> <!-- end main-container -->
</body>
</html>
"""

# HTML 렌더링 (화면 높이를 꽉 채우도록설정)
components.html(html_content, height=1000)
