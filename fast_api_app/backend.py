#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import datetime
import subprocess
from dotenv import load_dotenv

app = FastAPI(title="Centralized Reconciliation Dashboard (FastAPI Production Engine)")

# It will load .env file in memory 
load_dotenv()

# Pick the pin from memory
SYSTEM_SECRET_PIN = os.getenv("ADMIN_SECURITY_PIN", None)

# Pick the history days from memory
DASHBOARD_HISTORY_DAYS = int(os.getenv("DASHBOARD_HISTORY_DAYS", 15))

# Log view character limit from memory
LOG_VIEW_CHARACTER_LIMIT = int(os.getenv("LOG_VIEW_CHARACTER_LIMIT", 1500))

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
        if os.path.isdir(os.path.join(BASE_SERVER_DIR, f)) 
        and not f.startswith('.') 
        and f != 'playground'
        and f != 'cleanup'  # 🚨 BUG FIX: Main navigation me cleanup folder ko aane se roka
    ])

# 1. Main Dashboard Router Interface
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, service: str = None, date: str = None):
    services = get_all_services()
    if not service and services:
        service = services[0]
        
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    selected_date = date if date else today_str
        
    status = "⚪ NOT STARTED / PENDING"
    error_details = ""
    is_locked = False
    files = []
    operational_files = []  
    recon_history = []
    
    if service:
        current_dir = os.path.join(BASE_SERVER_DIR, service)
        stat_dir = os.path.join(current_dir, "stat")
        stat_error_dir = os.path.join(stat_dir, "error")
        out_dir = os.path.join(current_dir, "out")
        error_dir = os.path.join(current_dir, "error")
        usage_dir = os.path.join(current_dir, "usage")
        missing_dir = os.path.join(current_dir, "missing")  
        
        # Exact Shell LCK Path Configuration for Today
        today_lck_file = os.path.join(usage_dir, f"check_usage-{today_str}.lck")
        
        # 1. CURRENT DAY LOCK DETECTION
        if os.path.exists(today_lck_file):
            is_locked = True
            status = "⏳ RUNNING / LOCKED (Process is currently executing)"
            
        # 2. SELECTED DATE STATUS CALCULATION
        target_success_file = os.path.join(stat_dir, f"stat-{selected_date}.txt")
        target_error_file = os.path.join(stat_error_dir, f"stat-{selected_date}.txt")
        target_shell_error = os.path.join(error_dir, f"error-{selected_date}.txt")
        
        # Lock check 
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

        # --- SMART HISTORY TRACKER LOGIC (PAST X DAYS VIA .ENV) ---
        for i in range(DASHBOARD_HISTORY_DAYS):
            date_to_check = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            
            check_lck_path = os.path.join(usage_dir, f"check_usage-{date_to_check}.lck")
            check_success_path = os.path.join(stat_dir, f"stat-{date_to_check}.txt")
            check_error_path = os.path.join(stat_error_dir, f"stat-{date_to_check}.txt")
            check_shell_err_path = os.path.join(error_dir, f"error-{date_to_check}.txt")
            
            day_status = "⏳ Pending"
            day_color = "gray"
            
            # ✅ STEP 1: STRICT SUCCESS CHECK
            if os.path.exists(check_success_path) and os.path.getsize(check_success_path) > 0:
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
                    
            # ⏳ STEP 2: CHECK RUNNING 
            elif os.path.exists(check_lck_path):
                day_status = "⏳ Running"
                day_color = "yellow"
                
            # ❌ STEP 3: ERROR ENVELOPE CHECK 
            elif os.path.exists(check_error_path) or (os.path.exists(check_shell_err_path) and os.path.getsize(check_shell_err_path) > 0):
                day_status = "❌ Failed / Error"
                day_color = "red"
                
            # ⏳ STEP 4: SUCCESS FILE AND SIZE 0-BYTE 
            elif os.path.exists(check_success_path) and os.path.getsize(check_success_path) == 0:
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
            
        # --- LOG READING BLOCK ---
        out_details = ""
        target_out_file = os.path.join(out_dir, f"out-{selected_date}.txt")
        if os.path.exists(target_out_file) and os.path.getsize(target_out_file) > 0:
            with open(target_out_file, "r", encoding="utf-8", errors="ignore") as f:
                out_details = f.read()[-LOG_VIEW_CHARACTER_LIMIT:]
        else:
            out_details = f"No output logs found for date: {selected_date}"

        target_error_file = os.path.join(error_dir, f"error-{selected_date}.txt")
        if os.path.exists(target_error_file) and os.path.getsize(target_error_file) > 0:
            with open(target_error_file, "r", encoding="utf-8", errors="ignore") as f:
                error_details = f.read()
                
        # --- AUTOMATED STRUCTURAL ENGINE SCANNER ---
        operational_files = {
            "stat": [],
            "stat/error": [],
            "error": [],
            "missing": []
        }
        
        target_folders = {
            "stat": stat_dir,
            "stat/error": stat_error_dir,
            "error": error_dir,
            "missing": missing_dir
        }
        
        for prefix, path in target_folders.items():
            if os.path.exists(path):
                for f in sorted(os.listdir(path)):
                    if os.path.isfile(os.path.join(path, f)) and not f.startswith('.'):
                        operational_files[prefix].append(f"{prefix}/{f}")

    # --- DYNAMIC CLEANUP FOLDER SCANNER ---
    cleanup_dir = os.path.join(BASE_SERVER_DIR, "cleanup")
    cleanup_scripts = []
    
    if os.path.exists(cleanup_dir) and os.path.isdir(cleanup_dir):
        cleanup_scripts = sorted([
            f for f in os.listdir(cleanup_dir) 
            if os.path.isfile(os.path.join(cleanup_dir, f)) and f.endswith(".py")
        ])

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
            "operational_files": operational_files,  
            "is_locked": is_locked,
            "recon_history": recon_history,
            "selected_date": selected_date,
            "cleanup_scripts": cleanup_scripts,
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

# 3. API Endpoint: Load/Save Code modifications inside Isolated Sandbox
@app.post("/api/load-playground")
async def load_playground(service: str = Form(...), filename: str = Form(...), content: str = Form(...)):
    service_playground_dir = os.path.join(BASE_SERVER_DIR, service, "playground")
    os.makedirs(service_playground_dir, exist_ok=True)
    
    if filename.lower().endswith('.py'):
        target_name = "playground.py"
    else:
        target_name = "playground.sh"
        
    target_file = os.path.join(service_playground_dir, target_name)
    
    with open(target_file, "w", encoding="utf-8", newline='\n') as f:
        f.write(content)
        
    if target_name == "playground.sh" and os.name != 'nt':
        os.chmod(target_file, 0o755)
        
    return {
        "status": "success", 
        "message": f"🎉 Content successfully written to {service}/playground/{target_name}!"
    }

# 4. API Endpoint: Safe Dynamic Authorize Execution for Playground
@app.post("/api/run-playground")
async def run_playground(service: str = Form(...), pin: str = Form(...), confirm: bool = Form(...)):
    if SYSTEM_SECRET_PIN is None or SYSTEM_SECRET_PIN == "":
        return JSONResponse(status_code=500, content={"status": "error", "message": "❌ Server Security Misconfiguration: PIN is missing on host!"})
    if pin != SYSTEM_SECRET_PIN or not confirm:
        return JSONResponse(status_code=403, content={"status": "error", "message": "❌ Invalid Security PIN or Unconfirmed Action!"})
        
    service_playground_dir = os.path.join(BASE_SERVER_DIR, service, "playground")
    target_sh_script = os.path.join(service_playground_dir, "playground.sh")
    
    if not os.path.exists(target_sh_script):
        return JSONResponse(status_code=404, content={"status": "error", "message": f"❌ playground.sh not found inside {service}/playground/!"}) # 🚨 BUG FIX: Status code changed from 44 to 404
        
    try:
        if os.name == 'nt':
            subprocess.Popen(["cmd", "/c", "echo Running playground template on Windows"], cwd=service_playground_dir)
        else:
            subprocess.Popen(["bash", "playground.sh"], cwd=service_playground_dir)
            
        return {
            "status": "success", 
            "message": f"🚀 Playground script triggered successfully inside {service}/playground/ folder!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. API Endpoint: AD-HOC SYSTEM FILES DELETION / TRUNCATION ENGINE
@app.post("/api/delete-file")
async def delete_file(service: str = Form(...), relative_path: str = Form(...), action: str = Form(...)):
    if ".." in relative_path or relative_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Security alert: Unsafe path structure bypass attempt blocked.")
        
    target_file_path = os.path.join(BASE_SERVER_DIR, service, relative_path)
    
    if not os.path.exists(target_file_path):
        return JSONResponse(status_code=404, content={"status": "error", "message": f"❌ Target execution file not found: {relative_path}"})
        
    try:
        if action == "delete":
            os.remove(target_file_path)
            message_response = f"🗑️ File '{relative_path}' completely removed from filesystem database storage."
        elif action == "truncate":
            with open(target_file_path, "w", encoding="utf-8") as f:
                f.write("")  
            message_response = f"🧹 Content inside '{relative_path}' truncated successfully down to 0B."
        else:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Operation signature verification validation failed."})
            
        return {"status": "success", "message": message_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 6. API Endpoint: SECURE CLEANUP ENGINE WITH AUTOMATIC DATA INJECTION
@app.post("/api/execute-cleanup")
async def execute_cleanup(script_name: str = Form(...), target_date: str = Form(...)):
    cleanup_dir = os.path.join(BASE_SERVER_DIR, "cleanup")
    target_script_path = os.path.join(cleanup_dir, script_name)
    
    if not os.path.exists(target_script_path):
        return JSONResponse(status_code=404, content={"status": "error", "message": f"❌ Cleanup script '{script_name}' not found!"})
        
    try:
        # Cross-platform command resolver (Ensures python3 compatibility on Linux environments)
        exec_cmd = ["python3", script_name] if os.name != 'nt' else ["python", script_name]
        
        process = subprocess.Popen(
            exec_cmd,
            cwd=cleanup_dir,
            stdin=subprocess.PIPE,  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  
        )
        
        # Injecting date dynamically with unix-newline command trigger
        process.stdin.write(f"{target_date}\n")
        process.stdin.flush()  
        
        return {
            "status": "success",
            "message": f"🧹 Cleanup process for '{script_name}' triggered for date {target_date} in background!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))