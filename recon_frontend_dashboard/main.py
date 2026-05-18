import streamlit as st
import os
import datetime
import subprocess
from streamlit_ace import st_ace

st.set_page_config(page_title="Multi-Service Recon Dashboard", layout="wide")
st.title("Centralized Reconciliation Dashboard")

# --- BASE SERVER PATH ---
BASE_SERVER_DIR = "../crons" # Kyunki aapne folder local directory me hi banaya hai

# --- AUTOMATIC FOLDER DETECTION ---
all_services = [
    f for f in os.listdir(BASE_SERVER_DIR) 
    if os.path.isdir(os.path.join(BASE_SERVER_DIR, f)) and not f.startswith('.')
]
all_services.sort()

# --- UI: SERVICE SELECTION DROPDOWN ---
st.sidebar.header("Navigation")
selected_service = st.sidebar.selectbox("Select Service / Folder", all_services)

st.header(f"Monitoring: {selected_service}")

# --- DYNAMIC PATHS BASED ON SELECTION ---
CURRENT_SERVICE_DIR = os.path.join(BASE_SERVER_DIR, selected_service)

STAT_DIR = os.path.join(CURRENT_SERVICE_DIR, "stat")
STAT_ERROR_DIR = os.path.join(STAT_DIR, "error")
OUT_DIR = os.path.join(CURRENT_SERVICE_DIR, "out")
ERROR_DIR = os.path.join(CURRENT_SERVICE_DIR, "error")
USAGE_DIR = os.path.join(CURRENT_SERVICE_DIR, "usage") 

 
if os.path.exists(CURRENT_SERVICE_DIR):
    
    sh_files = [f for f in os.listdir(CURRENT_SERVICE_DIR) if f.endswith('.sh')]
else:
    sh_files = []

# 3. find sh file in the current service folder
if sh_files:
    SCRIPT_SH_NAME = sh_files[0]  # first .sh file 
else:
    SCRIPT_SH_NAME = "script.sh"  


SCRIPT_SH = os.path.join(CURRENT_SERVICE_DIR, SCRIPT_SH_NAME)
# Date configuration (Format: 2026-05-18)
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
daily_success_file = os.path.join(STAT_DIR, f"{today_str}.txt")

# --- LOCK DETECTION LOGIC ---
is_locked = False
if os.path.exists(USAGE_DIR):
    lck_files = [f for f in os.listdir(USAGE_DIR) if f.endswith('.lck')]
    if len(lck_files) > 0:
        is_locked = True

# --- LOGIC: STATUS CHECKING ---
status = "NOT STARTED / PENDING"
status_color = "info"
error_details = ""

if is_locked:
    status = "RUNNING / LOCKED (Process is currently executing)"
    status_color = "warning"

elif os.path.exists(daily_success_file):
    status = "COMPLETE / SUCCESS"
    status_color = "success"

elif os.path.exists(STAT_ERROR_DIR) and len(os.listdir(STAT_ERROR_DIR)) > 0:
    status = f" SCRIPT ERROR (Check stat/error)"
    status_color = "error"
    files = [os.path.join(STAT_ERROR_DIR, f) for f in os.listdir(STAT_ERROR_DIR)]
    if files:
        latest_file = max(files, key=os.path.getctime)
        with open(latest_file, "r") as f:
            error_details = f.read()

elif os.path.exists(ERROR_DIR) and len(os.listdir(ERROR_DIR)) > 0:
    status = " ISSUE DETECTED (Logs in error/ folder)"
    status_color = "warning"
    files = [os.path.join(ERROR_DIR, f) for f in os.listdir(ERROR_DIR)]
    if files:
        latest_file = max(files, key=os.path.getctime)
        with open(latest_file, "r") as f:
            error_details = f.read()

# --- UI DISPLAY ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Current Job Status")
    if status_color == "success":
        st.success(status)
    elif status_color == "error":
        st.error(status)
    elif status_color == "warning":
        st.warning(status)
    else:
        st.info(status)

    if error_details:
        st.subheader("Error Logs Details")
        st.text_area("Log Content:", error_details, height=250)

with col2:
    st.subheader("Execution Controls")
    
    if is_locked:
        st.button(f"Script is Already Running", disabled=True, key="disabled_btn")
        st.info("Manual trigger disabled because a lock (.lck) file exists in the usage folder.")
    else:
        if st.button(f"Trigger {selected_service} Manually", type="primary", key="active_btn"):
            if os.path.exists(SCRIPT_SH):
                st.warning(f"Triggering {selected_service}/{SCRIPT_SH_NAME}...")
                try:
                    process = subprocess.Popen(["bash", SCRIPT_SH_NAME], 
                                               cwd=CURRENT_SERVICE_DIR,
                                               stdout=subprocess.PIPE, 
                                               stderr=subprocess.PIPE)
                    st.success(f"{selected_service} script triggered successfully!")
                except Exception as e:
                    st.error(f"Could not start script: {e}")
            else:
                st.error(f"nsdl_aeps.sh not found in {selected_service} folder!")



# --- NEW CONCEPT: PLAYGROUND RUNNER ENGINE ---
st.markdown("---")
st.subheader(f"🎛️ Safe Playground Editor ({selected_service}/)")

# Session state initialize kar rahe hain taaki state track ho sake
if "code_loaded" not in st.session_state:
    st.session_state.code_loaded = False

if os.path.exists(CURRENT_SERVICE_DIR):
    all_files_in_dir = [
        f for f in os.listdir(CURRENT_SERVICE_DIR) 
        if os.path.isfile(os.path.join(CURRENT_SERVICE_DIR, f)) and (f.endswith('.py') or f.endswith('.sh'))
    ]
    all_files_in_dir.sort()

    if all_files_in_dir:
        selected_file_to_view = st.selectbox("📝 Select Production File to Load in Playground:", all_files_in_dir)
        
        if selected_file_to_view:
            full_file_path = os.path.join(CURRENT_SERVICE_DIR, selected_file_to_view)
            
            try:
                with open(full_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    production_content = f.read()
                
                st.info(f"ℹ️ Original code of {selected_file_to_view} loaded below. Modify it freely; production file will NOT be harmed.")
                
                # Playground Editor Text Area
                # --- PROFESSIONAL CODE EDITOR CHOSEN ---
                # Yeh automatic indentation, line numbers aur theme support karega
                modified_content = st_ace(
                    value=production_content,
                    language="python" if selected_file_to_view.endswith('.py') else "sh",
                    theme="monokai",          # Dark theme (VS Code jaisa)
                    keybinding="vscode",
                    font_size=14,
                    tab_size=4,               # Python ke liye 4 spaces automatic indent
                    wrap=True,
                    height=400,
                    auto_update=True,
                    key=f"ace_{selected_service}_{selected_file_to_view}"
                )
                
                PLAYGROUND_DIR = os.path.join(BASE_SERVER_DIR, "playground")
                ext = ".py" if selected_file_to_view.endswith('.py') else ".sh"
                target_playground_file = os.path.join(PLAYGROUND_DIR, f"playground{ext}")
                
                
                # STEP 1: KEWAL LOAD KARNE KA BUTTON
                # STEP 1: KEWAL LOAD KARNE KA BUTTON (Unique Key Added)
                if st.button(f"📥 Load Code into Template (No Run)", type="secondary", key=f"load_btn_{selected_service}_{selected_file_to_view}"):
                    if not os.path.exists(PLAYGROUND_DIR):
                        os.makedirs(PLAYGROUND_DIR)
                        
                    with open(target_playground_file, "w", encoding="utf-8") as f:
                        f.write(modified_content)
                        
                    st.session_state.code_loaded = True
                    
                    # File type ke hisab se message badlega
                    if selected_file_to_view.endswith('.sh'):
                        st.success(f"🎉 Shell Script loaded! Now clear the security check below to run.")
                    else:
                        st.success(f"🎉 Python file successfully loaded into playground/playground.py!")

                # --- LAYER CONFIGURATION FOR .SH FILES ONLY ---
                # Agar file .sh hai, toh security check aur RUN button dono dikhenge
                if selected_file_to_view.endswith('.sh'):
                    if st.session_state.code_loaded:
                        st.markdown("---")
                        st.markdown("⚠️ **Playground Execution Security Check (.sh File Detected)**")
                        
                        confirm_run = st.checkbox("I confirm that I want to execute this temporary playground script.", key=f"confirm_run_{selected_service}")
                        
                        secret_pin = st.text_input(
                            "Enter Admin/Manager Security PIN to authorize execution:", 
                            type="password", 
                            value="", 
                            key=f"run_pin_{selected_service}"
                        )
                        
                        # STEP 3: RUN BUTTON (SABHI CHECK PASS HONE PAR)
                        if confirm_run and secret_pin == "admin123":
                            if st.button(f"🚀 Authorization Approved: Run Playground Template", type="primary"):
                                st.warning("Triggering playground template on background...")
                                try:
                                    if os.name == 'nt':
                                        process = subprocess.Popen(["cmd", "/c", f"echo Running playground template on Windows"], cwd=PLAYGROUND_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                        st.success("[WINDOWS MOCK] Playground script executed!")
                                    else:
                                        process = subprocess.Popen(["bash", "playground.sh"], cwd=PLAYGROUND_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                        st.success("Playground script triggered successfully on Linux server!")
                                    
                                    st.session_state.code_loaded = False
                                    
                                except Exception as e:
                                    st.error(f"Could not run playground: {e}")
                                    
                        elif confirm_run and secret_pin != "":
                            st.error("❌ Invalid Security PIN! Execution blocked.")
                        else:
                            st.info("💡 Please check the confirmation box and enter the correct PIN to enable the Run button.")
                
                # Agar file .py hai, toh security aur run button hide ho jayenge
                else:
                    st.session_state.code_loaded = False # Py file ke liye running state reset aur blocked
                        
            except Exception as e:
                st.error(f"Error loading file to playground: {e}")
    else:
        st.text("No files found directly in this folder.")
                
                

# --- OUTPUT LOGS VIEW ---
st.markdown("---")
st.subheader(f"Recent Output Logs ({selected_service}/out/)")
if os.path.exists(OUT_DIR) and os.listdir(OUT_DIR):
    out_files = [os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR)]
    latest_out = max(out_files, key=os.path.getctime)
    with open(latest_out, "r") as f:
        st.text(f.read()[-1000:])
else:
    st.text("No output logs found in out/ folder.")