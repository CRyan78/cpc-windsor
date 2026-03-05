import streamlit as st
import pandas as pd
import re
import time
import urllib.parse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from streamlit_autorefresh import st_autorefresh 

# --- 1. CONFIG & REFRESH ---
st_autorefresh(interval=60000, key="datarefresh")
st.set_page_config(page_title="CPC Portal", layout="centered", page_icon="🚛")

# --- 2. GLOBAL STYLES ---
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px !important; }
    .header-box {background-color: #004a99 !important; color: white !important; padding: 25px; border-radius: 12px; margin-bottom: 15px;}
    .safety-box {background-color: #fff4f4 !important; border: 3px solid #cc0000 !important; padding: 20px; border-radius: 12px; margin-bottom: 15px; color: #1a1a1a !important;}
    .safety-box h2 { color: #cc0000 !important; margin-top: 0; font-size: 22px; }
    .btn-confirm {display: block !important; width: 100% !important; padding: 20px 0px !important; border-radius: 12px !important; text-align: center !important; font-weight: bold !important; font-size: 20px !important; text-decoration: none !important; color: white !important; margin-bottom: 15px !important; background-color: #107c10 !important; border: 2px solid #ffffff !important; text-decoration: none !important;}
    .btn-done {display: block !important; width: 100% !important; padding: 20px 0px !important; border-radius: 12px !important; text-align: center !important; font-weight: bold !important; font-size: 20px !important; text-decoration: none !important; color: white !important; margin-bottom: 15px !important; background-color: #007bff !important; border: 2px solid #ffffff !important; text-decoration: none !important;}
    .stop-detail-card {background-color: #f0f2f6 !important; color: #1a1a1a !important; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 6px solid #004a99 !important;}
    .eld-card {background-color: #2c3e50 !important; color: #ffffff !important; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 1px solid #34495e;}
    .eld-val {color: #3498db !important; font-size: 26px; font-weight: bold; font-family: monospace;}
    .btn-blue, .btn-green, .btn-red {display: block !important; width: 100% !important; padding: 15px 0px !important; border-radius: 10px !important; text-align: center !important; font-weight: bold !important; font-size: 18px !important; text-decoration: none !important; color: white !important; margin-bottom: 10px !important; border: none !important; text-decoration: none !important;}
    .btn-blue {background-color: #007bff !important;}
    .btn-green {background-color: #28a745 !important;}
    .btn-red {background-color: #dc3545 !important;}
    input { font-size: 24px !important; height: 60px !important; color: #000000 !important; background-color: #ffffff !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPERS ---
def clean_num(val):
    if pd.isna(val) or str(val).strip() in ('0', '', 'nan', 'None'): return ""
    return re.sub(r'\D', '', str(val).split('.')[0])

def clean_id_alphanumeric(val):
    if pd.isna(val) or str(val).strip() in ('0', '', 'nan', 'None'): return ""
    return str(val).strip()

def make_tel_link(phone_str):
    digits = re.sub(r'\D', '', str(phone_str))
    return f"tel:{digits}"

def get_col_val(row, possible_names, fallback_index=None):
    for col in possible_names:
        if col in row.index and not pd.isna(row[col]):
            return str(row[col]).strip()
    if fallback_index is not None and len(row) > fallback_index and not pd.isna(row.iloc[fallback_index]):
        return str(row.iloc[fallback_index]).strip()
    return "N/A"

def safe_get(row, col_name, index, default=""):
    if col_name in row and not pd.isna(row[col_name]): return str(row[col_name]).strip()
    if len(row) > index and not pd.isna(row.iloc[index]): return str(row.iloc[index]).strip()
    return default

# Date Math Logic
def format_date_metric(date_str, mode="down"):
    if date_str == "N/A" or not date_str or str(date_str).lower() in ['nan', 'none']:
        return "N/A", ""
    try:
        d = pd.to_datetime(date_str)
        now = pd.Timestamp.now()
        date_display = d.strftime('%m/%d/%y')
        
        if mode == "down": # Countdown for expirations
            days = (d - now).days
            if days < 0:
                return date_display, f"<span style='color:#ffb3b3; font-weight:bold;'>Expired</span>"
            elif days <= 30:
                return date_display, f"<span style='color:#ffe680; font-weight:bold;'>{days} days left</span>"
            else:
                return date_display, f"<span style='color:#b3ffcc;'>{days} days left</span>"
                
        else: # Countup for tenure
            rd = relativedelta(now, d)
            yrs = f"{rd.years}y " if rd.years > 0 else ""
            mos = f"{rd.months}m"
            return date_display, f"<span style='color:#b3ffcc;'>{yrs}{mos}</span>"
    except Exception:
        return str(date_str), ""

@st.cache_data(ttl=0)
def load_all_data():
    base_url = "https://docs.google.com/spreadsheets/d/1o77YRNaemFMZP-5e34_VVmdlGHtO2lGhT2kN_bh6W8I/export?format=csv"
    gids = {
        "roster": "956807855", "schedule": "2135671483", "email": "316342570",
        "quick": "644504571", "dispatch": "1528012287",
        "working_sched": "1659857002", "working_disp": "1195417546", "safety": "464410004"
    }
    def get_s(gid):
        try:
            df = pd.read_csv(f"{base_url}&gid={gid}&cb={int(time.time())}", low_memory=False)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    return (
        get_s(gids["roster"]), get_s(gids["dispatch"]), get_s(gids["schedule"]), 
        get_s(gids["quick"]), get_s(gids["safety"]), get_s(gids["working_sched"]), 
        get_s(gids["working_disp"])
    )

# --- 4. MAIN APP ---
try:
    roster, dispatch, schedule, quick_links, safety, next_schedule, next_dispatch = load_all_data()
    st.markdown("<h1 style='font-size: 28px;'>🚛 CPC Portal</h1>", unsafe_allow_html=True)
    user_input = st.text_input("Enter ID", value="").strip().lower()

    if user_input == "dispatch":
        st.subheader("📋 Dispatch Dashboard")
        responses_url = "https://docs.google.com/spreadsheets/d/1yGwaBQaciW6F0MTlHSTgx1ozp00nULTNApctZYtBOAU/edit?usp=sharing"
        st.markdown(f'<a href="{responses_url}" target="_blank" class="btn-confirm" style="background-color: #004a99 !important;">📊 VIEW LIVE ROUTE CONFIRMATIONS</a>', unsafe_allow_html=True)

    elif user_input:
        if '#' in roster.columns: id_col = '#'
        elif len(roster.columns) >= 15: id_col = roster.columns[14]
        else:
            st.error("Could not locate column '#' or Column O in Roster tab.")
            st.stop()

        roster['match_id'] = roster[id_col].apply(clean_num)
        match = roster[roster['match_id'] == user_input]

        if not match.empty:
            driver = match.iloc[0]
            
            d_name = get_col_val(driver, ['Driver Name', 'Driver', 'Name', 'Employee Name'], 0)
            raw_route = get_col_val(driver, ['Route', 'Route #', 'Current Route'], 1) 
            p_id = clean_id_alphanumeric(get_col_val(driver, ['PeopleNet ID', 'PeopleNet', 'ELD'], 12))
            
            # EXACT COLUMN MATCHING
            raw_dl = get_col_val(driver, ['DL Expiration Date'])
            raw_dot = get_col_val(driver, ['DOT Expiration Date', 'DOT physical expires'])
            raw_hire = get_col_val(driver, ['Hire Date'])
            raw_smart_drive = get_col_val(driver, ['SMART Drive score', 'SMART Drive', 'SmartDrive', 'Score'])
            
            # PROCESSING THE DATE MATH
            dl_date, dl_badge = format_date_metric(raw_dl, "down")
            dot_date, dot_badge = format_date_metric(raw_dot, "down")
            hire_date, hire_badge = format_date_metric(raw_hire, "up")
            
            # Clean up missing SD metric
            smart_drive = raw_smart_drive if str(raw_smart_drive).lower() != 'nan' else 'N/A'

            route_num = clean_num(raw_route)
            today_str = datetime.now().strftime("%m/%d/%Y")
            tom_str = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")

            st.markdown("### Daily Portal")
            tab_today, tab_tom = st.tabs([f"📅 Today ({today_str})", f"⏭️ Tomorrow ({tom_str})"])

            def get_safety_msg(target_date):
                msg = "Perform a thorough pre-trip inspection."
                if not safety.empty:
                    s_match = safety[safety.iloc[:, 0].astype(str).str.contains(target_date, na=False)]
                    if not s_match.empty: msg = s_match.iloc[0, 1]
                return msg

            with tab_today:
                st.markdown(f"<div class='safety-box'><h2>⚠️ SAFETY REMINDER</h2><p>{get_safety_msg(today_str)}</p></div>", unsafe_allow_html=True)
                is_confirmed = st.toggle("I have submitted the Confirmation Form", key=f"conf_{user_input}")
                form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfnw_F7nGy4GbJlMlCxSSGXx86b8g5J6VhXRkz_ZvABr2fcMg/viewform?"
                params = {"entry.534103007": d_name, "entry.726947479": user_input, "entry.316322786": raw_route}
                full_url = form_url + urllib.parse.urlencode(params)
                btn_class = "btn-done" if is_confirmed else "btn-confirm"
                btn_text = "✅ ROUTE CONFIRMED" if is_confirmed else "🚛 READ SAFETY & CONFIRM ROUTE"
                st.markdown(f'<a href="{full_url}" target="_blank" class="{btn_class}">{btn_text}</a>', unsafe_allow_html=True)

                st.markdown(f"""
                <div class='header-box'>
                    <h3>{d_name if d_name != 'N/A' else 'Driver'}</h3>
                    <p style="margin-top:-10px; margin-bottom:15px; opacity: 0.9;">
                        ID: <b>{user_input}</b> &nbsp;|&nbsp; Route: <b>{raw_route if raw_route != 'N/A' else 'Unassigned'}</b>
                    </p>
                    <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.3); margin-bottom: 15px;">
                    <div style="display:flex; justify-content:space-between; text-align:center; font-size:15px; line-height:1.4;">
                        <div style="flex:1;"><b>DL Exp</b><br>{dl_date}<br><small>{dl_badge}</small></div>
                        <div style="flex:1; border-left: 1px solid rgba(255,255,255,0.3);"><b>DOT Exp</b><br>{dot_date}<br><small>{dot_badge}</small></div>
                        <div style="flex:1; border-left: 1px solid rgba(255,255,255,0.3);"><b>Tenure</b><br>{hire_date}<br><small>{hire_badge}</small></div>
                        <div style="flex:1; border-left: 1px solid rgba(255,255,255,0.3);"><b>SmartDrive</b><br>{smart_drive}<br><small style="color:#b3ffcc;">Score</small></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""<div class='eld-card'><div style='font-size:14px; opacity:0.8;'>ELD LOGIN</div>
                            <span class='eld-val'>3299 | {p_id if p_id != 'N/A' else 'None'} | {p_id if p_id != 'N/A' else 'None'}</span></div>""", unsafe_allow_html=True)

                dispatch['route_match'] = dispatch.iloc[:, 0].apply(clean_num)
                today_notes = dispatch[dispatch['route_match'] == route_num]
                if not today_notes.empty:
                    st.markdown(f"<div style='border: 2px solid #d35400; padding: 15px; border-radius: 12px; background-color: #fffcf9; margin-bottom: 15px;'><b>Today's Notes:</b><br>{today_notes.iloc[0].get('Comments', 'None')}</div>", unsafe_allow_html=True)

                schedule['route_match'] = schedule.iloc[:, 0].apply(clean_num)
                stops = schedule[schedule['route_match'] == route_num]
                for _, stop in stops.iterrows():
                    sid = clean_num(safe_get(stop, 'Store ID', 4))
                    sid_5 = sid.zfill(5)
                    addr = safe_get(stop, 'Store Address', 5)
                    arr = safe_get(stop, 'Arrival time', 8)
                    with st.expander(f"📍 Store {sid_5} — {arr}", expanded=True):
                        st.markdown(f"<div class='stop-detail-card'>{addr}</div>", unsafe_allow_html=True)
                        t_url = f"tel:8008710204,1,,88012#,,{sid},#,,,1,,,1"
                        nav_url = f"http://maps.apple.com/?q={addr.replace(' ','+')}"
                        s_map = f"https://wg.cpcfact.com/store-{sid_5}/"
                        iss_url = f"https://forms.office.com/Pages/ResponsePage.aspx?id=DQSIkWdsW0yxEjajBLZtrQAAAAAAAAAAAAO__Ti7fnBUQzNYTTY1TjY3Uk0xMEwwTE9SUEZIWTRPRC4u&r6db86d06117646df9723ec7f53f3e1f3={sid_5}"
                        st.markdown(f"<a href='{t_url}' class='btn-green'>📞 Store Tracker</a>", unsafe_allow_html=True)
                        st.markdown(f"<a href='{nav_url}' class='btn-blue'>🌎 Navigation</a>", unsafe_allow_html=True)
                        st.markdown(f"<a href='{s_map}' class='btn-blue'>🗺️ Store Map</a>", unsafe_allow_html=True)
                        st.markdown(f"<a href='{iss_url}' class='btn-red'>🚨 Report Issue</a>", unsafe_allow_html=True)

            with tab_tom:
                st.markdown(f"<div class='safety-box' style='border-color: #004a99 !important; background-color: #f0f7ff !important;'><h2>⏭️ TOMORROW'S SAFETY</h2><p>{get_safety_msg(tom_str)}</p></div>", unsafe_allow_html=True)
                next_dispatch['route_match'] = next_dispatch.iloc[:, 0].apply(clean_num)
                tom_notes = next_dispatch[next_dispatch['route_match'] == route_num]
                if not tom_notes.empty:
                    st.markdown(f"<div style='border: 2px solid #004a99; padding: 15px; border-radius: 12px; background-color: #f0f7ff; margin-bottom: 15px;'><b>Tomorrow's Notes:</b><br>{tom_notes.iloc[0].get('Comments', 'None')}</div>", unsafe_allow_html=True)
                
                next_schedule['route_match'] = next_schedule.iloc[:, 0].apply(clean_num)
                t_stops = next_schedule[next_schedule['route_match'] == route_num]
                if t_stops.empty: st.info("Tomorrow's schedule not yet posted.")
                for _, stop in t_stops.iterrows():
                    sid_t = clean_num(safe_get(stop, 'Store ID', 4))
                    sid_t5 = sid_t.zfill(5)
                    addr_t = safe_get(stop, 'Store Address', 5)
                    arr_t = safe_get(stop, 'Arrival time', 8)
                    with st.expander(f"📍 Store {sid_t5} — {arr_t}"):
                        st.markdown(f"<div class='stop-detail-card'>{addr_t}</div>", unsafe_allow_html=True)
                        t_url_t = f"tel:8008710204,1,,88012#,,{sid_t},#,,,1,,,1"
                        nav_url_t = f"http://maps.apple.com/?q={addr_t.replace(' ','+')}"
                        s_map_t = f"https://wg.cpcfact.com/store-{sid_t5}/"
                        iss_url_t = f"https://forms.office.com/Pages/ResponsePage.aspx?id=DQSIkWdsW0yxEjajBLZtrQAAAAAAAAAAAAO__Ti7fnBUQzNYTTY1TjY3Uk0xMEwwTE9SUEZIWTRPRC4u&r6db86d06117646df9723ec7f53f3e1f3={sid_t5}"
                        st.markdown(f"<a href='{t_url_t}' class='btn-green'>📞 Store Tracker</a>", unsafe_allow_html=True)
                        st.markdown(f"<a href='{nav_url_t}' class='btn-blue'>🌎 Navigation</a>", unsafe_allow_html=True)
                        st.markdown(f"<a href='{s_map_t}' class='btn-blue'>🗺️ Store Map</a>", unsafe_allow_html=True)
                        st.markdown(f"<a href='{iss_url_t}' class='btn-red'>🚨 Report Issue</a>", unsafe_allow_html=True)

            st.divider()
            if not quick_links.empty:
                for _, link in quick_links.iterrows():
                    if len(link) >= 2:
                        n = str(link.iloc[0]).strip()
                        v = str(link.iloc[1]).strip()
                        if n and n != 'nan' and v and v != 'nan':
                            if "http" in v.lower(): st.markdown(f"<a href='{v}' class='btn-blue'>{n}</a>", unsafe_allow_html=True)
                            else: st.markdown(f"<a href='{make_tel_link(v)}' class='btn-green'>📞 Call {n}</a>", unsafe_allow_html=True)
        else: st.error("ID not found.")
except Exception as e: st.error(f"Critical Error: {e}")
