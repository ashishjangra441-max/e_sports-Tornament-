import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import urllib.parse
from datetime import datetime
import os

# ==========================================
# 1. PAGE CONFIGURATION & BROADCAST STYLING
# ==========================================
st.set_page_config(
    page_title="APEX | Broadcast HUD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom formatting function for large numbers (Millions, Thousands)
def format_large_number(num):
    if pd.isna(num) or num is None:
        return "$0"
    if num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num / 1_000:.0f}K"
    return f"${num:.0f}"

# Ultra-Crisp Tactical HUD Theme with Scanlines, Crosshairs, and Styled Dropdowns
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Share+Tech+Mono&family=Inter:wght@400;500;700&display=swap');

    /* Global Crosshair Cursor & CRT Scanline Background */
    html, body, [data-testid="stAppViewContainer"] {
        cursor: crosshair !important;
        background-color: #050508;
        background-image: 
            linear-gradient(rgba(0, 229, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 229, 255, 0.03) 1px, transparent 1px),
            repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.3) 3px, rgba(0, 0, 0, 0.3) 3px);
        background-size: 30px 30px, 30px 30px, 100% 4px;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Interactive Elements Hover Cursor */
    a, button, div[role="button"], .stSelectbox {
        cursor: pointer !important;
    }

    /* Aggressive Broadcast Headers */
    h1, h2, h3, h4, h5 {
        font-family: 'Orbitron', sans-serif !important;
        color: #ffffff !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.5rem;
    }
    
    /* Live Pulsing Animation */
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 42, 109, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 42, 109, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 42, 109, 0); }
    }

    /* Tactical Metric Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(15, 20, 25, 0.85) 0%, rgba(5, 8, 12, 0.95) 100%);
        border: 1px solid rgba(0, 229, 255, 0.15);
        border-left: 4px solid #00e5ff;
        border-radius: 2px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #00e5ff;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
    }
    div[data-testid="metric-container"]::after {
        content: '';
        position: absolute;
        bottom: 0;
        right: 0;
        width: 30px;
        height: 2px;
        background-color: #00e5ff;
    }
    
    div[data-testid="metric-container"] label {
        color: #8b949e !important;
        font-size: 0.8rem !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* Digital Number Readouts */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 400;
        font-size: 3rem !important;
        font-family: 'Share Tech Mono', monospace;
        text-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
    }

    /* Sci-Fi Selectbox (Dropdowns) */
    div[data-baseweb="select"] > div {
        background-color: rgba(5, 5, 8, 0.9) !important;
        border: 1px solid rgba(0, 229, 255, 0.5) !important;
        border-radius: 0px;
        color: #00e5ff !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 1.1rem;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #ff2a6d !important;
        box-shadow: 0 0 10px rgba(255, 42, 109, 0.3);
    }
    div[data-baseweb="popover"] ul {
        background-color: rgba(10, 12, 16, 0.95) !important;
        border: 1px solid #00e5ff !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    /* Broadcast Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(10, 15, 20, 0.8);
        padding: 5px 10px 0 10px;
        border-bottom: 2px solid rgba(0, 229, 255, 0.2);
        border-radius: 4px 4px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #6e7681;
        background-color: transparent;
        font-family: 'Orbitron', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 1px;
        border: none;
        padding: 12px 20px;
    }
    .stTabs [aria-selected="true"] {
        color: #00e5ff !important;
        background: linear-gradient(0deg, rgba(0,229,255,0.1) 0%, transparent 100%);
        border-bottom: 2px solid #00e5ff !important;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    
    /* Stealth DataFrames */
    [data-testid="stDataFrame"] {
        background: rgba(10, 12, 16, 0.8);
        border: 1px solid rgba(0, 229, 255, 0.1);
        border-radius: 0;
    }
    [data-testid="stDataFrame"] th {
        background-color: #0d1117 !important;
        color: #00e5ff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(0, 229, 255, 0.3) !important;
    }
    
    /* Progress Bars for Diagnostics */
    .stProgress > div > div > div {
        background-color: #00e5ff;
    }

    /* HUD Dividers */
    hr {
        border-top: 1px dashed rgba(0, 229, 255, 0.2);
        margin: 1.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Crisp HUD Brand Colors
CHART_THEME = "plotly_dark"
HUD_COLORS = ["#00e5ff", "#ff2a6d", "#bc13fe", "#00ff9d", "#ffb30f"]

# ==========================================
# 2. DATABASE CONNECTION (PRODUCTION READY)
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
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        # Silently fail for frontend mockup purposes if DB isn't running
        return None

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(query, params=None):
    engine = init_connection()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except SQLAlchemyError as e:
        st.warning(f"DATABANK ANOMALY.\n{e}")
        return pd.DataFrame()

# ==========================================
# 3. SIDEBAR: PRODUCTION CONTROLS & DIAGNOSTICS
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00e5ff; font-size: 2.8rem; margin-bottom: 0; letter-spacing: 4px; text-shadow: 0 0 15px rgba(0,229,255,0.4);'>APEX</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ffffff; font-family: Inter; font-weight: 700; letter-spacing: 3px; font-size: 0.8rem;'>BROADCAST DIRECTOR</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    db_status = init_connection()
    if db_status:
        st.markdown("<div style='padding: 10px; border: 1px solid #00ff9d; background: rgba(0,255,157,0.05); border-radius: 4px; text-align: center; margin-bottom: 15px;'><span style='color:#00ff9d; font-family: Orbitron; font-weight: 700; letter-spacing: 1px;'>DATALINK: SECURE</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='padding: 10px; border: 1px solid #ff2a6d; background: rgba(255,42,109,0.05); border-radius: 4px; text-align: center; margin-bottom: 15px;'><span style='color:#ff2a6d; font-family: Orbitron; font-weight: 700; letter-spacing: 1px;'>DATALINK: FAILED / MOCK DATA</span></div>", unsafe_allow_html=True)
        
    st.markdown("<p style='color: #8b949e; font-size: 0.75rem; margin-bottom: 2px; font-family: Inter; font-weight: 700; letter-spacing: 1px;'>MISSION CLOCK (UTC)</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #ffffff; font-family: Share Tech Mono; font-size: 1.5rem; margin-top: 0;'>{datetime.now().strftime('%Y.%m.%d // %H:%M:%S')}</p>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1); margin: 15px 0;'>", unsafe_allow_html=True)
    
    # Simulated Diagnostics
    st.markdown("<p style='color: #8b949e; font-size: 0.75rem; font-family: Inter; font-weight: 700; letter-spacing: 1px;'>SYSTEM DIAGNOSTICS</p>", unsafe_allow_html=True)
    st.progress(87, text="CORE LOAD (87%)")
    st.progress(42, text="MEMORY ALLOC (42%)")
    st.progress(98, text="NETWORK UPTIME (98%)")

    st.markdown("<hr style='border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; font-size: 0.75rem; font-family: Inter; font-weight: 700; letter-spacing: 1px;'>SYSTEM ALERTS</p>", unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # NEW: ANIMATED TRIGGER NOTIFICATIONS (HTML/JS INJECTED)
    # ---------------------------------------------------------
    trigger_html = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        body { margin: 0; padding: 0; background-color: transparent; font-family: 'Share Tech Mono', monospace; }
        #trigger-notifications { display: flex; flex-direction: column; overflow: hidden; height: 130px; }
        .alert-box {
            padding: 8px;
            font-size: 11px;
            border-left: 2px solid #00e5ff;
            background: rgba(0, 229, 255, 0.1);
            color: #00e5ff;
            margin-bottom: 8px;
            animation: fadeIn 0.3s ease;
        }
        .alert-box.warning {
            border-left-color: #ff2a6d;
            background: rgba(255, 42, 109, 0.1);
            color: #ff2a6d;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    <div id="trigger-notifications"></div>
    <script>
        const triggers = [
            { msg: "WARNING: Sector NA Latency > 150ms", type: "alert" },
            { msg: "INFO: Protocol CS:Nexus update complete", type: "info" },
            { msg: "ALERT: Unauthorized access attempt blocked", type: "alert" },
            { msg: "INFO: Core load stabilized at 87%", type: "info" },
            { msg: "WARNING: Match M-002 stream degradation", type: "alert" },
            { msg: "INFO: Syndicate LOUD roster updated", type: "info" }
        ];
        
        const container = document.getElementById('trigger-notifications');
        let i = 0;
        
        container.innerHTML = `<div class="alert-box">> INFO: Notification daemon started</div>`;
        
        setInterval(() => {
            if(container.children.length >= 3) {
                container.removeChild(container.lastChild);
            }
            const notif = document.createElement('div');
            const t = triggers[i];
            const isAlert = t.type === 'alert';
            
            notif.className = 'alert-box' + (isAlert ? ' warning' : '');
            notif.innerText = `> ${t.msg}`;
            
            container.prepend(notif);
            i = (i + 1) % triggers.length;
        }, 4000);
    </script>
    """
    # Render the HTML/JS ticker in the Streamlit Sidebar
    components.html(trigger_html, height=140)

    st.markdown("<br><p style='color: rgba(255,255,255,0.2); font-size: 0.7em; text-align: center; font-family: Share Tech Mono;'>SYS.VER: APEX_OS_9.4 // BUILD: OMEGA</p>", unsafe_allow_html=True)


# ==========================================
# 4. DASHBOARD ARCHITECTURE (TABS)
# ==========================================
st.markdown("<div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px;'><h1 style='font-size: 2rem; margin: 0;'>LIVE TELEMETRY FEED</h1><span style='color: #ff2a6d; font-family: Orbitron; font-weight: 800; font-size: 1.2rem; text-shadow: 0 0 10px rgba(255,42,109,0.5);'>• REC</span></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📡 OVERVIEW", "⚔️ TELEMETRY", "🛡️ ARCHIVES", "🏆 GLOBAL RANKINGS"])

# ---------------------------------------------------------
# TAB 1: Overview Feed
# ---------------------------------------------------------
with tab1:
    kpi_query = """
        SELECT 
            (SELECT COUNT(*) FROM Tournaments WHERE status IN ('Upcoming', 'Ongoing')) as active_tournaments,
            (SELECT COUNT(*) FROM Teams) as total_teams,
            (SELECT SUM(total_prize_pool) FROM Tournaments) as global_prize,
            (SELECT COUNT(*) FROM Matches WHERE status = 'Live') as live_matches
    """
    df_kpi = fetch_data(kpi_query)
    
    if not df_kpi.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Active Circuits", f"{df_kpi['active_tournaments'].iloc[0]:02d}")
        col2.metric("Syndicates", f"{df_kpi['total_teams'].iloc[0]:02d}")
        
        # Using custom formatting for Millions/Thousands
        prize_raw = df_kpi['global_prize'].iloc[0]
        col3.metric("Total Funding", format_large_number(prize_raw))
        
        # Highlight Live Matches if > 0
        live_count = df_kpi['live_matches'].iloc[0]
        if live_count > 0:
            st.markdown(f"""
                <style>
                div[data-testid="metric-container"]:nth-child(4) {{
                    border-left: 4px solid #ff2a6d !important;
                    animation: pulse-red 2s infinite;
                }}
                div[data-testid="metric-container"]:nth-child(4) div[data-testid="stMetricValue"] {{
                    color: #ff2a6d !important;
                    text-shadow: 0 0 15px rgba(255, 42, 109, 0.4) !important;
                }}
                </style>
            """, unsafe_allow_html=True)
        col4.metric("Live Engagements", f"{live_count:02d}")
    else:
        st.info("Awaiting telemetry data... (Or DB Connection Failed)")

    st.markdown("<hr>", unsafe_allow_html=True)
    
    col_v1, col_v2 = st.columns([1.2, 1.8])
    
    # Visual 1: Razor-Thin Donut Chart
    with col_v1:
        st.markdown("<h4 style='color: #8b949e !important; font-size: 0.9rem;'>>> INFRASTRUCTURE DEPLOYMENT</h4>", unsafe_allow_html=True)
        df_locations = fetch_data("SELECT location_type AS location, COUNT(*) as count FROM Tournaments GROUP BY location_type")
        
        if not df_locations.empty:
            fig1 = px.pie(
                df_locations, 
                names='location', 
                values='count', 
                hole=0.85, # Ultra thin
                color_discrete_sequence=HUD_COLORS
            )
            fig1.update_traces(hoverinfo='label+percent', textinfo='none')
            fig1.update_layout(
                template=CHART_THEME,
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=10, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(family="Inter", size=12, color="#e2e8f0"))
            )
            fig1.add_annotation(text=f"<span style='font-family: Share Tech Mono; font-size: 36px; color:#ffffff;'>{df_locations['count'].sum():02d}</span><br><span style='font-family: Orbitron; font-size: 10px; color:#00e5ff; letter-spacing: 2px;'>ZONES</span>", x=0.5, y=0.5, showarrow=False)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.caption("No infrastructure data detected.")

    # Visual 2: Equalizer-style Bar Chart
    with col_v2:
        st.markdown("<h4 style='color: #8b949e !important; font-size: 0.9rem;'>>> PRIZE DISTRIBUTION BY PROTOCOL</h4>", unsafe_allow_html=True)
        df_games = fetch_data("""
            SELECT game_title, SUM(total_prize_pool) as total_prize 
            FROM Tournaments 
            GROUP BY game_title 
            ORDER BY total_prize ASC
        """)
        
        if not df_games.empty:
            fig2 = px.bar(
                df_games, 
                x='total_prize', 
                y='game_title', 
                orientation='h',
            )
            fig2.update_traces(
                marker_color='rgba(0, 229, 255, 0.6)',
                marker_line_color='#00e5ff',
                marker_line_width=1,
                width=0.3, # Thin equalizer bars
                hovertemplate="Protocol: %{y}<br>Funding: $%{x:,.0f}<extra></extra>"
            )
            fig2.update_layout(
                template=CHART_THEME,
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, l=10, r=10, b=10),
                xaxis=dict(showgrid=True, gridcolor='rgba(0, 229, 255, 0.1)', title="", tickfont=dict(family="Share Tech Mono", color="#8b949e")),
                yaxis=dict(title="", tickfont=dict(family="Orbitron", size=12, color="#ffffff"))
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No prize data detected.")

# ---------------------------------------------------------
# TAB 2: Match Telemetry
# ---------------------------------------------------------
with tab2:
    col_op1, col_op2 = st.columns([3, 1])
    
    with col_op1:
        st.markdown("<h4 style='color: #8b949e !important; font-size: 0.9rem;'>>> COMBAT LOGS & SCHEDULE</h4>", unsafe_allow_html=True)
    with col_op2:
        status_options = ['ALL', 'LIVE', 'SCHEDULED', 'COMPLETED']
        selected_status = st.selectbox("STATUS OVERRIDE", status_options, label_visibility="collapsed")

    match_query = """
        SELECT 
            m.match_id as ID,
            m.match_date AS 'Timestamp', 
            tr.name AS 'Circuit',
            t1.name AS 'Alpha', 
            t2.name AS 'Beta',
            m.stage AS 'Phase',
            CONCAT(m.team1_score, ' - ', m.team2_score) AS 'Score',
            UPPER(m.status) AS 'Status'
        FROM Matches m
        LEFT JOIN Tournaments tr ON m.tournament_id = tr.tournament_id
        LEFT JOIN Teams t1 ON m.team1_id = t1.team_id
        LEFT JOIN Teams t2 ON m.team2_id = t2.team_id
        ORDER BY m.match_date DESC
        LIMIT 100
    """
    df_matches = fetch_data(match_query)
    
    if not df_matches.empty:
        if selected_status != 'ALL':
            df_matches = df_matches[df_matches['Status'] == selected_status]
            
        # Add a visual indicator to LIVE matches
        df_matches['Status'] = df_matches['Status'].apply(lambda x: '🔴 LIVE' if x == 'LIVE' else x)
            
        st.dataframe(
            df_matches, 
            width="stretch", 
            hide_index=True,
            column_config={
                "ID": None,
                "Timestamp": st.column_config.DatetimeColumn("T-Minus (UTC)", format="YYYY.MM.DD HH:mm"),
                "Alpha": st.column_config.TextColumn("Alpha Syndicate", width="medium"),
                "Beta": st.column_config.TextColumn("Beta Syndicate", width="medium"),
                "Score": st.column_config.TextColumn("Score", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #8b949e !important; font-size: 0.9rem;'>>> ENGAGEMENT FORECAST</h4>", unsafe_allow_html=True)
        
        df_matches['Timestamp'] = pd.to_datetime(df_matches['Timestamp'])
        df_timeline = df_matches.groupby(df_matches['Timestamp'].dt.date).size().reset_index(name='Matches')
        
        fig3 = px.line(
            df_timeline, 
            x='Timestamp', 
            y='Matches',
        )
        fig3.update_traces(
            line=dict(width=2, color="#00e5ff", shape='vh'), # Step-line chart for tech feel
            mode='lines+markers',
            marker=dict(size=4, color="#ffffff", symbol='square')
        )
        # Subtle gradient fill
        fig3.add_trace(go.Scatter(
            x=df_timeline['Timestamp'], y=df_timeline['Matches'],
            fill='tozeroy', mode='none', fillcolor='rgba(0, 229, 255, 0.1)', showlegend=False
        ))

        fig3.update_layout(
            template=CHART_THEME,
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=20, l=0, r=0),
            xaxis=dict(showgrid=True, gridcolor='rgba(0, 229, 255, 0.05)', title="", tickfont=dict(family="Share Tech Mono", color="#8b949e")),
            yaxis=dict(showgrid=True, gridcolor='rgba(0, 229, 255, 0.1)', title="", tickfont=dict(family="Share Tech Mono", color="#8b949e"))
        )
        st.plotly_chart(fig3, use_container_width=True, height=200)
        
    else:
        st.caption("No combat logs currently available.")

# ---------------------------------------------------------
# TAB 3: Syndicate Archives (Team DB)
# ---------------------------------------------------------
with tab3:
    st.markdown("<h4 style='color: #8b949e !important; font-size: 0.9rem;'>>> TARGET SYNDICATE PROFILE</h4>", unsafe_allow_html=True)
    
    df_teams = fetch_data("SELECT team_id as id, name, region, contact_email FROM Teams ORDER BY name")
    
    if not df_teams.empty:
        team_dict = dict(zip(df_teams['name'], df_teams['id']))
        selected_team_name = st.selectbox("SEARCH DATABASE", options=list(team_dict.keys()), label_visibility="collapsed")
        selected_team_id = team_dict[selected_team_name]
        
        team_info = df_teams[df_teams['id'] == selected_team_id].iloc[0]
        
        perf_query = """
            SELECT 
                COUNT(*) as total_matches,
                SUM(CASE WHEN winner_team_id = :tid THEN 1 ELSE 0 END) as wins
            FROM Matches 
            WHERE (team1_id = :tid OR team2_id = :tid) AND status = 'Completed'
        """
        df_perf = fetch_data(perf_query, params={"tid": selected_team_id})
        
        total_matches = df_perf['total_matches'].iloc[0] if not df_perf.empty else 0
        total_wins = df_perf['wins'].iloc[0] if not df_perf.empty and pd.notnull(df_perf['wins'].iloc[0]) else 0
        win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("Sector", team_info['region'])
        col_kpi2.metric("Total Drops", f"{int(total_matches):03d}")
        col_kpi3.metric("Victories", f"{int(total_wins):03d}")
        col_kpi4.metric("Lethality", f"{win_rate:.1f}%")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        col_r1, col_r2 = st.columns([2.5, 1])
        
        with col_r1:
            st.markdown("<h5 style='color: #ffffff; font-family: Orbitron; margin-bottom: 15px;'>ACTIVE OPERATIVES</h5>", unsafe_allow_html=True)
            player_query = "SELECT in_game_name AS 'Codename', first_name AS 'Given', last_name AS 'Surname', role AS 'Class', join_date AS 'Activation' FROM Players WHERE team_id = :tid"
            df_players = fetch_data(player_query, params={"tid": selected_team_id})
            
            if not df_players.empty:
                st.dataframe(
                    df_players, 
                    width="stretch", 
                    hide_index=True,
                    column_config={
                        "Activation": st.column_config.DateColumn("Activation", format="YYYY.MM.DD")
                    }
                )
            else:
                st.caption("No operative data found for this syndicate.")
                
        with col_r2:
            st.markdown("<h5 style='color: #ffffff; font-family: Orbitron; margin-bottom: 15px; text-align: center;'>CLASS DISTRIBUTION</h5>", unsafe_allow_html=True)
            if not df_players.empty and 'Class' in df_players.columns:
                role_counts = df_players['Class'].value_counts().reset_index()
                role_counts.columns = ['Class', 'Count']
                
                # Radar-like Polar Bar Chart for tactical feel
                fig4 = px.bar_polar(
                    role_counts, 
                    r='Count', 
                    theta='Class',
                    color='Class',
                    color_discrete_sequence=HUD_COLORS,
                    template=CHART_THEME
                )
                fig4.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=False),
                        angularaxis=dict(tickfont=dict(family="Orbitron", size=10, color="#8b949e"))
                    ),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                 st.caption("Insufficient class data.")
            
    else:
        st.caption("Awaiting database synchronization.")

# ---------------------------------------------------------
# TAB 4: Global Rankings (NEW - Leaderboard)
# ---------------------------------------------------------
with tab4:
    st.markdown("<h4 style='color: #8b949e !important; font-size: 0.9rem;'>>> OFFICIAL APEX STANDINGS</h4>", unsafe_allow_html=True)
    
    # Query to calculate total wins and total matches played per team
    leaderboard_query = """
        SELECT 
            t.name AS 'Syndicate',
            t.region AS 'Sector',
            COUNT(m.match_id) AS 'Matches Played',
            SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS 'Victories'
        FROM Teams t
        LEFT JOIN Matches m ON (t.team_id = m.team1_id OR t.team_id = m.team2_id) AND m.status = 'Completed'
        GROUP BY t.team_id
        HAVING `Matches Played` > 0
        ORDER BY Victories DESC, `Matches Played` ASC
        LIMIT 15
    """
    df_leaderboard = fetch_data(leaderboard_query)
    
    if not df_leaderboard.empty:
        # Calculate Win Rate locally
        df_leaderboard['Win Rate'] = (df_leaderboard['Victories'] / df_leaderboard['Matches Played'] * 100).round(1).astype(str) + "%"
        
        # Adding Rank Column
        df_leaderboard.insert(0, 'Rank', range(1, 1 + len(df_leaderboard)))
        
        st.dataframe(
            df_leaderboard,
            width="stretch",
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("RANK", format="#%d"),
                "Syndicate": st.column_config.TextColumn("SYNDICATE", width="medium"),
                "Sector": st.column_config.TextColumn("SECTOR", width="small"),
                "Matches Played": st.column_config.NumberColumn("DROPS"),
                "Victories": st.column_config.NumberColumn("VICTORIES"),
                "Win Rate": st.column_config.TextColumn("LETHALITY")
            }
        )
    else:
        st.caption("Insufficient combat data to generate standings.")