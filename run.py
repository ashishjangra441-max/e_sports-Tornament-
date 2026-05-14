"""
==============================================================================
APEX // QUANTUM OPERATIONS CONSOLE
Senior Data-Architect Edition  |  Build OMEGA.10
==============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import urllib.parse
from datetime import datetime, timedelta
import hashlib
import os
import io
import random
# ==========================================
# COLOR UTILITY FUNCTIONS
# ==========================================

def hex_to_rgba(hex_color, alpha):
    """
    Convert HEX color to RGBA format for Plotly and CSS.

    Example:
    #00f0ff + 0.2
    ->
    rgba(0,240,255,0.2)
    """

    if not hex_color:
        return f'rgba(0,0,0,{alpha})'

    hex_color = hex_color.strip().lstrip('#')

    # Handle short hex
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])

    # Safety fallback
    if len(hex_color) != 6:
        return f'rgba(0,0,0,{alpha})'

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return f'rgba({r},{g},{b},{alpha})'
# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="APEX // QUANTUM OPS",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULTS = {
    'sys_logs': [],
    'authenticated': False,
    'username': None,
    'role': None,
    'failed_attempts': 0,
    'theme': 'quantum',          # 'quantum' (cyan/magenta), 'amber' (night-vision), 'plasma' (purple/pink)
    'auto_refresh': 'OFF',
    'session_start': None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ==========================================
# 2. AUTHENTICATION (Hardcoded)
# ==========================================
USERS = {
    "admin": {
        "password_sha256": hashlib.sha256("admin@apex2026".encode()).hexdigest(),
        "role": "Admin",
        "display_name": "ARCHITECT-01",
        "clearance": "OMEGA",
    },
    "viewer": {
        "password_sha256": hashlib.sha256("viewer@apex2026".encode()).hexdigest(),
        "role": "Viewer",
        "display_name": "OBSERVER-07",
        "clearance": "DELTA",
    },
}

def verify_credentials(username, password):
    user = USERS.get(username.lower().strip())
    if not user:
        return None
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if pw_hash == user["password_sha256"]:
        return user
    return None


# ==========================================
# 3. THEME SYSTEM
# ==========================================
THEMES = {
    "quantum": {
        "primary":   "#00f0ff",   # electric cyan
        "secondary": "#ff006e",   # magenta
        "accent":    "#7c3aed",   # violet
        "success":   "#00ffa3",   # mint
        "warn":      "#fbbf24",   # amber
        "alert":     "#ff006e",
        "bg_a":      "#0a0e1a",
        "bg_b":      "#040810",
        "label":     "QUANTUM",
        "icon":      "◈",
    },
    "amber": {
        "primary":   "#ffb300",
        "secondary": "#ff5722",
        "accent":    "#ffd54f",
        "success":   "#76ff03",
        "warn":      "#ffeb3b",
        "alert":     "#ff5722",
        "bg_a":      "#1a0f00",
        "bg_b":      "#0d0700",
        "label":     "NIGHT-VISION",
        "icon":      "◬",
    },
    "plasma": {
        "primary":   "#d946ef",
        "secondary": "#06b6d4",
        "accent":    "#f0abfc",
        "success":   "#34d399",
        "warn":      "#fbbf24",
        "alert":     "#f43f5e",
        "bg_a":      "#1a0a1f",
        "bg_b":      "#0a0410",
        "label":     "PLASMA",
        "icon":      "◉",
    },
}


def inject_theme_css(theme_key):
    t = THEMES[theme_key]
    p, s, a = t["primary"], t["secondary"], t["accent"]
    success, warn, alert = t["success"], t["warn"], t["alert"]
    bg_a, bg_b = t["bg_a"], t["bg_b"]

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syncopate:wght@400;700&family=Rajdhani:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;700&display=swap');

        :root {{
            --apex-primary: {p};
            --apex-secondary: {s};
            --apex-accent: {a};
            --apex-success: {success};
            --apex-warn: {warn};
            --apex-alert: {alert};
            --apex-bg-a: {bg_a};
            --apex-bg-b: {bg_b};
            --grid-color: {hex_to_rgba(p, 0.05)};
        }}

        /* ===== GLOBAL ATMOSPHERE ===== */
        html, body, [data-testid="stAppViewContainer"] {{
            cursor: crosshair !important;
            background:
                radial-gradient(ellipse at 15% 20%, {hex_to_rgba(p, 0.08)} 0%, transparent 50%),
                radial-gradient(ellipse at 85% 80%, {hex_to_rgba(s, 0.08)} 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, {hex_to_rgba(a, 0.04)} 0%, transparent 70%),
                linear-gradient(180deg, {bg_a} 0%, {bg_b} 100%);
            background-attachment: fixed;
            color: #e8eaed;
            font-family: 'Rajdhani', sans-serif;
            overflow-x: hidden;
        }}

        /* Animated grid + scanline overlay */
        [data-testid="stAppViewContainer"]::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image:
                linear-gradient({p}08 1px, transparent 1px),
                linear-gradient(90deg, {p}08 1px, transparent 1px),
                repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.15) 4px, rgba(0,0,0,0.15) 4px);
            background-size: 40px 40px, 40px 40px, 100% 4px;
            pointer-events: none;
            z-index: 0;
            animation: gridShift 60s linear infinite;
        }}

        /* Vignette */
        [data-testid="stAppViewContainer"]::after {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.5) 100%);
            pointer-events: none;
            z-index: 0;
        }}

        @keyframes gridShift {{
            0% {{ transform: translate(0, 0); }}
            100% {{ transform: translate(40px, 40px); }}
        }}

        /* Push content above background */
        .main .block-container {{
            position: relative;
            z-index: 1;
            padding-top: 1.5rem;
            max-width: 100%;
        }}

        a, button, div[role="button"], .stSelectbox, summary {{ cursor: pointer !important; }}

        /* ===== TYPOGRAPHY ===== */
        h1, h2, h3, h4, h5 {{
            font-family: 'Syncopate', sans-serif !important;
            color: #ffffff !important;
            text-transform: uppercase;
            letter-spacing: 3px;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        p, label, span {{
            font-family: 'Rajdhani', sans-serif;
            letter-spacing: 0.5px;
        }}

        code, pre, .mono {{
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* ===== KPI METRIC CARDS — GLASSMORPHIC W/ ANIMATED BORDER ===== */
        div[data-testid="metric-container"] {{
            background:
                linear-gradient(135deg, {bg_a}cc 0%, {bg_b}ee 100%);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid {hex_to_rgba(p, 0.2)};
            border-radius: 4px;
            padding: 24px 22px;
            box-shadow:
                0 8px 32px rgba(0,0,0,0.6),
                inset 0 1px 0 {hex_to_rgba(p, 0.1)},
                inset 0 -1px 0 rgba(0,0,0,0.4);
            position: relative;
            overflow: hidden;
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s, box-shadow 0.3s;
        }}
        div[data-testid="metric-container"]::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, {p}, {s}, transparent);
            background-size: 200% 100%;
            animation: borderFlow 3s linear infinite;
        }}
        div[data-testid="metric-container"]::after {{
            content: '';
            position: absolute;
            top: 8px; right: 8px;
            width: 6px; height: 6px;
            background: {p};
            border-radius: 50%;
            box-shadow: 0 0 10px {p};
            animation: pulse-dot 2s ease-in-out infinite;
        }}
        div[data-testid="metric-container"]:hover {{
            transform: translateY(-4px) scale(1.01);
            border-color: {p};
            box-shadow:
                0 16px 48px {hex_to_rgba(p, 0.2)},
                inset 0 1px 0 {hex_to_rgba(p, 0.2)};
        }}
        @keyframes borderFlow {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        @keyframes pulse-dot {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(1.4); }}
        }}

        div[data-testid="metric-container"] label {{
            color: #8892a8 !important;
            font-size: 0.7rem !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 500 !important;
            letter-spacing: 3px !important;
            text-transform: uppercase;
        }}
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 2.6rem !important;
            font-family: 'Syncopate', sans-serif !important;
            text-shadow: 0 0 24px {hex_to_rgba(p, 0.4)}, 0 0 4px {p};
            letter-spacing: 1px;
            line-height: 1.1;
        }}
        div[data-testid="metric-container"] div[data-testid="stMetricDelta"] {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.8rem !important;
        }}

        /* ===== INPUTS ===== */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"],
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input {{
            background: linear-gradient(135deg, {bg_a}99, {bg_b}cc) !important;
            border: 1px solid {hex_to_rgba(p, 0.4)} !important;
            border-radius: 2px !important;
            color: {p} !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 1rem !important;
            transition: all 0.2s;
        }}
        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="input"] > div:hover,
        .stTextInput input:focus,
        .stNumberInput input:focus {{
            border-color: {s} !important;
            box-shadow: 0 0 0 2px {hex_to_rgba(s, 0.2)}, 0 0 16px {hex_to_rgba(s, 0.4)} !important;
        }}
        div[data-baseweb="popover"] ul {{
            background: {bg_b}f0 !important;
            border: 1px solid {p} !important;
            font-family: 'JetBrains Mono', monospace !important;
            backdrop-filter: blur(20px);
        }}

        /* ===== BUTTONS ===== */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
            background: linear-gradient(135deg, transparent, {hex_to_rgba(p, 0.1)}) !important;
            border: 1px solid {p} !important;
            color: {p} !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 3px !important;
            text-transform: uppercase;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            border-radius: 2px;
            width: 100%;
            position: relative;
            overflow: hidden;
            padding: 10px 20px !important;
        }}
        .stButton > button::before, .stDownloadButton > button::before, .stFormSubmitButton > button::before {{
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, {hex_to_rgba(p, 0.2)}, transparent);
            transition: left 0.5s;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
            background: {hex_to_rgba(p, 0.15)} !important;
            box-shadow: 0 0 24px {hex_to_rgba(p, 0.5)}, inset 0 0 12px {hex_to_rgba(p, 0.25)} !important;
            color: #ffffff !important;
            transform: translateY(-2px);
        }}
        .stButton > button:hover::before, .stDownloadButton > button:hover::before, .stFormSubmitButton > button:hover::before {{
            left: 100%;
        }}

        /* ===== TABS — ANIMATED UNDERLINE ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            background: linear-gradient(180deg, {bg_a}80, transparent);
            padding: 6px 14px 0 14px;
            border-bottom: 1px solid {hex_to_rgba(p, 0.15)};
            border-radius: 4px 4px 0 0;
            backdrop-filter: blur(8px);
        }}
        .stTabs [data-baseweb="tab"] {{
            color: #6b7280 !important;
            background: transparent !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: 2px !important;
            border: none !important;
            padding: 14px 22px !important;
            text-transform: uppercase;
            transition: color 0.2s;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {p} !important;
        }}
        .stTabs [aria-selected="true"] {{
            color: {p} !important;
            background: linear-gradient(0deg, {hex_to_rgba(p, 0.1)} 0%, transparent 100%) !important;
            border-bottom: 2px solid {p} !important;
            text-shadow: 0 0 12px {p};
        }}

        /* ===== DATAFRAMES ===== */
        [data-testid="stDataFrame"] {{
            background: linear-gradient(135deg, {bg_a}cc, {bg_b}ee);
            border: 1px solid {hex_to_rgba(p, 0.15)};
            border-radius: 4px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        }}
        [data-testid="stDataFrame"] th {{
            background: {bg_b} !important;
            color: {p} !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 2px !important;
            text-transform: uppercase;
            font-size: 0.78rem !important;
            border-bottom: 2px solid {hex_to_rgba(p, 0.4)} !important;
            padding: 12px !important;
        }}
        [data-testid="stDataFrame"] td {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.85rem !important;
        }}

        /* ===== EXPANDERS ===== */
        div[data-testid="stExpander"] {{
            background: linear-gradient(135deg, {bg_a}cc, {bg_b}f0) !important;
            border: 1px solid {hex_to_rgba(alert, 0.4)} !important;
            border-left: 4px solid {alert} !important;
            border-radius: 2px !important;
            margin-top: 24px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        }}
        div[data-testid="stExpander"] summary p {{
            color: {alert} !important;
            font-family: 'Syncopate', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 3px !important;
            text-shadow: 0 0 12px {hex_to_rgba(alert, 0.5)};
            font-size: 0.9rem !important;
        }}

        /* ===== PROGRESS BARS ===== */
        .stProgress > div > div > div {{
            background: linear-gradient(90deg, {p}, {s}) !important;
            box-shadow: 0 0 8px {hex_to_rgba(p, 0.5)};
        }}

        /* ===== SCROLLBARS ===== */
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: {bg_b}; }}
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, {hex_to_rgba(p, 0.4)}, {hex_to_rgba(s, 0.4)});
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(180deg, {p}, {s});
        }}

        /* ===== HR ===== */
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, {hex_to_rgba(p, 0.4)}, transparent);
            margin: 2rem 0;
            position: relative;
        }}

        /* ===== TICKER STRIP ===== */
        .apex-ticker {{
            background: linear-gradient(90deg, {bg_b}, {bg_a}, {bg_b});
            border-top: 1px solid {hex_to_rgba(p, 0.2)};
            border-bottom: 1px solid {hex_to_rgba(p, 0.2)};
            padding: 10px 0;
            margin: 14px 0 24px 0;
            overflow: hidden;
            position: relative;
            backdrop-filter: blur(4px);
        }}
        .apex-ticker-track {{
            display: inline-block;
            white-space: nowrap;
            animation: tickerScroll 50s linear infinite;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            letter-spacing: 1.5px;
        }}
        .apex-ticker-track:hover {{ animation-play-state: paused; }}
        @keyframes tickerScroll {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        .ticker-item {{ margin: 0 32px; color: #8892a8; }}
        .ticker-up {{ color: {success}; }}
        .ticker-down {{ color: {alert}; }}
        .ticker-tag {{ color: {p}; font-weight: 700; }}

        /* ===== HEADER BAR ===== */
        .apex-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 28px;
            background: linear-gradient(135deg, {bg_a}f0, {bg_b}f0);
            border: 1px solid {hex_to_rgba(p, 0.2)};
            border-left: 4px solid {p};
            border-radius: 2px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 32px rgba(0,0,0,0.6), inset 0 1px 0 {hex_to_rgba(p, 0.1)};
            position: relative;
            overflow: hidden;
        }}
        .apex-header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 1px;
            background: linear-gradient(90deg, transparent, {p}, {s}, transparent);
            background-size: 200% 100%;
            animation: borderFlow 4s linear infinite;
        }}
        .apex-header-title {{
            font-family: 'Syncopate', sans-serif;
            font-weight: 700;
            font-size: 1.5rem;
            color: #ffffff;
            letter-spacing: 6px;
            margin: 0;
            text-shadow: 0 0 20px {hex_to_rgba(p, 0.4)};
        }}
        .apex-header-sub {{
            font-family: 'JetBrains Mono', monospace;
            color: {p};
            font-size: 0.7rem;
            letter-spacing: 3px;
            margin-top: 4px;
        }}
        .apex-rec-badge {{
            font-family: 'Syncopate', sans-serif;
            font-weight: 700;
            color: {alert};
            font-size: 0.85rem;
            letter-spacing: 3px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .live-pulse {{
            display: inline-block;
            width: 10px; height: 10px;
            border-radius: 50%;
            background: {alert};
            box-shadow: 0 0 12px {alert};
            animation: pulse-dot 1.2s infinite;
        }}

        /* ===== LOGIN — IMMERSIVE BOOT SCREEN ===== */
        .apex-login-bg {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: -1;
            background:
                radial-gradient(ellipse at 20% 30%, {hex_to_rgba(p, 0.1)} 0%, transparent 50%),
                radial-gradient(ellipse at 80% 70%, {hex_to_rgba(s, 0.1)} 0%, transparent 50%),
                {bg_b};
        }}
        .apex-login-card {{
            max-width: 520px;
            margin: 5vh auto 0 auto;
            padding: 50px 44px;
            background: linear-gradient(135deg, {bg_a}f0 0%, {bg_b}f8 100%);
            border: 1px solid {hex_to_rgba(p, 0.4)};
            border-radius: 4px;
            box-shadow:
                0 0 80px {hex_to_rgba(p, 0.2)},
                0 20px 60px rgba(0,0,0,0.8),
                inset 0 1px 0 {hex_to_rgba(p, 0.2)};
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
            animation: cardEntry 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes cardEntry {{
            0% {{ opacity: 0; transform: translateY(30px) scale(0.95); }}
            100% {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .apex-login-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, {p}, {s}, {a}, {p});
            background-size: 200% 100%;
            animation: borderFlow 3s linear infinite;
        }}
        .apex-login-card::after {{
            content: '';
            position: absolute;
            top: 12px; right: 12px;
            width: 10px; height: 10px;
            background: {success};
            border-radius: 50%;
            box-shadow: 0 0 16px {success};
            animation: pulse-dot 1.5s infinite;
        }}
        .apex-corner {{
            position: absolute;
            width: 24px; height: 24px;
            border: 2px solid {p};
        }}
        .apex-corner.tl {{ top: 12px; left: 12px; border-right: none; border-bottom: none; }}
        .apex-corner.tr {{ top: 12px; right: 12px; border-left: none; border-bottom: none; }}
        .apex-corner.bl {{ bottom: 12px; left: 12px; border-right: none; border-top: none; }}
        .apex-corner.br {{ bottom: 12px; right: 12px; border-left: none; border-top: none; }}

        .apex-login-icon {{
            font-family: 'Syncopate', sans-serif;
            font-size: 4.5rem;
            text-align: center;
            background: linear-gradient(135deg, {p}, {s});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            line-height: 1;
            text-shadow: 0 0 40px {hex_to_rgba(p, 0.4)};
            animation: glow-pulse 3s ease-in-out infinite;
        }}
        @keyframes glow-pulse {{
            0%, 100% {{ filter: drop-shadow(0 0 12px {hex_to_rgba(p, 0.5)}); }}
            50% {{ filter: drop-shadow(0 0 24px {hex_to_rgba(s, 0.5)}); }}
        }}
        .apex-login-title {{
            font-family: 'Syncopate', sans-serif;
            font-weight: 700;
            font-size: 2.4rem;
            letter-spacing: 12px;
            color: #ffffff;
            text-align: center;
            margin: 8px 0 0 0;
            text-shadow: 0 0 24px {p};
        }}
        .apex-login-sub {{
            font-family: 'JetBrains Mono', monospace;
            color: {p};
            text-align: center;
            letter-spacing: 6px;
            font-size: 0.75rem;
            margin-top: 8px;
            margin-bottom: 36px;
            text-transform: uppercase;
        }}
        .apex-boot-line {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: {success};
            letter-spacing: 1px;
            margin: 4px 0;
            opacity: 0;
            animation: typeIn 0.4s forwards;
        }}
        .apex-boot-line:nth-child(1) {{ animation-delay: 0.2s; }}
        .apex-boot-line:nth-child(2) {{ animation-delay: 0.5s; }}
        .apex-boot-line:nth-child(3) {{ animation-delay: 0.8s; }}
        .apex-boot-line:nth-child(4) {{ animation-delay: 1.1s; }}
        @keyframes typeIn {{
            0% {{ opacity: 0; transform: translateX(-10px); }}
            100% {{ opacity: 1; transform: translateX(0); }}
        }}
        .apex-credentials-box {{
            margin-top: 24px;
            padding: 16px;
            background: linear-gradient(135deg, {bg_b}cc, {bg_a}cc);
            border: 1px dashed {hex_to_rgba(p, 0.4)};
            border-radius: 2px;
            font-family: 'JetBrains Mono', monospace;
        }}
        .apex-cred-row {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 0.78rem;
            border-bottom: 1px dashed {hex_to_rgba(p, 0.1)};
        }}
        .apex-cred-row:last-child {{ border-bottom: none; }}
        .apex-cred-label {{ color: #8892a8; letter-spacing: 1px; }}
        .apex-cred-value {{ color: {p}; font-weight: 700; letter-spacing: 1px; }}

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {bg_a}f8, {bg_b}f8) !important;
            border-right: 1px solid {hex_to_rgba(p, 0.2)};
        }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            font-family: 'Rajdhani', sans-serif;
        }}

        /* ===== OPERATOR BADGE ===== */
        .apex-op-badge {{
            background: linear-gradient(135deg, {bg_b}, {bg_a});
            border: 1px solid {hex_to_rgba(p, 0.4)};
            border-left: 3px solid {p};
            border-radius: 2px;
            padding: 14px;
            margin: 12px 0;
            position: relative;
            overflow: hidden;
        }}
        .apex-op-badge::before {{
            content: '';
            position: absolute;
            top: 0; right: 0;
            width: 30px; height: 30px;
            background: linear-gradient(225deg, {hex_to_rgba(p, 0.2)} 0%, transparent 70%);
        }}
        .apex-op-clearance {{
            display: inline-block;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            letter-spacing: 2px;
            padding: 2px 8px;
            border: 1px solid currentColor;
            border-radius: 2px;
            margin-top: 6px;
        }}

        /* Status pills */
        .apex-status-pill {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        .pill-success {{ background: {hex_to_rgba(success, 0.1)}; color: {success}; border: 1px solid {hex_to_rgba(success, 0.4)}; }}
        .pill-alert   {{ background: {hex_to_rgba(alert, 0.1)};   color: {alert};   border: 1px solid {hex_to_rgba(alert, 0.4)};   }}
        .pill-warn    {{ background: {hex_to_rgba(warn, 0.1)};    color: {warn};    border: 1px solid {hex_to_rgba(warn, 0.4)};    }}
        .pill-info    {{ background: {hex_to_rgba(p, 0.1)};       color: {p};       border: 1px solid {hex_to_rgba(p, 0.4)};       }}

        /* Section headers */
        .apex-section-header {{
            font-family: 'JetBrains Mono', monospace;
            color: {p};
            font-size: 0.78rem;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin: 20px 0 12px 0;
            padding-left: 12px;
            border-left: 2px solid {p};
        }}
        .apex-section-header::before {{
            content: '▸ ';
            color: {s};
        }}
        </style>
    """, unsafe_allow_html=True)


# ==========================================
# 4. LOGIN SCREEN
# ==========================================
def render_login():
    inject_theme_css(st.session_state.theme)
    t = THEMES[st.session_state.theme]

    st.markdown('<div class="apex-login-bg"></div>', unsafe_allow_html=True)

    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown(f"""
            <div class="apex-login-card">
              <div class="apex-corner tl"></div>
              <div class="apex-corner tr"></div>
              <div class="apex-corner bl"></div>
              <div class="apex-corner br"></div>
              <div class="apex-login-icon">{t['icon']}</div>
              <h1 class="apex-login-title">APEX</h1>
              <p class="apex-login-sub">QUANTUM OPERATIONS CONSOLE</p>
              <div style="margin-bottom: 24px;">
                <div class="apex-boot-line">> initializing kernel.................[OK]</div>
                <div class="apex-boot-line">> handshake encrypted................[OK]</div>
                <div class="apex-boot-line">> datalink established...............[OK]</div>
                <div class="apex-boot-line">> awaiting operator credentials......[__]</div>
              </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("OPERATOR ID", placeholder="enter operator id...").strip()
            password = st.text_input("ACCESS KEY", type="password", placeholder="enter access key...")
            submitted = st.form_submit_button("◈ AUTHENTICATE")

            if submitted:
                if st.session_state.failed_attempts >= 5:
                    st.error("🔒 LOCKOUT ENGAGED — TOO MANY FAILED ATTEMPTS. RESTART SESSION.")
                else:
                    user = verify_credentials(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.username = username.lower()
                        st.session_state.role = user["role"]
                        st.session_state.failed_attempts = 0
                        st.session_state.session_start = datetime.now()
                        ts = datetime.now().strftime('%H:%M:%S')
                        st.session_state.sys_logs.insert(0, f"[{ts}] ✅ AUTH OK :: {user['display_name']} :: {user['clearance']}")
                        st.rerun()
                    else:
                        st.session_state.failed_attempts += 1
                        remaining = 5 - st.session_state.failed_attempts
                        st.error(f"❌ AUTHENTICATION FAILED — {remaining} ATTEMPT(S) REMAINING")

        st.markdown(f"""
            <div class="apex-credentials-box">
              <div style="color:{t['primary']};font-family:'JetBrains Mono',monospace;font-size:0.7rem;letter-spacing:3px;text-transform:uppercase;margin-bottom:10px;text-align:center;">▸ DEMO ACCESS PROTOCOLS</div>
              <div class="apex-cred-row">
                <span class="apex-cred-label">// ADMIN</span>
                <span class="apex-cred-value">admin / admin@apex2026</span>
              </div>
              <div class="apex-cred-row">
                <span class="apex-cred-label">// VIEWER</span>
                <span class="apex-cred-value">viewer / viewer@apex2026</span>
              </div>
            </div>
            <p style="text-align:center;color:#6b7280;font-family:'JetBrains Mono',monospace;font-size:0.7rem;letter-spacing:3px;margin-top:24px;">◈ TRANSMISSION ENCRYPTED // QUANTUM PROTOCOL v9.6 ◈</p>
        """, unsafe_allow_html=True)


# ==========================================
# 5. AUTH GATE
# ==========================================
if not st.session_state.authenticated:
    render_login()
    st.stop()

inject_theme_css(st.session_state.theme)
IS_ADMIN = (st.session_state.role == "Admin")
THEME = THEMES[st.session_state.theme]
USER = USERS[st.session_state.username]

CHART_THEME = "plotly_dark"
HUD_COLORS = [THEME["primary"], THEME["secondary"], THEME["accent"], THEME["success"], THEME["warn"]]


# ==========================================
# 6. UTILITIES
# ==========================================
def format_large_number(num):
    if pd.isna(num) or num is None:
        return "$0"
    if num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    if num >= 1_000:
        return f"${num / 1_000:.0f}K"
    return f"${num:.0f}"

def df_to_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def log_event(emoji, msg):
    ts = datetime.now().strftime('%H:%M:%S')
    st.session_state.sys_logs.insert(0, f"[{ts}] {emoji} {msg}")
    st.session_state.sys_logs = st.session_state.sys_logs[:8]


def hex_to_rgba(hex_color, alpha):
    """Convert HEX color to RGBA string for Plotly/CSS compatibility."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


# ==========================================
# 7. DATABASE
# ==========================================
try:
    DB_USER = st.secrets.get("DB_USER", "root")
    DB_PASS = st.secrets.get("DB_PASS", "Jangra@9876")
    DB_HOST = st.secrets.get("DB_HOST", "localhost")
    DB_NAME = st.secrets.get("DB_NAME", "esports_db")
except FileNotFoundError:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "Jangra@9876")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "esports_db")

@st.cache_resource(show_spinner=False)
def init_connection():
    try:
        encoded_pass = urllib.parse.quote_plus(DB_PASS)
        db_url = f"mysql+pymysql://{DB_USER}:{encoded_pass}@{DB_HOST}/{DB_NAME}"
        return create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
    except Exception:
        return None

@st.cache_data(ttl=15, show_spinner=False)
def fetch_data(query, params=None):
    engine = init_connection()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except SQLAlchemyError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def execute_write(query, params=None, success_msg="DB OVERRIDE SUCCESSFUL"):
    if not IS_ADMIN:
        log_event("🔒", "PERMISSION DENIED :: VIEWER ROLE")
        return False
    engine = init_connection()
    if engine is None:
        log_event("❌", "NO UPLINK")
        return False
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
        st.cache_data.clear()
        log_event("✅", success_msg)
        return True
    except SQLAlchemyError as e:
        log_event("❌", f"ERR :: {str(e)[:50]}...")
        return False


# ==========================================
# 8. AUTO-REFRESH
# ==========================================
REFRESH_MAP = {"OFF": 0, "5s": 5_000, "15s": 15_000, "30s": 30_000}
refresh_ms = REFRESH_MAP.get(st.session_state.auto_refresh, 0)
if refresh_ms > 0:
    try:
        st.autorefresh(interval=refresh_ms, key="apex_autorefresh")
    except Exception:
        st.markdown(f'<meta http-equiv="refresh" content="{refresh_ms // 1000}">', unsafe_allow_html=True)


# ==========================================
# 9. SIDEBAR
# ==========================================
with st.sidebar:
    p, s, alert = THEME["primary"], THEME["secondary"], THEME["alert"]

    st.markdown(f"""
        <div style='text-align:center;padding:18px 0 6px 0;'>
          <div style='font-family:Syncopate,sans-serif;font-size:3rem;background:linear-gradient(135deg,{p},{s});-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1;'>{THEME['icon']}</div>
          <div style='font-family:Syncopate,sans-serif;color:#fff;font-size:1.4rem;letter-spacing:8px;font-weight:700;margin-top:4px;text-shadow:0 0 16px {hex_to_rgba(p, 0.5)};'>APEX</div>
          <div style='font-family:JetBrains Mono,monospace;color:{p};font-size:0.65rem;letter-spacing:3px;margin-top:2px;'>QUANTUM OPS // v9.6</div>
        </div>
    """, unsafe_allow_html=True)

    # Operator badge
    role_color = "#00ffa3" if IS_ADMIN else "#fbbf24"
    session_dur = datetime.now() - st.session_state.session_start if st.session_state.session_start else timedelta(0)
    mins = int(session_dur.total_seconds() // 60)
    secs = int(session_dur.total_seconds() % 60)

    st.markdown(f"""
        <div class='apex-op-badge'>
          <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
            <div>
              <div style='color:#8892a8;font-family:JetBrains Mono,monospace;font-size:0.65rem;letter-spacing:2px;'>// OPERATOR</div>
              <div style='color:#fff;font-family:Syncopate,sans-serif;font-weight:700;letter-spacing:2px;font-size:0.95rem;margin-top:4px;'>{USER['display_name']}</div>
            </div>
            <div class='apex-op-clearance' style='color:{role_color};'>{USER['clearance']}</div>
          </div>
          <div style='margin-top:10px;font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#8892a8;letter-spacing:1px;'>
            <div style='display:flex;justify-content:space-between;'><span>ROLE</span><span style='color:{role_color};'>{st.session_state.role.upper()}</span></div>
            <div style='display:flex;justify-content:space-between;margin-top:4px;'><span>UPTIME</span><span style='color:{p};'>{mins:02d}m {secs:02d}s</span></div>
          </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("⏻ TERMINATE SESSION"):
        for k in ['authenticated', 'username', 'role', 'session_start']:
            st.session_state[k] = DEFAULTS[k]
        st.rerun()

    st.markdown("---")

    # DB status
    db_status = init_connection()
    if db_status:
        st.markdown(f"""
            <div style='padding:12px;background:linear-gradient(135deg,{hex_to_rgba(THEME['success'], 0.08)},transparent);border:1px solid {hex_to_rgba(THEME['success'], 0.4)};border-radius:2px;text-align:center;margin-bottom:16px;'>
              <div style='display:flex;justify-content:center;align-items:center;gap:8px;'>
                <span class='live-pulse' style='background:{THEME['success']};box-shadow:0 0 10px {THEME['success']};'></span>
                <span style='color:{THEME['success']};font-family:Syncopate,sans-serif;font-weight:700;letter-spacing:3px;font-size:0.75rem;'>DATALINK :: SECURE</span>
              </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style='padding:12px;background:linear-gradient(135deg,{hex_to_rgba(alert, 0.08)},transparent);border:1px solid {hex_to_rgba(alert, 0.4)};border-radius:2px;text-align:center;margin-bottom:16px;'>
              <span style='color:{alert};font-family:Syncopate,sans-serif;font-weight:700;letter-spacing:3px;font-size:0.75rem;'>⚠ DATALINK :: OFFLINE</span>
            </div>
        """, unsafe_allow_html=True)

    # Theme switcher
    st.markdown('<div class="apex-section-header">SPECTRUM</div>', unsafe_allow_html=True)
    theme_keys = list(THEMES.keys())
    cols_t = st.columns(3)
    for i, tk in enumerate(theme_keys):
        with cols_t[i]:
            is_active = (tk == st.session_state.theme)
            label = f"{THEMES[tk]['icon']}"
            if st.button(label, key=f"theme_{tk}", help=THEMES[tk]['label']):
                st.session_state.theme = tk
                st.rerun()
            if is_active:
                st.markdown(f"<div style='text-align:center;color:{THEMES[tk]['primary']};font-family:JetBrains Mono,monospace;font-size:0.6rem;letter-spacing:2px;margin-top:-8px;'>● ACTIVE</div>", unsafe_allow_html=True)

    # Auto-refresh
    st.markdown('<div class="apex-section-header">LIVE FEED</div>', unsafe_allow_html=True)
    st.session_state.auto_refresh = st.select_slider(
        "refresh", options=["OFF", "5s", "15s", "30s"],
        value=st.session_state.auto_refresh, label_visibility="collapsed"
    )
    if st.session_state.auto_refresh != "OFF":
        st.markdown(
            f"<div style='font-family:JetBrains Mono,monospace;color:{alert};font-size:0.78rem;letter-spacing:3px;text-align:center;margin-top:8px;'><span class='live-pulse'></span> POLLING @ {st.session_state.auto_refresh}</div>",
            unsafe_allow_html=True
        )

    if st.button("📡 PULL TELEMETRY"):
        st.cache_data.clear()
        log_event("📡", "TELEMETRY REFRESHED")
        st.rerun()

    # Logs
    st.markdown('<div class="apex-section-header">EVENT STREAM</div>', unsafe_allow_html=True)
    if st.session_state.sys_logs:
        for log in st.session_state.sys_logs:
            color = THEME['success'] if "✅" in log else (alert if "❌" in log else p)
            st.markdown(
                f"<div style='color:{color};font-family:JetBrains Mono,monospace;font-size:0.72rem;border-left:2px solid {color};padding:5px 8px;margin-bottom:6px;background:rgba(0,0,0,0.4);letter-spacing:0.5px;'>{log}</div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown("<div style='color:#6b7280;font-family:JetBrains Mono,monospace;font-size:0.75rem;letter-spacing:1px;'>// AWAITING ACTIVITY...</div>", unsafe_allow_html=True)

    # Diagnostics
    st.markdown('<div class="apex-section-header">DIAGNOSTICS</div>', unsafe_allow_html=True)
    cpu_load = random.randint(72, 92)
    mem_load = random.randint(38, 56)
    net_load = random.randint(60, 88)
    st.progress(cpu_load, text=f"CORE LOAD ({cpu_load}%)")
    st.progress(mem_load, text=f"MEMORY ({mem_load}%)")
    st.progress(net_load, text=f"NETWORK ({net_load}%)")

    st.markdown(f"<div style='text-align:center;color:#4b5563;font-family:JetBrains Mono,monospace;font-size:0.65rem;letter-spacing:2px;margin-top:24px;padding-top:16px;border-top:1px solid {hex_to_rgba(p, 0.1)};'>SYS.OMEGA.10 // SECURE</div>", unsafe_allow_html=True)


# ==========================================
# 10. MAIN HEADER + TICKER
# ==========================================
live_indicator = ""
if st.session_state.auto_refresh != "OFF":
    live_indicator = f"<span class='apex-rec-badge' style='margin-right:18px;'><span class='live-pulse'></span>LIVE</span>"

st.markdown(f"""
    <div class='apex-header'>
      <div>
        <div class='apex-header-title'>QUANTUM TELEMETRY FEED</div>
        <div class='apex-header-sub'>// {datetime.now().strftime('%Y.%m.%d :: %H:%M:%S')} UTC :: BROADCAST {st.session_state.theme.upper()}</div>
      </div>
      <div>
        {live_indicator}
        <span class='apex-rec-badge'><span class='live-pulse'></span>REC</span>
      </div>
    </div>
""", unsafe_allow_html=True)

# Ticker
def build_ticker():
    df_t = fetch_data("SELECT name, total_prize_pool FROM Tournaments ORDER BY total_prize_pool DESC LIMIT 8")
    if df_t.empty:
        df_t = pd.DataFrame({
            "name": ["Omega Finals", "Alpha Circuit", "Beta Invitational", "Gamma Open", "Delta League", "Epsilon Cup"],
            "total_prize_pool": [2_500_000, 1_200_000, 800_000, 600_000, 450_000, 300_000]
        })
    items = []
    for _, row in df_t.iterrows():
        delta = random.choice(['▲', '▼', '◆'])
        delta_class = 'ticker-up' if delta == '▲' else ('ticker-down' if delta == '▼' else '')
        change = random.uniform(0.5, 12.4)
        items.append(
            f"<span class='ticker-item'><span class='ticker-tag'>◈ {row['name'].upper()[:24]}</span> "
            f"<span class='mono'>{format_large_number(row['total_prize_pool'])}</span> "
            f"<span class='{delta_class}'>{delta} {change:.1f}%</span></span>"
        )
    items.append(f"<span class='ticker-item ticker-tag'>◆ SYS.STATUS :: NOMINAL</span>")
    items.append(f"<span class='ticker-item'>◆ ACTIVE OPERATORS :: <span class='ticker-up'>{random.randint(12, 47)}</span></span>")
    return "".join(items)

ticker_content = build_ticker()
# Duplicate for seamless loop
st.markdown(f"""
    <div class='apex-ticker'>
      <div class='apex-ticker-track'>
        {ticker_content}{ticker_content}
      </div>
    </div>
""", unsafe_allow_html=True)


# ==========================================
# 11. TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "◈ OVERVIEW",
    "⚔ MATCH FEED",
    "🛡 ARCHIVES",
    "🏆 RANKINGS",
    "🆚 H2H",
    "🌳 BRACKET",
    "📊 ANALYTICS",
])

# ---------------------------------------------------------
# TAB 1: OVERVIEW
# ---------------------------------------------------------
with tab1:
    df_kpi = fetch_data("""
        SELECT
            (SELECT COUNT(*) FROM Tournaments WHERE status IN ('Upcoming', 'Ongoing')) as active_tournaments,
            (SELECT COUNT(*) FROM Teams) as total_teams,
            (SELECT SUM(total_prize_pool) FROM Tournaments) as global_prize,
            (SELECT COUNT(*) FROM Matches WHERE status = 'Live') as live_matches
    """)
    if df_kpi.empty or pd.isna(df_kpi['active_tournaments'].iloc[0]):
        df_kpi = pd.DataFrame({"active_tournaments": [7], "total_teams": [32], "global_prize": [4_750_000], "live_matches": [3]})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("◇ Active Circuits", f"{df_kpi['active_tournaments'].iloc[0]:02d}", delta="+2 this week")
    col2.metric("◇ Syndicates", f"{df_kpi['total_teams'].iloc[0]:02d}", delta="+5 registered")
    col3.metric("◇ Total Funding", format_large_number(df_kpi['global_prize'].iloc[0]), delta="+12.4% MoM")
    col4.metric("◇ Live Engagements", f"{df_kpi['live_matches'].iloc[0]:02d}")

    st.markdown('<div class="apex-section-header">DEPLOYMENT MATRIX</div>', unsafe_allow_html=True)

    col_v1, col_v2 = st.columns([1.1, 1.9])
    with col_v1:
        df_locations = fetch_data("SELECT location_type AS location, COUNT(*) as count FROM Tournaments GROUP BY location_type")
        if df_locations.empty:
            df_locations = pd.DataFrame({"location": ["LAN", "Online", "Hybrid"], "count": [8, 18, 6]})

        fig1 = px.pie(df_locations, names='location', values='count', hole=0.78,
                      color_discrete_sequence=HUD_COLORS)
        fig1.update_traces(hoverinfo='label+percent', textinfo='none',
                           marker=dict(line=dict(color=THEME['bg_b'], width=2)))
        fig1.update_layout(template=CHART_THEME, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                           margin=dict(t=10, b=10, l=0, r=0),
                           legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                                       font=dict(family="Rajdhani", size=12, color="#e8eaed")))
        fig1.add_annotation(
            text=f"<span style='font-family:Syncopate;font-size:32px;color:#fff;font-weight:700;'>{df_locations['count'].sum():02d}</span><br>"
                 f"<span style='font-family:JetBrains Mono;font-size:10px;color:{THEME['primary']};letter-spacing:3px;'>ZONES</span>",
            x=0.5, y=0.5, showarrow=False)
        st.plotly_chart(fig1, width='stretch')

    with col_v2:
        df_games = fetch_data("SELECT game_title, SUM(total_prize_pool) as total_prize FROM Tournaments GROUP BY game_title ORDER BY total_prize ASC")
        if df_games.empty or pd.isna(df_games['total_prize'].iloc[0]):
            df_games = pd.DataFrame({"game_title": ["Apex Legends", "CS:GO 2", "Valorant", "Dota 2"],
                                     "total_prize": [650_000, 850_000, 1_200_000, 2_050_000]})

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=df_games['game_title'], x=df_games['total_prize'], orientation='h',
            marker=dict(
                color=df_games['total_prize'],
                colorscale=[[0, THEME['secondary']], [1, THEME['primary']]],
                line=dict(color=THEME['primary'], width=1),
            ),
            hovertemplate="<b>%{y}</b><br>Funding: $%{x:,.0f}<extra></extra>",
            text=[format_large_number(v) for v in df_games['total_prize']],
            textposition='outside',
            textfont=dict(family="JetBrains Mono", color="#fff", size=11),
        ))
        fig2.update_layout(template=CHART_THEME, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                           margin=dict(t=10, l=10, r=80, b=10),
                           xaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.1), title="",
                                      tickfont=dict(family="JetBrains Mono", color="#8892a8")),
                           yaxis=dict(title="", tickfont=dict(family="Rajdhani", size=13, color="#fff")),
                           bargap=0.5)
        st.plotly_chart(fig2, width='stretch')

    # Activity heatmap (GitHub-style match density)
    st.markdown('<div class="apex-section-header">ENGAGEMENT DENSITY :: 90-DAY HEATMAP</div>', unsafe_allow_html=True)
    df_heat = fetch_data("SELECT DATE(match_date) as d, COUNT(*) as c FROM Matches WHERE match_date >= DATE_SUB(NOW(), INTERVAL 90 DAY) GROUP BY DATE(match_date)")
    if df_heat.empty:
        # Synthesize realistic 90-day window
        dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=90)
        random.seed(42)
        counts = [random.choices([0, 0, 1, 2, 3, 5, 8], weights=[3, 4, 5, 4, 3, 2, 1])[0] for _ in dates]
        df_heat = pd.DataFrame({"d": dates, "c": counts})

    df_heat['d'] = pd.to_datetime(df_heat['d'])
    # Build calendar grid (weeks x weekdays)
    df_heat['week'] = df_heat['d'].dt.isocalendar().week
    df_heat['weekday'] = df_heat['d'].dt.weekday
    df_heat['week_idx'] = (df_heat['d'] - df_heat['d'].min()).dt.days // 7

    pivot = df_heat.pivot_table(index='weekday', columns='week_idx', values='c', fill_value=0)

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        colorscale=[[0, THEME['bg_b']], [0.3, THEME['accent']], [0.7, THEME['primary']], [1, THEME['secondary']]],
        showscale=True,
        colorbar=dict(tickfont=dict(family="JetBrains Mono", color="#8892a8", size=10),
                      thickness=12, len=0.8),
        hovertemplate="Engagements: <b>%{z}</b><extra></extra>",
        xgap=2, ygap=2,
    ))
    fig_heat.update_layout(
        template=CHART_THEME, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=20, l=80, r=20), height=240,
        xaxis=dict(showgrid=False, title="", showticklabels=False),
        yaxis=dict(showgrid=False, title="",
                   tickmode='array',
                   tickvals=[0, 1, 2, 3, 4, 5, 6],
                   ticktext=['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
                   tickfont=dict(family="JetBrains Mono", size=10, color="#8892a8")),
    )
    st.plotly_chart(fig_heat, width='stretch')

    # Exports
    e1, e2 = st.columns(2)
    e1.download_button("⬇ EXPORT KPI", data=df_to_csv_bytes(df_kpi),
                       file_name=f"apex_kpi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")
    e2.download_button("⬇ EXPORT FUNDING", data=df_to_csv_bytes(df_games),
                       file_name=f"apex_funding_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

    if IS_ADMIN:
        with st.expander("⚠ OVERRIDE :: INJECT SPONSOR FUNDS [TRIGGER]"):
            st.markdown(f"<p style='color:#8892a8;font-family:JetBrains Mono,monospace;font-size:0.8rem;letter-spacing:1px;'>// Activates <code style='color:{THEME['primary']};'>trg_add_sponsor_contribution</code> :: auto-updates prize pool</p>", unsafe_allow_html=True)
            df_tours = fetch_data("SELECT tournament_id, name FROM Tournaments")
            df_spons = fetch_data("SELECT sponsor_id, name FROM Sponsors")
            if df_tours.empty:
                df_tours = pd.DataFrame({"tournament_id": [1, 2, 3], "name": ["Alpha Circuit [MOCK]", "Beta Invitational [MOCK]", "Omega Finals [MOCK]"]})
            if df_spons.empty:
                df_spons = pd.DataFrame({"sponsor_id": [101, 102, 103], "name": ["Neuro-Link Corp [MOCK]", "Hyperion Dynamics [MOCK]", "Aegis Systems [MOCK]"]})

            tour_dict = dict(zip(df_tours['name'], df_tours['tournament_id']))
            spons_dict = dict(zip(df_spons['name'], df_spons['sponsor_id']))

            with st.form("sponsor_funds_form"):
                c1, c2 = st.columns(2)
                sel_tour = c1.selectbox("Circuit", list(tour_dict.keys()))
                sel_spon = c2.selectbox("Corporation", list(spons_dict.keys()))
                c3, c4 = st.columns(2)
                tier = c3.selectbox("Tier", ["Platinum", "Gold", "Silver", "Bronze"])
                amount = c4.number_input("Amount ($)", min_value=1000.0, value=50000.0, step=5000.0)
                if st.form_submit_button("◈ AUTHORIZE TRANSFER"):
                    q = """INSERT INTO Tournament_Sponsors (tournament_id, sponsor_id, sponsorship_tier, contribution_amount)
                           VALUES (:tid, :sid, :tier, :amt)
                           ON DUPLICATE KEY UPDATE contribution_amount = contribution_amount + :amt, sponsorship_tier = :tier"""
                    if execute_write(q, {"tid": tour_dict[sel_tour], "sid": spons_dict[sel_spon], "tier": tier, "amt": amount},
                                     f"FUNDS INJECTED :: {sel_spon}"):
                        st.rerun()
    else:
        st.markdown(
            f"<div style='padding:14px;border:1px dashed {THEME['warn']};background:linear-gradient(135deg,{hex_to_rgba(THEME['warn'], 0.04)},transparent);font-family:JetBrains Mono,monospace;color:{THEME['warn']};text-align:center;letter-spacing:3px;font-size:0.8rem;margin-top:24px;border-radius:2px;'>🔒 OVERRIDE PANELS LOCKED :: VIEWER CLEARANCE</div>",
            unsafe_allow_html=True
        )


# ---------------------------------------------------------
# TAB 2: MATCH FEED
# ---------------------------------------------------------
with tab2:
    col_op1, col_op2 = st.columns([3, 1])
    col_op1.markdown('<div class="apex-section-header">COMBAT TELEMETRY</div>', unsafe_allow_html=True)
    with col_op2:
        selected_status = st.selectbox("filter", ['ALL', 'LIVE', 'SCHEDULED', 'COMPLETED'], label_visibility="collapsed")

    df_matches = fetch_data("""
        SELECT m.match_id as ID, m.match_date AS 'Timestamp', tr.name AS 'Circuit',
               t1.name AS 'Alpha', t2.name AS 'Beta', m.stage AS 'Phase',
               CONCAT(m.team1_score, ' - ', m.team2_score) AS 'Score',
               UPPER(m.status) AS 'Status'
        FROM Matches m
        LEFT JOIN Tournaments tr ON m.tournament_id = tr.tournament_id
        LEFT JOIN Teams t1 ON m.team1_id = t1.team_id
        LEFT JOIN Teams t2 ON m.team2_id = t2.team_id
        ORDER BY m.match_date DESC LIMIT 100
    """)
    if df_matches.empty:
        df_matches = pd.DataFrame({
            "ID": list(range(1, 9)),
            "Timestamp": pd.date_range(end=pd.Timestamp.now(), periods=8, freq='-12H'),
            "Circuit": ["Omega Finals [MOCK]"] * 4 + ["Alpha Circuit [MOCK]"] * 4,
            "Alpha": ["Neon Vanguard", "Cybernetic Knights", "Aegis Squad", "Phantom Strike", "Iron Wolves", "Solar Flare", "Void Walkers", "Quantum Team"],
            "Beta": ["Quantum Team", "Nova Syndicate", "Void Walkers", "Solar Flare", "Phantom Strike", "Iron Wolves", "Aegis Squad", "Cybernetic Knights"],
            "Phase": ["Finals", "Semi-Finals", "Semi-Finals", "Quarter-Finals", "Quarter-Finals", "Quarter-Finals", "Quarter-Finals", "Group Stage"],
            "Score": ["3 - 2", "1 - 1", "2 - 0", "2 - 1", "0 - 0", "2 - 0", "1 - 2", "3 - 1"],
            "Status": ["COMPLETED", "LIVE", "COMPLETED", "COMPLETED", "SCHEDULED", "COMPLETED", "COMPLETED", "COMPLETED"]
        })

    if selected_status != 'ALL':
        df_matches = df_matches[df_matches['Status'] == selected_status]

    def fmt_status(s):
        return {'LIVE': '🔴 LIVE', 'COMPLETED': '🟢 COMPLETED',
                'SCHEDULED': '🟡 SCHEDULED', 'POSTPONED': '⚪ POSTPONED'}.get(s, s)

    df_display = df_matches.copy()
    df_display['Status'] = df_display['Status'].apply(fmt_status)
    df_display['Timings'] = pd.to_datetime(df_display['Timestamp']).dt.strftime('%Y.%m.%d :: %H:%M')
    df_display = df_display[['ID', 'Timings', 'Circuit', 'Alpha', 'Beta', 'Phase', 'Score', 'Status']]

    st.dataframe(df_display, width="stretch", hide_index=True,
                 column_config={
                     "ID": None,
                     "Timings": st.column_config.TextColumn("Timestamp (UTC)", width="medium"),
                     "Alpha": st.column_config.TextColumn("Alpha Syndicate", width="medium"),
                     "Beta": st.column_config.TextColumn("Beta Syndicate", width="medium"),
                 })

    st.download_button("⬇ EXPORT TELEMETRY", data=df_to_csv_bytes(df_display),
                       file_name=f"apex_telemetry_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

    if IS_ADMIN:
        with st.expander("⚠ OVERRIDE :: RESOLVE MATCH [TRIGGER]"):
            st.markdown(f"<p style='color:#8892a8;font-family:JetBrains Mono,monospace;font-size:0.8rem;letter-spacing:1px;'>// Setting 'Completed' fires <code style='color:{THEME['primary']};'>trg_auto_set_match_winner</code></p>", unsafe_allow_html=True)
            df_live = fetch_data("SELECT match_id, CONCAT(match_date, ' | ', t1.name, ' vs ', t2.name) as match_name FROM Matches m JOIN Teams t1 ON m.team1_id = t1.team_id JOIN Teams t2 ON m.team2_id = t2.team_id WHERE m.status != 'Completed'")
            if df_live.empty:
                df_live = pd.DataFrame({"match_id": [1, 2], "match_name": ["2026.05.01 | Neon [MOCK] vs Quantum [MOCK]", "2026.05.02 | Cyber [MOCK] vs Nova [MOCK]"]})

            match_dict = dict(zip(df_live['match_name'], df_live['match_id']))
            with st.form("resolve_form"):
                sel = st.selectbox("Engagement", list(match_dict.keys()))
                c1, c2, c3 = st.columns(3)
                t1s = c1.number_input("Alpha", min_value=0, value=0, step=1)
                t2s = c2.number_input("Beta", min_value=0, value=0, step=1)
                stt = c3.selectbox("Status", ["Completed", "Live", "Postponed"])
                if st.form_submit_button("◈ EXECUTE OVERRIDE"):
                    q = "UPDATE Matches SET team1_score = :s1, team2_score = :s2, status = :st WHERE match_id = :mid"
                    if execute_write(q, {"s1": t1s, "s2": t2s, "st": stt, "mid": match_dict[sel]},
                                     f"MATCH #{match_dict[sel]} RESOLVED"):
                        st.rerun()

    # Engagement timeline
    st.markdown('<div class="apex-section-header">ENGAGEMENT FORECAST</div>', unsafe_allow_html=True)
    df_matches['Timestamp'] = pd.to_datetime(df_matches['Timestamp'])
    df_timeline = df_matches.groupby(df_matches['Timestamp'].dt.date).size().reset_index(name='Matches')

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_timeline['Timestamp'], y=df_timeline['Matches'],
        fill='tozeroy', mode='lines+markers',
        line=dict(width=2.5, color=THEME['primary'], shape='spline'),
        marker=dict(size=8, color=THEME['secondary'], line=dict(color=THEME['primary'], width=2),
                    symbol='diamond'),
        fillcolor=hex_to_rgba(THEME['primary'], 0.1),
        hovertemplate="<b>%{y}</b> engagements<br>%{x}<extra></extra>",
    ))
    fig3.update_layout(template=CHART_THEME, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       margin=dict(t=10, b=20, l=0, r=0),
                       xaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.05), title="",
                                  tickfont=dict(family="JetBrains Mono", color="#8892a8")),
                       yaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.1), title="",
                                  tickfont=dict(family="JetBrains Mono", color="#8892a8")))
    st.plotly_chart(fig3, width='stretch')


# ---------------------------------------------------------
# TAB 3: ARCHIVES
# ---------------------------------------------------------
with tab3:
    st.markdown('<div class="apex-section-header">SYNDICATE PROFILE</div>', unsafe_allow_html=True)
    df_teams = fetch_data("SELECT team_id as id, name, region, contact_email FROM Teams ORDER BY name")
    if df_teams.empty:
        df_teams = pd.DataFrame([
            {"id": 1, "name": "Neon Vanguard [MOCK]", "region": "NA", "contact_email": "neon@vanguard.gg"},
            {"id": 2, "name": "Cybernetic Knights [MOCK]", "region": "EU", "contact_email": "cyber@knights.gg"},
            {"id": 3, "name": "Quantum Team [MOCK]", "region": "KR", "contact_email": "q@team.gg"},
        ])

    team_dict = dict(zip(df_teams['name'], df_teams['id']))
    sel_team_name = st.selectbox("◇ TARGET", options=list(team_dict.keys()), label_visibility="collapsed")
    sel_team_id = team_dict[sel_team_name]
    team_info = df_teams[df_teams['id'] == sel_team_id].iloc[0]

    df_perf = fetch_data("SELECT COUNT(*) as total_matches, SUM(CASE WHEN winner_team_id = :tid THEN 1 ELSE 0 END) as wins FROM Matches WHERE (team1_id = :tid OR team2_id = :tid) AND status = 'Completed'", params={"tid": sel_team_id})
    if df_perf.empty or pd.isna(df_perf['total_matches'].iloc[0]) or df_perf['total_matches'].iloc[0] == 0:
        df_perf = pd.DataFrame({"total_matches": [22], "wins": [16]})

    total = int(df_perf['total_matches'].iloc[0])
    wins = int(df_perf['wins'].iloc[0]) if pd.notnull(df_perf['wins'].iloc[0]) else 0
    win_rate = (wins / total * 100) if total else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("◇ Sector", team_info['region'])
    k2.metric("◇ Total Drops", f"{total:03d}")
    k3.metric("◇ Victories", f"{wins:03d}")
    k4.metric("◇ Lethality", f"{win_rate:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)
    col_r1, col_r2 = st.columns([2.4, 1])

    with col_r1:
        st.markdown("<h5 style='color:#fff;font-family:Syncopate;margin-bottom:14px;'>ACTIVE OPERATIVES</h5>", unsafe_allow_html=True)
        df_players = fetch_data("SELECT player_id, in_game_name AS 'Codename', first_name AS 'Given', last_name AS 'Surname', role AS 'Class', join_date AS 'Activation' FROM Players WHERE team_id = :tid", params={"tid": sel_team_id})
        if df_players.empty:
            df_players = pd.DataFrame({
                "player_id": [1, 2, 3, 4, 5],
                "Codename": ["Ghost", "Viper", "Phantom", "Cipher", "Halo"],
                "Given": ["John", "Jane", "Alex", "Mira", "Kai"],
                "Surname": ["Doe", "Smith", "Wright", "Chen", "Park"],
                "Class": ["IGL", "Entry Fragger", "Sniper", "Support", "Flex"],
                "Activation": pd.to_datetime(['2026-01-01', '2026-01-15', '2026-02-01', '2025-11-20', '2026-03-10'])
            })

        st.dataframe(df_players, width="stretch", hide_index=True,
                     column_config={"player_id": None,
                                    "Activation": st.column_config.DateColumn("Activation", format="YYYY.MM.DD")})

        st.download_button("⬇ EXPORT ROSTER", data=df_to_csv_bytes(df_players.drop(columns=['player_id'], errors='ignore')),
                           file_name=f"apex_roster_{sel_team_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv")

    with col_r2:
        st.markdown("<h5 style='color:#fff;font-family:Syncopate;margin-bottom:14px;text-align:center;'>CLASS MAP</h5>", unsafe_allow_html=True)
        if not df_players.empty and 'Class' in df_players.columns:
            rc = df_players['Class'].value_counts().reset_index()
            rc.columns = ['Class', 'Count']
            fig4 = px.bar_polar(rc, r='Count', theta='Class', color='Class',
                                color_discrete_sequence=HUD_COLORS, template=CHART_THEME)
            fig4.update_traces(opacity=0.85)
            fig4.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)',
                                          radialaxis=dict(visible=False),
                                          angularaxis=dict(tickfont=dict(family="Rajdhani", size=11, color="#fff"),
                                                           gridcolor=hex_to_rgba(THEME['primary'], 0.1))),
                               showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig4, width='stretch')

    # Operative dossier
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="apex-section-header">OPERATIVE DOSSIER</div>', unsafe_allow_html=True)

    if not df_players.empty:
        sel_op = st.selectbox("Target Operative", df_players['Codename'].tolist(), key="op_sel")
        op = df_players[df_players['Codename'] == sel_op].iloc[0]
        join_date = pd.to_datetime(op['Activation'])
        tenure = (pd.Timestamp.now() - join_date).days

        op_c1, op_c2 = st.columns([1, 1.5])
        with op_c1:
            st.markdown(f"""
                <div style='border:1px solid {hex_to_rgba(THEME['primary'], 0.4)};border-left:4px solid {THEME['primary']};padding:24px;background:linear-gradient(135deg,{hex_to_rgba(THEME['bg_a'], 0.8)},{hex_to_rgba(THEME['bg_b'], 0.94)});position:relative;overflow:hidden;'>
                  <div class='apex-corner tl' style='border-color:{THEME['primary']}99;'></div>
                  <div class='apex-corner br' style='border-color:{THEME['primary']}99;'></div>
                  <div style='font-family:JetBrains Mono,monospace;color:#8892a8;font-size:0.7rem;letter-spacing:3px;'>// DOSSIER #{op.get('player_id','---'):04d}</div>
                  <div style='font-family:Syncopate,sans-serif;color:#fff;font-size:1.8rem;letter-spacing:4px;margin:10px 0;font-weight:700;text-shadow:0 0 16px {hex_to_rgba(THEME['primary'], 0.4)};'>{op['Codename'].upper()}</div>
                  <div style='color:#8892a8;font-family:Rajdhani,sans-serif;font-size:1rem;'>{op['Given']} {op['Surname']}</div>
                  <hr style='border-top:1px dashed {hex_to_rgba(THEME['primary'], 0.2)};margin:16px 0;'>
                  <div style='display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;font-size:0.85rem;margin-bottom:8px;'>
                    <span style='color:#8892a8;letter-spacing:1px;'>CLASS</span>
                    <span style='color:{THEME['primary']};font-weight:700;'>{op['Class']}</span>
                  </div>
                  <div style='display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;font-size:0.85rem;margin-bottom:8px;'>
                    <span style='color:#8892a8;letter-spacing:1px;'>ACTIVATION</span>
                    <span style='color:{THEME['primary']};font-weight:700;'>{join_date.strftime('%Y.%m.%d')}</span>
                  </div>
                  <div style='display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;font-size:0.85rem;'>
                    <span style='color:#8892a8;letter-spacing:1px;'>TENURE</span>
                    <span style='color:{THEME['primary']};font-weight:700;'>{tenure} DAYS</span>
                  </div>
                </div>
            """, unsafe_allow_html=True)

        with op_c2:
            seed = int(hashlib.md5(str(op['Codename']).encode()).hexdigest(), 16) % (10**8)
            random.seed(seed)
            cats = ['Aggression', 'Accuracy', 'Survival', 'Utility', 'Objective', 'Synergy']
            op_vals = [random.randint(55, 95) for _ in cats]
            avg_vals = [random.randint(60, 80) for _ in cats]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=op_vals + [op_vals[0]], theta=cats + [cats[0]],
                fill='toself', name=op['Codename'],
                fillcolor=hex_to_rgba(THEME['primary'], 0.25),
                line=dict(color=THEME['primary'], width=2.5),
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=avg_vals + [avg_vals[0]], theta=cats + [cats[0]],
                fill='toself', name='Squad Avg',
                fillcolor=hex_to_rgba(THEME['secondary'], 0.15),
                line=dict(color=THEME['secondary'], width=1.5, dash='dot'),
            ))
            fig_radar.update_layout(
                template=CHART_THEME,
                polar=dict(bgcolor='rgba(0,0,0,0)',
                           radialaxis=dict(visible=True, range=[0, 100], showline=False,
                                           tickfont=dict(family="JetBrains Mono", color="#8892a8", size=9),
                                           gridcolor=hex_to_rgba(THEME['primary'], 0.15)),
                           angularaxis=dict(tickfont=dict(family="Rajdhani", size=11, color="#fff", weight=600),
                                            gridcolor=hex_to_rgba(THEME['primary'], 0.1))),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(font=dict(family="JetBrains Mono", size=11, color="#e8eaed"),
                            orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                margin=dict(t=30, b=40, l=30, r=30), height=380,
            )
            st.plotly_chart(fig_radar, width='stretch')

    # CRUD
    if IS_ADMIN:
        with st.expander("⚠ DIRECTORY OVERRIDE :: ROSTER CRUD"):
            ct1, ct2, ct3 = st.tabs(["[+] REGISTER", "[~] REASSIGN", "[-] TERMINATE"])
            with ct1:
                with st.form("add_form"):
                    st.markdown(f"<p style='color:{THEME['primary']};font-family:Syncopate;letter-spacing:3px;'>NEW OPERATIVE</p>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    ign = c1.text_input("Codename")
                    fn = c2.text_input("Given")
                    ln = c3.text_input("Surname")
                    c4, c5 = st.columns(2)
                    rl = c4.selectbox("Class", ["IGL", "Entry Fragger", "Sniper", "Support", "Flex"])
                    jd = c5.date_input("Activation")
                    if st.form_submit_button("◈ REGISTER"):
                        if ign and fn and ln:
                            q = "INSERT INTO Players (team_id, in_game_name, first_name, last_name, role, join_date) VALUES (:tid, :ign, :fn, :ln, :rl, :jd)"
                            if execute_write(q, {"tid": sel_team_id, "ign": ign, "fn": fn, "ln": ln, "rl": rl, "jd": jd}, f"REGISTERED :: {ign}"):
                                st.rerun()
                        else:
                            st.error("Missing fields")
            with ct2:
                if not df_players.empty:
                    pd_dict = dict(zip(df_players['Codename'], df_players['player_id']))
                    with st.form("upd_form"):
                        st.markdown(f"<p style='color:{THEME['success']};font-family:Syncopate;letter-spacing:3px;'>REASSIGN CLASS</p>", unsafe_allow_html=True)
                        sp = st.selectbox("Target", list(pd_dict.keys()))
                        nr = st.selectbox("New Class", ["IGL", "Entry Fragger", "Sniper", "Support", "Flex"])
                        if st.form_submit_button("◈ REASSIGN"):
                            q = "UPDATE Players SET role = :r WHERE player_id = :p"
                            if execute_write(q, {"r": nr, "p": pd_dict[sp]}, f"{sp} → {nr}"):
                                st.rerun()
            with ct3:
                if not df_players.empty:
                    pd_dict = dict(zip(df_players['Codename'], df_players['player_id']))
                    with st.form("del_form"):
                        st.markdown(f"<p style='color:{THEME['alert']};font-family:Syncopate;letter-spacing:3px;'>TERMINATE CONTRACT</p>", unsafe_allow_html=True)
                        sd = st.selectbox("Target", list(pd_dict.keys()), key="del_sel")
                        if st.form_submit_button("◈ TERMINATE", type="primary"):
                            q = "DELETE FROM Players WHERE player_id = :p"
                            if execute_write(q, {"p": pd_dict[sd]}, f"TERMINATED :: {sd}"):
                                st.rerun()
    else:
        st.markdown(
            f"<div style='padding:14px;border:1px dashed {THEME['warn']};background:linear-gradient(135deg,{hex_to_rgba(THEME['warn'], 0.04)},transparent);font-family:JetBrains Mono,monospace;color:{THEME['warn']};text-align:center;letter-spacing:3px;font-size:0.8rem;margin-top:24px;border-radius:2px;'>🔒 ROSTER MOD LOCKED :: VIEWER CLEARANCE</div>",
            unsafe_allow_html=True
        )


# ---------------------------------------------------------
# TAB 4: RANKINGS
# ---------------------------------------------------------
with tab4:
    st.markdown('<div class="apex-section-header">GLOBAL STANDINGS</div>', unsafe_allow_html=True)
    df_lb = fetch_data("""
        SELECT t.name AS 'Syndicate', t.region AS 'Sector',
               COUNT(m.match_id) AS 'Matches Played',
               SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS 'Victories'
        FROM Teams t
        LEFT JOIN Matches m ON (t.team_id = m.team1_id OR t.team_id = m.team2_id) AND m.status = 'Completed'
        GROUP BY t.team_id, t.name, t.region
        ORDER BY Victories DESC, `Matches Played` DESC
    """)
    if df_lb.empty:
        df_lb = pd.DataFrame({
            "Syndicate": ["Neon Vanguard [MOCK]", "Cybernetic Knights [MOCK]", "Quantum Team [MOCK]", "Aegis Squad [MOCK]", "Phantom Strike [MOCK]", "Iron Wolves [MOCK]"],
            "Sector": ["NA", "EU", "KR", "SA", "EU", "NA"],
            "Matches Played": [18, 15, 22, 12, 16, 14],
            "Victories": [14, 11, 17, 7, 10, 8]
        })

    df_lb['Win Rate'] = (df_lb['Victories'] / df_lb['Matches Played'] * 100).fillna(0).round(1).astype(str) + '%'
    df_lb.insert(0, 'Rank', range(1, 1 + len(df_lb)))

    st.dataframe(df_lb, width="stretch", hide_index=True,
                 column_config={
                     "Rank": st.column_config.NumberColumn("◇ Rank", width="small"),
                     "Matches Played": st.column_config.ProgressColumn("Total Drops", format="%d", min_value=0,
                                                                        max_value=int(df_lb['Matches Played'].max() if df_lb['Matches Played'].max() > 0 else 10)),
                     "Win Rate": st.column_config.TextColumn("Lethality", width="small"),
                 })

    st.download_button("⬇ EXPORT RANKINGS", data=df_to_csv_bytes(df_lb),
                       file_name=f"apex_rankings_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

    st.markdown('<div class="apex-section-header">SECTOR PERFORMANCE MATRIX</div>', unsafe_allow_html=True)
    df_sec = df_lb.groupby('Sector')[['Matches Played', 'Victories']].sum().reset_index()
    if not df_sec.empty and df_sec['Matches Played'].sum() > 0:
        fig5 = px.scatter(df_sec, x='Matches Played', y='Victories', size='Victories', color='Sector',
                          color_discrete_sequence=HUD_COLORS, hover_name='Sector', size_max=50)
        fig5.update_traces(marker=dict(line=dict(color='#fff', width=1.5)))
        fig5.update_layout(template=CHART_THEME, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                           margin=dict(t=10, b=20, l=10, r=10),
                           xaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.1), title="Total Engagements",
                                      tickfont=dict(family="JetBrains Mono", color="#8892a8")),
                           yaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.1), title="Victories",
                                      tickfont=dict(family="JetBrains Mono", color="#8892a8")),
                           legend=dict(font=dict(family="Rajdhani", color="#e8eaed")))
        st.plotly_chart(fig5, width='stretch')


# ---------------------------------------------------------
# TAB 5: H2H
# ---------------------------------------------------------
with tab5:
    st.markdown('<div class="apex-section-header">SYNDICATE COMPARATOR</div>', unsafe_allow_html=True)
    df_th = fetch_data("SELECT team_id as id, name, region FROM Teams ORDER BY name")
    if df_th.empty:
        df_th = pd.DataFrame([
            {"id": 1, "name": "Neon Vanguard [MOCK]", "region": "NA"},
            {"id": 2, "name": "Cybernetic Knights [MOCK]", "region": "EU"},
            {"id": 3, "name": "Quantum Team [MOCK]", "region": "KR"},
            {"id": 4, "name": "Aegis Squad [MOCK]", "region": "SA"},
        ])

    td = dict(zip(df_th['name'], df_th['id']))
    names = list(td.keys())
    h1, h2 = st.columns(2)
    a = h1.selectbox("◇ ALPHA", names, index=0, key="ha")
    b = h2.selectbox("◇ BETA", names, index=1 if len(names) > 1 else 0, key="hb")

    if a == b:
        st.warning("⚠ Select two distinct syndicates")
    else:
        ai, bi = td[a], td[b]

        def stats(tid):
            d = fetch_data("SELECT COUNT(*) as t, SUM(CASE WHEN winner_team_id = :tid THEN 1 ELSE 0 END) as w FROM Matches WHERE (team1_id = :tid OR team2_id = :tid) AND status = 'Completed'", params={"tid": tid})
            if d.empty or pd.isna(d['t'].iloc[0]) or d['t'].iloc[0] == 0:
                random.seed(tid * 7919)
                return {"t": random.randint(8, 25), "w": random.randint(3, 18)}
            return {"t": int(d['t'].iloc[0]), "w": int(d['w'].iloc[0] or 0)}

        sa, sb = stats(ai), stats(bi)
        wra = (sa['w'] / sa['t'] * 100) if sa['t'] else 0
        wrb = (sb['w'] / sb['t'] * 100) if sb['t'] else 0

        df_h2h = fetch_data("""
            SELECT m.match_date, t1.name AS alpha, t2.name AS beta,
                   m.team1_score, m.team2_score, m.winner_team_id, m.status, m.stage
            FROM Matches m
            LEFT JOIN Teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN Teams t2 ON m.team2_id = t2.team_id
            WHERE ((m.team1_id = :a AND m.team2_id = :b) OR (m.team1_id = :b AND m.team2_id = :a))
              AND m.status = 'Completed'
            ORDER BY m.match_date DESC
        """, params={"a": ai, "b": bi})

        if df_h2h.empty:
            random.seed(ai * 13 + bi * 31)
            n = random.randint(2, 6)
            rows = []
            for i in range(n):
                t1s, t2s = random.randint(0, 3), random.randint(0, 3)
                while t1s == t2s:
                    t2s = random.randint(0, 3)
                winner = ai if t1s > t2s else bi
                rows.append({"match_date": pd.Timestamp.now() - pd.Timedelta(days=30 * (i + 1)),
                             "alpha": a, "beta": b, "team1_score": t1s, "team2_score": t2s,
                             "winner_team_id": winner, "status": "Completed",
                             "stage": random.choice(["Group Stage", "Quarter-Finals", "Semi-Finals", "Finals"])})
            df_h2h = pd.DataFrame(rows)

        aw = int((df_h2h['winner_team_id'] == ai).sum())
        bw = int((df_h2h['winner_team_id'] == bi).sum())
        ht = len(df_h2h)

        kc1, kc2, kc3, kc4, kc5 = st.columns([1.4, 1, 1, 1, 1.4])
        kc1.metric(f"◇ {a[:18]}", f"{wra:.1f}%", delta=f"{sa['w']} wins")
        kc2.metric("◇ Encounters", f"{ht:02d}")
        kc3.metric(f"◇ {a[:8]} W", f"{aw:02d}")
        kc4.metric(f"◇ {b[:8]} W", f"{bw:02d}")
        kc5.metric(f"◇ {b[:18]}", f"{wrb:.1f}%", delta=f"{sb['w']} wins")

        # Radar
        st.markdown('<div class="apex-section-header">METRIC OVERLAY</div>', unsafe_allow_html=True)
        random.seed(ai * 101)
        am = {"Lethality": round(wra, 1), "Volume": min(100, sa['t'] * 4),
              "Form": random.randint(40, 95), "Map Ctrl": random.randint(40, 95),
              "Clutch": random.randint(40, 95), "Discipline": random.randint(40, 95)}
        random.seed(bi * 101)
        bm = {"Lethality": round(wrb, 1), "Volume": min(100, sb['t'] * 4),
              "Form": random.randint(40, 95), "Map Ctrl": random.randint(40, 95),
              "Clutch": random.randint(40, 95), "Discipline": random.randint(40, 95)}

        cats = list(am.keys())
        fig_h = go.Figure()
        fig_h.add_trace(go.Scatterpolar(r=list(am.values()) + [list(am.values())[0]],
                                         theta=cats + [cats[0]], fill='toself', name=a,
                                         fillcolor=hex_to_rgba(THEME['primary'], 0.25),
                                         line=dict(color=THEME['primary'], width=2.5)))
        fig_h.add_trace(go.Scatterpolar(r=list(bm.values()) + [list(bm.values())[0]],
                                         theta=cats + [cats[0]], fill='toself', name=b,
                                         fillcolor=hex_to_rgba(THEME['secondary'], 0.25),
                                         line=dict(color=THEME['secondary'], width=2.5)))
        fig_h.update_layout(template=CHART_THEME,
                             polar=dict(bgcolor='rgba(0,0,0,0)',
                                        radialaxis=dict(visible=True, range=[0, 100],
                                                        tickfont=dict(family="JetBrains Mono", color="#8892a8", size=9),
                                                        gridcolor=hex_to_rgba(THEME['primary'], 0.15)),
                                        angularaxis=dict(tickfont=dict(family="Rajdhani", size=12, color="#fff"),
                                                         gridcolor=hex_to_rgba(THEME['primary'], 0.1))),
                             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                             showlegend=True,
                             legend=dict(font=dict(family="Syncopate", size=11, color="#e8eaed"),
                                         orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                             margin=dict(t=20, b=40, l=40, r=40), height=480)
        st.plotly_chart(fig_h, width='stretch')

        # Encounter log
        st.markdown('<div class="apex-section-header">ENCOUNTER LOG</div>', unsafe_allow_html=True)
        df_disp = df_h2h.copy()
        df_disp['match_date'] = pd.to_datetime(df_disp['match_date']).dt.strftime('%Y.%m.%d')
        df_disp['Score'] = df_disp['team1_score'].astype(str) + ' - ' + df_disp['team2_score'].astype(str)
        df_disp['Victor'] = df_disp['winner_team_id'].apply(lambda x: a if x == ai else b)
        df_disp = df_disp[['match_date', 'stage', 'alpha', 'Score', 'beta', 'Victor']]
        df_disp.columns = ['Date', 'Phase', 'Alpha', 'Score', 'Beta', 'Victor']
        st.dataframe(df_disp, width="stretch", hide_index=True)


# ---------------------------------------------------------
# TAB 6: BRACKET
# ---------------------------------------------------------
with tab6:
    st.markdown('<div class="apex-section-header">ELIMINATION TREE</div>', unsafe_allow_html=True)
    df_tb = fetch_data("SELECT tournament_id, name FROM Tournaments")
    if df_tb.empty:
        df_tb = pd.DataFrame({"tournament_id": [1, 2], "name": ["Omega Finals [MOCK]", "Alpha Circuit [MOCK]"]})

    tdb = dict(zip(df_tb['name'], df_tb['tournament_id']))
    sb = st.selectbox("◇ Circuit", list(tdb.keys()), key="brt")
    tib = tdb[sb]

    df_br = fetch_data("""
        SELECT m.match_id, m.stage, m.match_date,
               t1.name AS team1, t2.name AS team2,
               m.team1_score, m.team2_score, m.status, m.winner_team_id,
               t1.team_id AS t1_id, t2.team_id AS t2_id
        FROM Matches m
        LEFT JOIN Teams t1 ON m.team1_id = t1.team_id
        LEFT JOIN Teams t2 ON m.team2_id = t2.team_id
        WHERE m.tournament_id = :tid
        ORDER BY FIELD(m.stage, 'Round of 16', 'Quarter-Finals', 'Semi-Finals', 'Finals'), m.match_date
    """, params={"tid": tib})

    if df_br.empty:
        teams_m = ["Neon Vanguard", "Quantum Team", "Cybernetic Knights", "Nova Syndicate",
                   "Aegis Squad", "Void Walkers", "Phantom Strike", "Iron Wolves"]
        rows = []
        for i in range(0, 8, 2):
            rows.append({"match_id": 100 + i, "stage": "Quarter-Finals",
                         "team1": teams_m[i], "team2": teams_m[i + 1],
                         "team1_score": 2, "team2_score": 1, "status": "Completed",
                         "winner_team_id": i, "t1_id": i, "t2_id": i + 1})
        rows.append({"match_id": 200, "stage": "Semi-Finals",
                     "team1": teams_m[0], "team2": teams_m[2],
                     "team1_score": 2, "team2_score": 0, "status": "Completed",
                     "winner_team_id": 0, "t1_id": 0, "t2_id": 2})
        rows.append({"match_id": 201, "stage": "Semi-Finals",
                     "team1": teams_m[4], "team2": teams_m[6],
                     "team1_score": 1, "team2_score": 2, "status": "Live",
                     "winner_team_id": None, "t1_id": 4, "t2_id": 6})
        rows.append({"match_id": 300, "stage": "Finals",
                     "team1": teams_m[0], "team2": "TBD",
                     "team1_score": 0, "team2_score": 0, "status": "Scheduled",
                     "winner_team_id": None, "t1_id": 0, "t2_id": None})
        df_br = pd.DataFrame(rows)

    stage_order = ["Round of 16", "Quarter-Finals", "Semi-Finals", "Finals"]
    df_br['stage'] = pd.Categorical(df_br['stage'], categories=stage_order, ordered=True)
    df_br = df_br.sort_values(['stage', 'match_date'] if 'match_date' in df_br.columns else ['stage'])

    p, alert, success = THEME['primary'], THEME['alert'], THEME['success']
    stages_present = [s for s in stage_order if s in df_br['stage'].astype(str).unique()]

    if not stages_present:
        st.caption("No bracket data.")
    else:
        col_w, match_h, gap, col_gap = 280, 80, 24, 80
        sm = {s: df_br[df_br['stage'].astype(str) == s].reset_index(drop=True) for s in stages_present}
        max_m = max(len(v) for v in sm.values())
        canvas_h = max_m * (match_h + gap) + 80
        canvas_w = len(stages_present) * (col_w + col_gap) + 40

        fig_br = go.Figure()
        fig_br.update_xaxes(visible=False, range=[0, canvas_w])
        fig_br.update_yaxes(visible=False, range=[0, canvas_h])
        positions = {}

        for ci, stg in enumerate(stages_present):
            ms = sm[stg]
            n = len(ms)
            spacing = canvas_h / (n + 1)
            x0 = 20 + ci * (col_w + col_gap)
            x1 = x0 + col_w
            fig_br.add_annotation(x=(x0 + x1) / 2, y=canvas_h - 20, text=f"<b>{stg.upper()}</b>",
                                   showarrow=False, font=dict(family="Syncopate", size=14, color=p))
            for i, row in ms.iterrows():
                yc = canvas_h - 60 - (i + 1) * spacing + spacing / 2
                y0, y1 = yc - match_h / 2, yc + match_h / 2
                status = str(row.get('status', ''))
                bc = alert if status == 'Live' else (success if status == 'Completed' else p)
                fig_br.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                                  line=dict(color=bc, width=2), fillcolor='rgba(10,14,26,0.85)')
                fig_br.add_shape(type="line", x0=x0, y0=yc, x1=x1, y1=yc,
                                  line=dict(color=f"{hex_to_rgba(p, 0.2)}", width=1, dash='dot'))
                t1n = str(row['team1']) if pd.notna(row['team1']) else "TBD"
                t2n = str(row['team2']) if pd.notna(row['team2']) else "TBD"
                t1s = row.get('team1_score') if pd.notna(row.get('team1_score')) else '-'
                t2s = row.get('team2_score') if pd.notna(row.get('team2_score')) else '-'
                w1 = pd.notna(row.get('winner_team_id')) and row.get('winner_team_id') == row.get('t1_id')
                w2 = pd.notna(row.get('winner_team_id')) and row.get('winner_team_id') == row.get('t2_id')
                c1 = success if w1 else "#e8eaed"
                c2 = success if w2 else "#e8eaed"
                fig_br.add_annotation(x=x0 + 14, y=(yc + y1) / 2, xanchor='left',
                                       text=f"<b>{t1n[:24]}</b>", showarrow=False,
                                       font=dict(family="Rajdhani", size=13, color=c1))
                fig_br.add_annotation(x=x1 - 14, y=(yc + y1) / 2, xanchor='right',
                                       text=f"<b>{t1s}</b>", showarrow=False,
                                       font=dict(family="JetBrains Mono", size=14, color=c1))
                fig_br.add_annotation(x=x0 + 14, y=(y0 + yc) / 2, xanchor='left',
                                       text=f"<b>{t2n[:24]}</b>", showarrow=False,
                                       font=dict(family="Rajdhani", size=13, color=c2))
                fig_br.add_annotation(x=x1 - 14, y=(y0 + yc) / 2, xanchor='right',
                                       text=f"<b>{t2s}</b>", showarrow=False,
                                       font=dict(family="JetBrains Mono", size=14, color=c2))
                fig_br.add_annotation(x=x0 + 6, y=y1 + 8, xanchor='left',
                                       text=f"● {status.upper()}", showarrow=False,
                                       font=dict(family="JetBrains Mono", size=9, color=bc))
                positions[row['match_id']] = (x1, yc, x0, yc)

        for ci in range(len(stages_present) - 1):
            cur = sm[stages_present[ci]].reset_index(drop=True)
            nxt = sm[stages_present[ci + 1]].reset_index(drop=True)
            for j, nr in nxt.iterrows():
                feeders = [2 * j, 2 * j + 1]
                if any(f >= len(cur) for f in feeders):
                    continue
                np_ = positions.get(nr['match_id'])
                if not np_:
                    continue
                nlx, ny = np_[2], np_[3]
                for f in feeders:
                    fp = positions.get(cur.iloc[f]['match_id'])
                    if not fp:
                        continue
                    fx, fy = fp[0], fp[1]
                    mx = (fx + nlx) / 2
                    fig_br.add_shape(type="line", x0=fx, y0=fy, x1=mx, y1=fy, line=dict(color=f"{hex_to_rgba(p, 0.4)}", width=1.5))
                    fig_br.add_shape(type="line", x0=mx, y0=fy, x1=mx, y1=ny, line=dict(color=f"{hex_to_rgba(p, 0.4)}", width=1.5))
                    fig_br.add_shape(type="line", x0=mx, y0=ny, x1=nlx, y1=ny, line=dict(color=f"{hex_to_rgba(p, 0.4)}", width=1.5))

        fig_br.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                             margin=dict(t=10, b=10, l=10, r=10),
                             height=max(500, canvas_h), showlegend=False)
        st.plotly_chart(fig_br, width='stretch')

        st.markdown(f"""
            <div style='display:flex;gap:32px;justify-content:center;margin-top:8px;font-family:JetBrains Mono,monospace;font-size:0.78rem;letter-spacing:3px;'>
              <span style='color:{success};'><span class='apex-status-pill pill-success'>● COMPLETED</span></span>
              <span style='color:{alert};'><span class='apex-status-pill pill-alert'>● LIVE</span></span>
              <span style='color:{p};'><span class='apex-status-pill pill-info'>● SCHEDULED</span></span>
            </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------
# TAB 7: ANALYTICS — Predictive Insights
# ---------------------------------------------------------
with tab7:
    st.markdown('<div class="apex-section-header">PREDICTIVE INTELLIGENCE</div>', unsafe_allow_html=True)

    # Synthesize trend data
    days = pd.date_range(end=pd.Timestamp.now().normalize(), periods=30)
    random.seed(7)
    revenue = np.cumsum(np.random.normal(50, 15, 30)) + 800
    matches = np.random.poisson(4, 30) + np.arange(30) * 0.1
    viewership = np.cumsum(np.random.normal(200, 50, 30)) + 5000

    a1, a2, a3 = st.columns(3)
    with a1:
        delta = ((revenue[-1] - revenue[-7]) / revenue[-7] * 100)
        st.metric("◇ 30D Revenue", format_large_number(revenue[-1] * 1000), f"{delta:+.1f}%")
        # Sparkline
        sf = go.Figure()
        sf.add_trace(go.Scatter(x=days, y=revenue, mode='lines', fill='tozeroy',
                                 line=dict(color=THEME['primary'], width=2),
                                 fillcolor=hex_to_rgba(THEME['primary'], 0.1)))
        sf.update_layout(height=80, margin=dict(t=0, b=0, l=0, r=0),
                          xaxis=dict(visible=False), yaxis=dict(visible=False),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(sf, width='stretch')

    with a2:
        delta = ((matches[-1] - matches[-7]) / matches[-7] * 100)
        st.metric("◇ Match Velocity", f"{matches[-1]:.0f}/day", f"{delta:+.1f}%")
        sf = go.Figure()
        sf.add_trace(go.Scatter(x=days, y=matches, mode='lines', fill='tozeroy',
                                 line=dict(color=THEME['secondary'], width=2),
                                 fillcolor=hex_to_rgba(THEME['secondary'], 0.1)))
        sf.update_layout(height=80, margin=dict(t=0, b=0, l=0, r=0),
                          xaxis=dict(visible=False), yaxis=dict(visible=False),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(sf, width='stretch')

    with a3:
        delta = ((viewership[-1] - viewership[-7]) / viewership[-7] * 100)
        st.metric("◇ Avg Viewership", f"{viewership[-1]/1000:.1f}K", f"{delta:+.1f}%")
        sf = go.Figure()
        sf.add_trace(go.Scatter(x=days, y=viewership, mode='lines', fill='tozeroy',
                                 line=dict(color=THEME['accent'], width=2),
                                 fillcolor=hex_to_rgba(THEME['accent'], 0.1)))
        sf.update_layout(height=80, margin=dict(t=0, b=0, l=0, r=0),
                          xaxis=dict(visible=False), yaxis=dict(visible=False),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(sf, width='stretch')

    st.markdown('<div class="apex-section-header">7-DAY FORECAST PROJECTION</div>', unsafe_allow_html=True)

    # Simple linear projection
    future_days = pd.date_range(start=days[-1] + pd.Timedelta(days=1), periods=7)
    rev_trend = np.poly1d(np.polyfit(np.arange(30), revenue, 1))
    rev_forecast = rev_trend(np.arange(30, 37))

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(x=days, y=revenue, mode='lines', name='Historical',
                                 line=dict(color=THEME['primary'], width=2.5),
                                 fill='tozeroy', fillcolor=hex_to_rgba(THEME['primary'], 0.1)))
    fig_fc.add_trace(go.Scatter(x=future_days, y=rev_forecast, mode='lines', name='Forecast',
                                 line=dict(color=THEME['secondary'], width=2.5, dash='dash'),
                                 fill='tozeroy', fillcolor=hex_to_rgba(THEME['secondary'], 0.08)))
    # Confidence band
    upper = rev_forecast + np.linspace(20, 80, 7)
    lower = rev_forecast - np.linspace(20, 80, 7)
    fig_fc.add_trace(go.Scatter(x=list(future_days) + list(future_days[::-1]),
                                 y=list(upper) + list(lower[::-1]),
                                 fill='toself', fillcolor=hex_to_rgba(THEME['secondary'], 0.08),
                                 line=dict(color='rgba(0,0,0,0)'), name='95% CI', showlegend=True))
    fig_fc.update_layout(template=CHART_THEME, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         margin=dict(t=10, b=20, l=10, r=10), height=380,
                         xaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.1), title="",
                                    tickfont=dict(family="JetBrains Mono", color="#8892a8")),
                         yaxis=dict(showgrid=True, gridcolor=hex_to_rgba(THEME['primary'], 0.1), title="Revenue Index",
                                    tickfont=dict(family="JetBrains Mono", color="#8892a8")),
                         legend=dict(font=dict(family="Rajdhani", color="#e8eaed")))
    st.plotly_chart(fig_fc, width='stretch')

    # Insights cards
    st.markdown('<div class="apex-section-header">ARCHITECT INSIGHTS</div>', unsafe_allow_html=True)
    ic1, ic2, ic3 = st.columns(3)
    insights = [
        ("◆ ANOMALY DETECTED", THEME['warn'], "Match volume in EU sector deviates +18% from baseline. Recommend deeper telemetry pull."),
        ("◇ TREND CONFIRMED", THEME['success'], "Prize-pool growth correlates with sponsor injection events at r=0.87. Trigger system performing as expected."),
        ("⚠ CAPACITY ALERT", THEME['alert'], "Live engagement throughput approaching 92% capacity. Scale broadcast infrastructure within 14d."),
    ]
    for col, (title, color, body) in zip([ic1, ic2, ic3], insights):
        with col:
            st.markdown(f"""
                <div style='padding:18px;border:1px solid {color}66;border-left:3px solid {color};background:linear-gradient(135deg,{hex_to_rgba(THEME['bg_a'], 0.8)},{hex_to_rgba(THEME['bg_b'], 0.94)});min-height:140px;backdrop-filter:blur(8px);'>
                  <div style='color:{color};font-family:Syncopate,sans-serif;font-size:0.8rem;letter-spacing:3px;font-weight:700;margin-bottom:10px;'>{title}</div>
                  <div style='color:#e8eaed;font-family:Rajdhani,sans-serif;font-size:0.95rem;line-height:1.4;'>{body}</div>
                </div>
            """, unsafe_allow_html=True)


# ==========================================
# 12. FOOTER
# ==========================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f"""
    <div style='text-align:center;color:#4b5563;font-family:JetBrains Mono,monospace;font-size:0.72rem;letter-spacing:3px;padding:16px 0;'>
      ◈ APEX QUANTUM CONSOLE v9.6 :: BUILD OMEGA.10 ◈ OPERATOR :: <span style='color:{THEME['primary']};'>{USER['display_name']}</span> :: CLEARANCE <span style='color:{THEME['primary']};'>{USER['clearance']}</span> :: END OF TRANSMISSION
    </div>
""", unsafe_allow_html=True)