from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import datetime
import subprocess

app = FastAPI(title="Centralized Reconciliation Dashboard (FastAPI Production Engine)")

# --- ABSOLUTE TEMPLATE PATH DETECTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(CURRENT_DIR, "templates"))

# --- SIBLING FOLDER CRONS PATH ---
BASE_SERVER_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../crons"))

def get_all_services():
    if not os.path.exists(BASE_SERVER_DIR):
        return []
    return sorted([
        f for f in os.listdir(BASE_SERVER_DIR) 
        if os.path.isdir(os.path.join(BASE_SERVER_DIR, f)) and not f.startswith('.') and f != 'playground'
    ])

# 1. Main Dashboard Router Interface
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, service: str = None):
    services = get_all_services()
    
    if not service and services:
        service = services[0]
        
    status = "⚪ NOT STARTED / PENDING"
    error_details = ""
    is_locked = False
    files = []
    recon_history = []
    
    if service:
        current_dir = os.path.join(BASE_SERVER_DIR, service)
        stat_dir = os.path.join(current_dir, "stat")
        stat_error_dir = os.path.join(stat_dir, "error")
        out_dir = os.path.join(current_dir, "out")
        error_dir = os.path.join(current_dir, "error")
        usage_dir = os.path.join(current_dir, "usage")
        
        # Exact Shell LCK Path Configuration for Today
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        today_lck_file = os.path.join(usage_dir, f"check_usage-{today_str}.lck")
        
        # 1. CURRENT DAY LOCK DETECTION
        if os.path.exists(today_lck_file):
            is_locked = True
            status = "⏳ RUNNING / LOCKED (Process is currently executing)"
            
        # 2. CURRENT DAY STATUS CALCULATION
        today_success_file = os.path.join(stat_dir, f"stat-{today_str}.txt")
        today_error_file = os.path.join(stat_error_dir, f"stat-{today_str}.txt")
        today_shell_error = os.path.join(error_dir, f"error-{today_str}.txt")
        
        if not is_locked:
            if os.path.exists(today_success_file) and os.path.getsize(today_success_file) > 0:
                with open(today_success_file, "r", encoding="utf-8") as f:
                    if f.read().strip() == "1":
                        status = "✅ COMPLETE / SUCCESS"
                    else:
                        status = "⚠️ INCOMPLETE / NO SUCCESS FLAG"
            elif os.path.exists(today_error_file) or (os.path.exists(today_shell_error) and os.path.getsize(today_shell_error) > 0):
                status = "🚨 SCRIPT ERROR / FAILED (Check Logs)"
                # Reading the latest shell or console logs to show on card
                if os.path.exists(today_shell_error) and os.path.getsize(today_shell_error) > 0:
                    with open(today_shell_error, "r", encoding="utf-8", errors="ignore") as f: error_details = f.read()

        # --- SMART HISTORY TRACKER LOGIC (PAST 5 DAYS) ---
        for i in range(5):
            date_to_check = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            
            check_lck_path = os.path.join(usage_dir, f"check_usage-{date_to_check}.lck")
            check_success_path = os.path.join(stat_dir, f"stat-{date_to_check}.txt")
            check_error_path = os.path.join(stat_error_dir, f"stat-{date_to_check}.txt")
            check_shell_err_path = os.path.join(error_dir, f"error-{date_to_check}.txt")
            
            day_status = "⏳ Pending"
            day_color = "gray"
            
            # CONDITION 1: Check if it's currently running
            if os.path.exists(check_lck_path):
                day_status = "⏳ Running"
                day_color = "yellow"
                
            # CONDITION 2: Check if script explicitly marked as Python Error or Shell Error
            elif os.path.exists(check_error_path) or (os.path.exists(check_shell_err_path) and os.path.getsize(check_shell_err_path) > 0):
                day_status = "❌ Failed / Error"
                day_color = "red"
                
            # CONDITION 3: Check for Success File & Flag Content
            elif os.path.exists(check_success_path):
                file_size = os.path.getsize(check_success_path)
                if file_size > 0:
                    try:
                        with open(check_success_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                        if content == "1":
                            day_status = "✅ Success"
                            day_color = "green"
                        else:
                            day_status = "⚠️ No Flag"
                            day_color = "yellow"
                    except:
                        day_status = "⚠️ Read Error"
                        day_color = "yellow"
                else:
                    day_status = "⏳ Incomplete (0B)"
                    day_color = "yellow"
            
            recon_history.append({
                "date": date_to_check, 
                "status": day_status, 
                "color": day_color
            })
            
        # Fetching dynamic editable template files (.py & .sh)
        if os.path.exists(current_dir):
            files = sorted([f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f)) and (f.endswith('.py') or f.endswith('.sh'))])
            # =========================================================================
        # 📋 NEW DIRECT LOG READING BLOCK (FOR OUT LOGS & ERROR LOGS)
        # =========================================================================
        out_details = ""
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 1. Standard Out Log (.txt) ko hamesha read karein taaki user processing dekh sake
        today_out_file = os.path.join(out_dir, f"out-{today_str}.txt")
        if os.path.exists(today_out_file) and os.path.getsize(today_out_file) > 0:
            with open(today_out_file, "r", encoding="utf-8", errors="ignore") as f:
                # Aakhiri 1500 characters dikhayenge taaki screen par space zyada na ghure
                out_details = f.read()[-1500:]
        else:
            out_details = "No output logs found for today yet."

        # 2. Standard Error Log (.txt) agar exist karta hai toh use error_details me dalein
        today_shell_error = os.path.join(error_dir, f"error-{today_str}.txt")
        if os.path.exists(today_shell_error) and os.path.getsize(today_shell_error) > 0:
            with open(today_shell_error, "r", encoding="utf-8", errors="ignore") as f:
                error_details = f.read()
        # =========================================================================
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "services": services,
            "selected_service": service,
            "status": status,
            "out_details": out_details,
            "error_details": error_details,
            "files": files,
            "is_locked": is_locked,
            "recon_history": recon_history
        }
    )

# 2. API Endpoint: Fetch Production Code Content
@app.get("/api/get-file-content")
async def get_file_content(service: str, filename: str):
    file_path = os.path.join(BASE_SERVER_DIR, service, filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return {"content": f.read()}
    raise HTTPException(status_code=404, detail="File not found")

# 3. API Endpoint: Load/Save Code modifications inside Sandbox
@app.post("/api/load-playground")
async def load_playground(service: str = Form(...), filename: str = Form(...), content: str = Form(...)):
    playground_dir = os.path.join(BASE_SERVER_DIR, "playground")
    os.makedirs(playground_dir, exist_ok=True)
    
    ext = ".py" if filename.endswith('.py') else ".sh"
    target_file = os.path.join(playground_dir, f"playground{ext}")
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    return {"status": "success", "message": f"🎉 Code successfully loaded into playground/playground{ext}!"}

# 4. API Endpoint: Safe Authorize Execution for Playground (.sh only)
@app.post("/api/run-playground")
async def run_playground(pin: str = Form(...), confirm: bool = Form(...)):
    if pin != "admin123" or not confirm:
        return JSONResponse(status_code=403, content={"status": "error", "message": "❌ Invalid Security PIN or Unconfirmed Action!"})
        
    playground_dir = os.path.join(BASE_SERVER_DIR, "playground")
    
    try:
        if os.name == 'nt':
            subprocess.Popen(["cmd", "/c", "echo Running playground template on Windows"], cwd=playground_dir)
        else:
            subprocess.Popen(["bash", "playground.sh"], cwd=playground_dir)
        return {"status": "success", "message": "🚀 Playground script triggered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))