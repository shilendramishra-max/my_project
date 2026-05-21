#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import datetime
import subprocess
import json
import streamlit as st
from dotenv import load_dotenv

# --- PRODUCTION-GRADE LAYOUT CONFIGURATION ---
st.set_page_config(
    page_title="Multi-Service Recon Control Dashboard",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLING INJECTION (Matches the dark aesthetic of original HTML) ---
st.markdown("""
    <style>
        /* Base Background and App Canvas Reset */
        .stApp {
            background-color: #0b0f17 !important;
            color: #e2e8f0 !important;
        }
        /* Sidebar container styling */
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid rgba(51, 65, 85, 0.6) !important;
        }
        /* Custom styling to emulate Tailwind badges and containers */
        .custom-card {
            background-color: #0f172a;
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            margin-bottom: 1rem;
        }
        /* Custom Scrollbars */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0b0f19; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
        
        /* Eliminate native gap allocations */
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- ENVIRONMENT & SECRETS MATRIX LOADING ---
load_dotenv()
SYSTEM_SECRET_PIN = os.getenv("ADMIN_SECURITY_PIN", None)
DASHBOARD_HISTORY_DAYS = int(os.getenv("DASHBOARD_HISTORY_DAYS", 15))
LOG_VIEW_CHARACTER_LIMIT = int(os.getenv("LOG_VIEW_CHARACTER_LIMIT", 1500))

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_SERVER_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../crons"))

# --- HARD DATA-FOOTPRINT SCANNER CORES ---
def get_all_services():
    if not os.path.exists(BASE_SERVER_DIR):
        return []
    return sorted([
        f for f in os.listdir(BASE_SERVER_DIR) 
        if os.path.isdir(os.path.join(BASE_SERVER_DIR, f)) and not f.startswith('.') and f != 'playground'
    ])

# --- STATE LIFECYCLE CONTROLLERS ---
if 'active_editor_buffer' not in st.session_state:
    st.session_state.active_editor_buffer = ""
if 'active_editor_filename' not in st.session_state:
    st.session_state.active_editor_filename = ""
if 'admin_mode_active' not in st.session_state:
    st.session_state.admin_mode_active = False

# --- STICKY STYLED DASHBOARD HEADER ---
st.markdown("""
    <div style="background-color: rgba(15, 23, 42, 0.8); backdrop-filter: blur(8px); border-bottom: 1px solid rgba(51, 65, 85, 0.6); padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.5rem;">🔄</span>
            <h1 style="font-size: 1.25rem; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; background: linear-gradient(to right, #60a5fa, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                Multiservice Recon Control Dashboard <span style="font-size: 0.75rem; color: #64748b; font-weight: 400; text-transform: none;">(Streamlit Production Engine)</span>
            </h1>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #64748b; background-color: rgba(15, 23, 42, 0.6); padding: 0.375rem 0.75rem; border-radius: 0.375rem; border: 1px solid #1e293b;">
            <span style="width: 0.5rem; height: 0.5rem; background-color: #10b981; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #10b981;"></span>
            <span>Engine Status: Operational</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- DATA STREAM PIPELINE POPULATION ---
services = get_all_services()
if not services:
    st.error("🚨 Configuration Error: No valid cron service directories detected inside Sibling folder target environment.")
    st.stop()

# --- SIDEBAR: NAVIGATION CONTROLLER LAYER ---
st.sidebar.markdown("""
    <div style="padding-bottom: 0.5rem;">
        <h2 style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; display: flex; align-items: center; gap: 0.5rem; margin: 0;">
            📁 Navigation Control
        </h2>
    </div>
""", unsafe_allow_html=True)

selected_service = st.sidebar.selectbox("Select Active Cron Service:", services, label_visibility="collapsed")

# Inject Active Dynamic Indicator Status Box
st.sidebar.markdown(f"""
    <div style="margin-top: 1rem; display: flex; align-items: center; justify-content: space-between; padding: 0.625rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 600; background-color: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2);">
        <span style="text-transform: uppercase; letter-spacing: 0.05em;">⚡ {selected_service} Active</span>
        <span style="width: 0.375rem; height: 0.375rem; background-color: #60a5fa; border-radius: 50%; box-shadow: 0 0 8px rgba(96,165,250,0.6);"></span>
    </div>
""", unsafe_allow_html=True)

# Date Parameter Synchronizer
st.sidebar.markdown("<br><p style='font-size: 0.75rem; color: #555; margin-bottom:2px;'>Jump to Historical Date Frame Mapping Matrix:</p>", unsafe_allow_html=True)
selected_date_raw = st.sidebar.date_input("Query Execution Date", datetime.datetime.now(), label_visibility="collapsed")
selected_date = selected_date_raw.strftime("%Y-%m-%d")
today_str = datetime.datetime.now().strftime("%Y-%m-%d")

# --- PATH DISCOVERY LAYER ---
current_dir = os.path.join(BASE_SERVER_DIR, selected_service)
stat_dir = os.path.join(current_dir, "stat")
stat_error_dir = os.path.join(stat_dir, "error")
out_dir = os.path.join(current_dir, "out")
error_dir = os.path.join(current_dir, "error")
usage_dir = os.path.join(current_dir, "usage")
missing_dir = os.path.join(current_dir, "missing")

# --- LIVE STATE DISCOVERY ENGINES ---
status = "⚪ NOT STARTED / PENDING"
error_details = ""
is_locked = False

today_lck_file = os.path.join(usage_dir, f"check_usage-{today_str}.lck")
if os.path.exists(today_lck_file):
    is_locked = True

target_success_file = os.path.join(stat_dir, f"stat-{selected_date}.txt")
target_error_file = os.path.join(stat_error_dir, f"stat-{selected_date}.txt")
target_shell_error = os.path.join(error_dir, f"error-{selected_date}.txt")

if is_locked and selected_date == today_str:
    status = "⏳ RUNNING / LOCKED (Process is currently executing)"
else:
    if os.path.exists(target_success_file) and os.path.getsize(target_success_file) > 0:
        with open(target_success_file, "r", encoding="utf-8") as f:
            if f.read().strip() == "1":
                status = "✅ COMPLETE / SUCCESS"
            else:
                status = "⚠️ INCOMPLETE / NO SUCCESS FLAG"
    elif os.path.exists(target_error_file) or (os.path.exists(target_shell_error) and os.path.getsize(target_shell_error) > 0):
        status = "🚨 SCRIPT ERROR / FAILED (Check Logs)"
        if os.path.exists(target_shell_error) and os.path.getsize(target_shell_error) > 0:
            with open(target_shell_error, "r", encoding="utf-8", errors="ignore") as f:
                error_details = f.read()
    else:
        status = "⚪ NOT STARTED / PENDING"

# --- SMART HISTORY TRACKER ENGINE LOGIC ---
recon_history = []
for i in range(DASHBOARD_HISTORY_DAYS):
    date_to_check = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
    
    check_lck_path = os.path.join(usage_dir, f"check_usage-{date_to_check}.lck")
    check_success_path = os.path.join(stat_dir, f"stat-{date_to_check}.txt")
    check_error_path = os.path.join(stat_error_dir, f"stat-{date_to_check}.txt")
    check_shell_err_path = os.path.join(error_dir, f"error-{date_to_check}.txt")
    
    day_status = "⏳ Pend"
    day_color = "gray"
    
    if os.path.exists(check_success_path) and os.path.getsize(check_success_path) > 0:
        try:
            with open(check_success_path, "r", encoding="utf-8") as f:
                if f.read().strip() == "1":
                    day_status = "✓ Done"
                    day_color = "green"
                else:
                    day_status = "⚠ No Flag"
                    day_color = "yellow"
        except:
            day_status = "⚠ Flag Error"
            day_color = "yellow"
    elif os.path.exists(check_lck_path):
        day_status = "⏳ Running"
        day_color = "yellow"
    elif os.path.exists(check_error_path) or (os.path.exists(check_shell_err_path) and os.path.getsize(check_shell_err_path) > 0):
        day_status = "✕ Failed"
        day_color = "red"
    elif os.path.exists(check_success_path) and os.path.getsize(check_success_path) == 0:
        day_status = "⏳ Incomplete"
        day_color = "yellow"
        
    recon_history.append({"date": date_to_check, "status": day_status, "color": day_color})

# --- FILE FOOTPRINT PARSING ENGINE ---
files = []
if os.path.exists(current_dir):
    files = sorted([f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f)) and (f.endswith('.py') or f.endswith('.sh'))])

# Out Log Processing Trace Frame
out_details = ""
target_out_file = os.path.join(out_dir, f"out-{selected_date}.txt")
if os.path.exists(target_out_file) and os.path.getsize(target_out_file) > 0:
    with open(target_out_file, "r", encoding="utf-8", errors="ignore") as f:
        out_details = f.read()[-LOG_VIEW_CHARACTER_LIMIT:]
else:
    out_details = f"No output logs found for date: {selected_date}"

# Fetch Dynamic Directory Footprints for Admin File Interface Block
operational_files = {"stat": [], "stat/error": [], "error": [], "missing": []}
target_folders = {"stat": stat_dir, "stat/error": stat_error_dir, "error": error_dir, "missing": missing_dir}

for prefix, path in target_folders.items():
    if os.path.exists(path):
        for f in sorted(os.listdir(path)):
            if os.path.isfile(os.path.join(path, f)) and not f.startswith('.'):
                operational_files[prefix].append(f"{prefix}/{f}")


# --- MAIN INTERFACE BRANDING LAYOUT ---
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <span style="font-size: 1.75rem;">📊</span>
        <h2 style="font-size: 1.5rem; font-weight: 900; color: #f8fafc; letter-spacing: -0.025em; margin: 0;">
            Service Panel: <span style="font-family: monospace; color: #60a5fa;">{selected_service}</span>
        </h2>
    </div>
""", unsafe_allow_html=True)

# Top Data KPIs Panel Layout Rows
col_kpi1, col_kpi2 = st.columns([1, 2])

with col_kpi1:
    # Current Execution Status Layout Block
    status_class_style = "color: #f87171; background-color: rgba(159, 18, 57, 0.4); border-color: rgba(153, 27, 27, 0.8);"
    if "COMPLETE" in status:
        status_class_style = "color: #34d399; background-color: rgba(6, 78, 59, 0.4); border-color: rgba(6, 95, 70, 0.8);"
    elif "LOCKED" in status or "RUNNING" in status:
        status_class_style = "color: #fbbf24; background-color: rgba(120, 53, 4, 0.4); border-color: rgba(146, 64, 14, 0.8);"
        
    st.markdown(f"""
        <div class="custom-card" style="height: 110px; display: flex; flex-col; justify-content: space-between;">
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 8px;">
                <span style="width: 0.5rem; height: 0.5rem; background-color: #3b82f6; border-radius: 50%;"></span> Current Status
            </div>
            <div style="padding: 0.5rem; border-radius: 0.75rem; text-align: center; font-weight: 700; font-size: 0.75rem; border: 1px solid; {status_class_style}">
                <div style="text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.6; margin-bottom: 2px;">System State ({selected_date})</div>
                <div style="font-size: 0.85rem; font-weight: 900;">{status}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    # Dynamic 15 Days History Grid Layout Panel
    st.markdown("""
        <div class="custom-card" style="min-height: 110px; padding-bottom: 0.75rem;">
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 10px;">
                📅 Past 15 Days Recon History Tracker (Click on Sidebar Date to Navigate)
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Render historical items as clean metric micro columns row
    grid_cols = st.columns(5)
    for index, day in enumerate(recon_history[:15]):
        target_col = grid_cols[index % 5]
        
        # Mapping background indicator metrics colors safely
        border_col = "rgba(51, 65, 85, 0.8)"
        bg_col = "rgba(15, 23, 42, 0.4)"
        text_badge_color = "#94a3b8"
        
        if day["color"] == "green":
            border_col = "rgba(6, 95, 70, 0.6)"; bg_col = "rgba(6, 78, 59, 0.2)"; text_badge_color = "#34d399"
        elif day["color"] == "red":
            border_col = "rgba(153, 27, 27, 0.6)"; bg_col = "rgba(159, 18, 57, 0.2)"; text_badge_color = "#f87171"
        elif day["color"] == "yellow":
            border_col = "rgba(146, 64, 14, 0.6)"; bg_col = "rgba(120, 53, 4, 0.2)"; text_badge_color = "#fbbf24"
            
        is_current_pin = "border: 2px solid #3b82f6; box-shadow: 0 0 12px rgba(59,130,246,0.3); background-color: #1e293b;" if day["date"] == selected_date else f"border: 1px solid {border_col}; background-color: {bg_col};"
        pin_emoji = "📌" if day["date"] == selected_date else ""
        
        target_col.markdown(f"""
            <div style="border-radius: 0.75rem; padding: 0.5rem; text-align: center; height: 62px; display: flex; flex-direction: column; justify-content: space-between; {is_current_pin}">
                <div style="font-size: 9px; font-weight: 700; color: {'#60a5fa' if day['date'] == selected_date else '#64748b'}; tracking-tighter;">
                    {day['date']} {pin_emoji}
                </div>
                <div style="font-size: 11px; font-weight: 900; text-transform: uppercase; color: {text_badge_color};">
                    {day['status']}
                </div>
            </div>
        """, unsafe_allow_html=True)


# --- CONSOLIDATED EXECUTION AND WORKSPACE PANELS ---
col_workspace1, col_workspace2 = st.columns(2)

with col_workspace1:
    st.markdown(f"""
        <div style="background-color: #0f172a; border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 0.75rem; padding: 1.25rem; height: 600px; display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <h3 style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin: 0;">
                    📋 Standard Output Logs (<span style="color: #60a5fa; font-family: monospace;">out-{selected_date}.txt</span>)
                </h3>
                <span style="width: 0.5rem; height: 0.5rem; background-color: #60a5fa; border-radius: 50%; box-shadow: 0 0 8px #60a5fa;"></span>
            </div>
            <div style="font-size: 11px; color: #64748b; font-family: monospace; margin-bottom: 8px;">Recent stream processing trace execution blocks:</div>
            <div style="flex-grow: 1; background-color: #05070c; border: 1px solid #0b0f19; border-radius: 0.75rem; padding: 1rem; overflow-y: auto; font-family: monospace; font-size: 12px; color: #34d399; white-space: pre-wrap;">{'<span style="color: #475569; font-style: italic;">' + out_details + '</span>' if "No output logs found" in out_details else out_details}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Append trace block panel explicitly if runtime errors manifest inside state arrays
    if error_details:
        st.markdown(f"""
            <div style="margin-top: 1rem; padding: 0.75rem; background-color: rgba(159, 18, 57, 0.1); border: 1px solid rgba(153, 27, 27, 0.4); border-radius: 0.75rem; font-family: monospace; font-size: 12px; color: #f87171;">
                <div style="font-weight: 700; text-transform: uppercase; font-size: 10px; color: #ef4444; margin-bottom: 4px;">🚨 System Traceback Error Detected:</div>
                {error_details}
            </div>
        """, unsafe_allow_html=True)

with col_workspace2:
    st.markdown("""
        <div style="background-color: #0f172a; border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 0.75rem; padding: 1.25rem; display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <h3 style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin: 0;">
                    🎛️ Safe Playground Sandbox & Directory Manager
                </h3>
                <span style="width: 0.5rem; height: 0.5rem; background-color: #c084fc; border-radius: 50%; box-shadow: 0 0 8px #c084fc;"></span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # SECTION 1: AD-HOC DIRECTORY MANAGER COMPONENT
    st.markdown("<div style='font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #fbbf24; margin-bottom: 6px;'>⚙️ Ad-hoc Folder & File Directory Manager</div>", unsafe_allow_html=True)
    
    col_adm1, col_adm2, col_adm3 = st.columns([1, 1.5, 1])
    
    with col_adm1:
        admin_folder = st.selectbox("Select Target Admin Folder Scope:", ["-- Folder --", "stat", "stat/error", "error", "missing"], label_visibility="collapsed")
    
    with col_adm2:
        available_admin_files = ["-- Select File --"]
        if admin_folder != "-- Folder --":
            available_admin_files.extend([f.split('/')[-1] for f in operational_files.get(admin_folder, [])])
        
        selected_admin_filename = st.selectbox("Choose Admin Operational File:", available_admin_files, disabled=(admin_folder == "-- Folder --"), label_visibility="collapsed")
        
    with col_adm3:
        col_btn1, col_btn2 = st.columns(2)
        target_relative_action_path = f"{admin_folder}/{selected_admin_filename}" if (admin_folder != "-- Folder --" and selected_admin_filename != "-- Select File --") else None
        
        with col_btn1:
            if st.button("🧹 Clear", disabled=not target_relative_action_path, use_container_width=True, help="Truncate content data matrix down to 0B state instantly."):
                full_truncate_target = os.path.join(BASE_SERVER_DIR, selected_service, target_relative_action_path)
                try:
                    with open(full_truncate_target, "w", encoding="utf-8") as f:
                        f.write("")
                    st.toast(f"🧹 Content inside '{target_relative_action_path}' truncated down to 0B.", icon="🧹")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with col_btn2:
            if st.button("🗑️ Del", disabled=not target_relative_action_path, use_container_width=True, help="Completely delete the targeted data entity block from server filesystem."):
                full_delete_target = os.path.join(BASE_SERVER_DIR, selected_service, target_relative_action_path)
                try:
                    os.remove(full_delete_target)
                    st.toast(f"🗑️ File '{target_relative_action_path}' completely removed from filesystem storage database matrix.", icon="🗑️")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # Dynamic Load Controller to bind Admin data content straight onto main Workspace Area Editor
    if target_relative_action_path and st.button(f"📥 Load Admin Asset Content Buffer: {selected_admin_filename}", use_container_width=True):
        full_admin_read_target = os.path.join(BASE_SERVER_DIR, selected_service, target_relative_action_path)
        if os.path.exists(full_admin_read_target):
            with open(full_admin_read_target, "r", encoding="utf-8", errors="ignore") as f:
                st.session_state.active_editor_buffer = f.read()
                st.session_state.active_editor_filename = target_relative_action_path
                st.session_state.admin_mode_active = True
                st.rerun()

    st.markdown("<hr style='border: 1px solid #1e293b; margin: 10px 0;'>", unsafe_allow_html=True)

    # SECTION 2: LIVE CRON SCRIPT WORKSPACE PICKER
    cron_template_options = ["-- Select Template File to Load --"] + files
    selected_cron_file = st.selectbox("Workspace Template Script Selection Selector:", cron_template_options, label_visibility="collapsed")
    
    if selected_cron_file != "-- Select Template File to Load --" and st.button("📥 Load Selected Script into Workspace Staging Frame", use_container_width=True):
        full_cron_read_target = os.path.join(BASE_SERVER_DIR, selected_service, selected_cron_file)
        if os.path.exists(full_cron_read_target):
            with open(full_cron_read_target, "r", encoding="utf-8", errors="ignore") as f:
                st.session_state.active_editor_buffer = f.read()
                st.session_state.active_editor_filename = selected_cron_file
                st.session_state.admin_mode_active = False
                st.rerun()

    # SECTION 3: SYSTEM INTERACTIVE INTERFACE TEXT BUFFER ZONE (Replaces Ace Editor Engine canvas)
    if st.session_state.active_editor_filename:
        banner_color = "rgba(245, 158, 11, 0.15)" if st.session_state.admin_mode_active else "rgba(59, 130, 246, 0.15)"
        text_accent = "#fbbf24" if st.session_state.admin_mode_active else "#60a5fa"
        mode_label = "⚙️ Admin Text Mode Active:" if st.session_state.admin_mode_active else "ℹ️ Workspace Isolation Memory Frame Filled:"
        
        st.markdown(f"""
            <div style="background-color: {banner_color}; border: 1px solid {text_accent}40; padding: 0.5rem; border-radius: 0.5rem; font-size: 11px; color: {text_accent}; font-weight: 500; margin-bottom: 8px;">
                {mode_label} Opened file configuration structural target matrix context path: <span style="font-family: monospace; font-weight: 700;">{st.session_state.active_editor_filename}</span>
            </div>
        """, unsafe_allow_html=True)
        
    edited_workspace_code = st.text_area("Workspace Sandbox Code Processing Terminal Canvas:", value=st.session_state.active_editor_buffer, height=260, label_visibility="collapsed")

    # SECTION 4: LOAD INTO TEMPLATE INTEGRATION ENGINE (API equivalence mapping context)
    if st.button("📥 Load Code into Sandbox Template (No Risk Mode)", use_container_width=True):
        if not st.session_state.active_editor_filename:
            st.error("Operation Denied: No transaction element loaded inside execution context framework.")
        elif st.session_state.admin_mode_active:
            st.error("Action denied: System protection mechanisms prevent writing sandbox pipeline logs straight into administrative operational matrix frameworks.")
        else:
            service_playground_dir = os.path.join(BASE_SERVER_DIR, selected_service, "playground")
            os.makedirs(service_playground_dir, exist_ok=True)
            
            target_playground_extension_name = "playground.py" if st.session_state.active_editor_filename.lower().endswith('.py') else "playground.sh"
            full_sandbox_write_target = os.path.join(service_playground_dir, target_playground_extension_name)
            
            try:
                with open(full_sandbox_write_target, "w", encoding="utf-8", newline='\n') as f:
                    f.write(edited_workspace_code)
                if target_playground_extension_name == "playground.sh" and os.name != 'nt':
                    os.chmod(full_sandbox_write_target, 0o755)
                    
                st.success(f"🎉 Content successfully written to isolated database: {selected_service}/playground/{target_playground_extension_name}")
            except Exception as e:
                st.error(f"Filesystem Exception Allocation Intercepted: {str(e)}")

# --- PLAYGROUND ISOLATED SECURITY AUTHORIZATION PIPELINE GATE ---
# Auto display conditional logic matches HTML `filename.endsWith('.sh')` triggering configuration block 
if st.session_state.active_editor_filename.lower().endswith('.sh') and not st.session_state.admin_mode_active:
    st.markdown("""
        <div style="margin-top: 1.5rem; background-color: #111827; border: 1px solid rgba(51, 65, 85, 0.8); border-radius: 0.75rem; padding: 1.25rem; box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);">
            <h4 style="font-size: 0.875rem; font-weight: 700; color: #fbbf24; display: flex; align-items: center; gap: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 1rem 0;">
                ⚠️ Playground Execution Security Access Authorization Gate
            </h4>
        </div>
    """, unsafe_allow_html=True)
    
    sec_col1, sec_col2, sec_col3 = st.columns([1.5, 1, 1])
    
    with sec_col1:
        confirm_execution_checkbox = st.checkbox("I confirm to execute this temporary playground staging template pipeline.", value=False)
    with sec_col2:
        input_security_pin = st.text_input("Enter Security PIN Matrix Insertion:", type="password", placeholder="Enter Security PIN", label_visibility="collapsed")
    with sec_col3:
        if st.button("🚀 Approve & Run Template Pipeline", use_container_width=True):
            if is_locked:
                st.error("This staging template is currently locked and cannot be executed because another production instance is already running.")
            elif not confirm_execution_checkbox:
                st.error("Staging Exception: Please toggle the authentication confirmation statement gate switch first!")
            elif not input_security_pin:
                st.error("Authorization Violation: PIN block entry security metrics inputs can't be null!")
            elif SYSTEM_SECRET_PIN is None or SYSTEM_SECRET_PIN == "":
                st.error("❌ Server Security Misconfiguration: .env file configuration records or system access authentication secrets are missing on host engine matrix!")
            elif input_security_pin != SYSTEM_SECRET_PIN:
                st.error("❌ Invalid Security PIN: Transaction signature verification verification failed.")
            else:
                service_playground_dir = os.path.join(BASE_SERVER_DIR, selected_service, "playground")
                target_sandbox_sh_script_path = os.path.join(service_playground_dir, "playground.sh")
                
                if not os.path.exists(target_sandbox_sh_script_path):
                    st.error(f"❌ Execution Core Misalignment: playground.sh file trace entity could not be verified inside directory mapping: {selected_service}/playground/")
                else:
                    try:
                        if os.name == 'nt':
                            subprocess.Popen(["cmd", "/c", "echo Running playground template on Windows"], cwd=service_playground_dir)
                        else:
                            subprocess.Popen(["bash", "playground.sh"], cwd=service_playground_dir)
                        st.success(f"🚀 Playground shell script pipeline context triggered successfully inside `{selected_service}/playground/` folder execution track matrices!")
                    except Exception as e:
                        st.error(f"Shell System Exception Traceback: {str(e)}")

# --- SYSTEM FOOTER SIGNATURE NOTE MATRICES ---
st.markdown("""
    <footer style="margin-top: 3rem; border-top: 1px solid rgba(15, 23, 20, 0.8); background-color: #0a0d14; padding: 1rem 0; text-align: center; font-family: monospace; font-size: 11px; color: #475569; letter-spacing: 0.05em;">
        <div>&copy; 2026 Centralized Recon Engine stack. All Rights Reserved.</div>
        <div style="margin-top: 0.25rem; color: #64748b;">
            Engineered with ❤️ by <span style="color: rgba(96, 165, 250, 0.8); font-weight: 700; cursor: text;">Shilendra Kumar Mishra</span>
        </div>
    </footer>
""", unsafe_allow_html=True)