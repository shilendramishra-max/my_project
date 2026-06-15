#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, Form, HTTPException, status, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import datetime
import subprocess
from dotenv import load_dotenv
import uuid
from google.cloud import bigquery

app = FastAPI(title="Centralized Reconciliation Dashboard (FastAPI Production Engine)")

# It will load .env file in memory 
load_dotenv()

# Pick the pin from memory
SYSTEM_SECRET_PIN = os.getenv("ADMIN_SECURITY_PIN", None)

# Pick the history days from memory
END_HISTORY_DAYS = int(os.getenv("END_HISTORY_DAYS", 15))
STRAT_HISTORY_DAYS = int(os.getenv("STRAT_HISTORY_DAYS", 0))
# Log view character limit from memory
LOG_VIEW_CHARACTER_LIMIT = int(os.getenv("LOG_VIEW_CHARACTER_LIMIT", 1500))

# --- ABSOLUTE TEMPLATE PATH DETECTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(CURRENT_DIR, "templates"))

# --- SIBLING FOLDER CRONS PATH ---
BASE_SERVER_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../crons"))

project_id = os.getenv("PROJECT_ID",None)
os.environ['GOOGLE_CLOUD_QUOTA_PROJECT'] = project_id

# 🎯 BUG FIX 1: Variable name changed to bq_client to match internal endpoints
bq_client = bigquery.Client(project=project_id)
DATASET_PREFIX = os.getenv("DATASET",None)


# ========================================================
# ☁️ BIGQUERY LOGGING & UTILITY UTILS
# ========================================================
def log_activity_to_bq(username: str, action: str, service: str, status_val: str, details: str):
    table_id = f"{DATASET_PREFIX}.audit_logs"
    
    # 🎯 PYTHON 3.14 FIX: utcnow() replaced with timezone-aware ISO format
    current_utc_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    rows_to_insert = [{
        "id": str(uuid.uuid4()),
        "timestamp": current_utc_time,
        "username": username,
        "action": action,
        "service": service,
        "status": status_val,
        "details": details
    }]
    try:
        bq_client.insert_rows_json(table_id, rows_to_insert)
    except Exception as e:
        print(f"🚨 BQ Logging Failed: {str(e)}")

def verify_user_from_bq(username_input: str, password_input: str) -> bool:
    query = f"SELECT username FROM `{DATASET_PREFIX}.users` WHERE username = @username AND password = @password LIMIT 1"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username_input),
            bigquery.ScalarQueryParameter("password", "STRING", password_input),
        ]
    )
    try:
        query_job = bq_client.query(query, job_config=job_config)
        return len(list(query_job.result())) > 0
    except Exception as e:
        print(f"🚨 BQ Auth Query Failed: {str(e)}")
        return False

# 🎯 FIXED MIDDLEWARE: Dashboard actions aur API paths par strict no-store session nahi todega
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    
    if request.url.path in ["/login", "/logout"]:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    else:
        response.headers["Cache-Control"] = "no-store,no-cache, must-revalidate, max-age=0"
        
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ========================================================
# 🔑 LOGIN & LOGOUT ROUTING ENGINES
# ========================================================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
   if request.cookies.get("session_user"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
   return templates.TemplateResponse(request, name="login.html", context={})

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    if verify_user_from_bq(username, password):
        log_activity_to_bq(username, "LOGIN", "SYSTEM", "SUCCESS", "Logged in via VPN Link")
        
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="session_user", 
            value=username, 
            path="/",               # ◄── Secure domain-wide lock
            httponly=True,          
            samesite="lax"          
        )
        return response
    
    log_activity_to_bq(username, "LOGIN", "SYSTEM", "❌ FAILED", f"Wrong credentials typed for user: {username}")
    return RedirectResponse(url="/login?error=true", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/logout")
async def handle_logout(request: Request):
    username = request.cookies.get("session_user") or "Unknown_User"
    log_activity_to_bq(username, "LOGOUT", "SYSTEM", "SUCCESS", "User logged out safely")
    
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_user", path="/")
    return response

@app.get("/logout", include_in_schema=False)
async def handle_logout_get_fallback(request: Request):
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

def get_all_services():
    if not os.path.exists(BASE_SERVER_DIR):
        return []
    return sorted([
        f for f in os.listdir(BASE_SERVER_DIR) 
        if os.path.isdir(os.path.join(BASE_SERVER_DIR, f)) 
        and not f.startswith('.') 
        and f != 'playground'
        and f != 'cleanup'  
    ])

# 1. Main Dashboard Router Interface
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, service: str = None, date: str = None):
    # 🔒 SECURITY BLOCK: Guard mechanism active
    username = request.cookies.get("session_user")
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    services = get_all_services()
    if not service and services:
        service = services[0]
        
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    selected_date = date if date else today_str
        
    status_msg = "⚪ NOT STARTED / PENDING"
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
        
        today_lck_file = os.path.join(usage_dir, f"check_usage-{today_str}.lck")
        
        if os.path.exists(today_lck_file):
            is_locked = True
            status_msg = "⏳ RUNNING / LOCKED (Process is currently executing)"
            
        target_success_file = os.path.join(stat_dir, f"stat-{selected_date}.txt")
        target_error_file = os.path.join(stat_error_dir, f"stat-{selected_date}.txt")
        target_shell_error = os.path.join(error_dir, f"error-{selected_date}.txt")
        
        if is_locked and selected_date == today_str:
            status_msg = "⏳ RUNNING / LOCKED (Process is currently executing)"
        else:
            if os.path.exists(target_success_file) and os.path.getsize(target_success_file) > 0:
                with open(target_success_file, "r", encoding="utf-8") as f:
                    if f.read().strip() == "1":
                        status_msg = "✅ COMPLETE / SUCCESS"
                    else:
                        status_msg = "⚠️ INCOMPLETE / NO SUCCESS FLAG"
            elif os.path.exists(target_error_file) or (os.path.exists(target_shell_error) and os.path.getsize(target_shell_error) > 0):
                status_msg = "🚨 SCRIPT ERROR / FAILED (Check Logs)"
                if os.path.exists(target_shell_error) and os.path.getsize(target_shell_error) > 0:
                    with open(target_shell_error, "r", encoding="utf-8", errors="ignore") as f: 
                        error_details = f.read()
            else:
                status_msg = "⚪ NOT STARTED / PENDING"

        for i in range(STRAT_HISTORY_DAYS, END_HISTORY_DAYS):
            date_to_check = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            
            check_lck_path = os.path.join(usage_dir, f"check_usage-{date_to_check}.lck")
            check_success_path = os.path.join(stat_dir, f"stat-{date_to_check}.txt")
            check_error_path = os.path.join(stat_error_dir, f"stat-{date_to_check}.txt")
            check_shell_err_path = os.path.join(error_dir, f"error-{date_to_check}.txt")
            
            day_status = "⏳ Pending"
            day_color = "gray"
            
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
                    
            elif os.path.exists(check_lck_path):
                day_status = "⏳ Running"
                day_color = "yellow"
                
            elif (os.path.exists(check_error_path) and os.path.getsize(check_error_path) > 0) or (os.path.exists(check_shell_err_path) and os.path.getsize(check_shell_err_path) > 0):
                day_status = "❌ Failed / Error"
                day_color = "red"
                
            elif (os.path.exists(check_success_path) and os.path.getsize(check_success_path) == 0) or (os.path.exists(check_error_path) and os.path.getsize(check_error_path) == 0):
                day_status = "⏳ Incomplete (0B)"
                day_color = "yellow"
            
            recon_history.append({
                "date": date_to_check, 
                "status": day_status, 
                "color": day_color
            })
            
        if os.path.exists(current_dir):
            files = sorted([f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f)) and (f.endswith('.py') or f.endswith('.sh'))])
            
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
            "user": username, 
            "services": services,
            "selected_service": service,
            "status": status_msg, 
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
async def get_file_content(request: Request, service: str, filename: str):
    username = request.cookies.get("session_user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized session.")
        
    file_path = os.path.join(BASE_SERVER_DIR, service, filename)
    if os.path.exists(file_path):
        log_activity_to_bq(username, "LOAD_TEMPLATE", service, "SUCCESS", f"Viewed code for {filename}")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return {"content": f.read()}
    raise HTTPException(status_code=404, detail="File not found")

# 3. API Endpoint: Load/Save Code modifications inside Isolated Sandbox
@app.post("/api/load-playground")
async def load_playground(request: Request, service: str = Form(...), filename: str = Form(...), content: str = Form(...)):
    username = request.cookies.get("session_user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

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
        
    log_activity_to_bq(username, "SAVE_PLAYGROUND", service, "SUCCESS", f"Saved modified template to Sandbox as {target_name}")
    return {
        "status": "success", 
        "message": f"🎉 Content successfully written to {service}/playground/{target_name}!"
    }

# 4. API Endpoint: Safe Dynamic Authorize Execution for Playground
@app.post("/api/run-playground")
async def run_playground(request: Request, service: str = Form(...), pin: str = Form(...), confirm: bool = Form(...)):
    username = request.cookies.get("session_user") or "Unknown_User"
    
    if SYSTEM_SECRET_PIN is None or SYSTEM_SECRET_PIN == "":
        log_activity_to_bq(username, "TRIGGER_SCRIPT", service, "❌ FAILED", "Server PIN config error")
        return JSONResponse(status_code=500, content={"status": "error", "message": "❌ Server Security Misconfiguration: PIN is missing on host!"})
    if pin != SYSTEM_SECRET_PIN or not confirm:
        log_activity_to_bq(username, "TRIGGER_SCRIPT", service, "❌ REJECTED", "Invalid Security PIN attempt hit")
        return JSONResponse(status_code=403, content={"status": "error", "message": "❌ Invalid Security PIN or Unconfirmed Action!"})
        
    service_playground_dir = os.path.join(BASE_SERVER_DIR, service, "playground")
    target_sh_script = os.path.join(service_playground_dir, "playground.sh")
    
    if not os.path.exists(target_sh_script):
        log_activity_to_bq(username, "TRIGGER_SCRIPT", service, "❌ FAILED", "playground.sh file missing from workspace")
        return JSONResponse(status_code=404, content={"status": "error", "message": f"❌ playground.sh not found inside {service}/playground/!"})
        
    try:
        if os.name == 'nt':
            git_bash_path = r"C:\Users\shilendra.mishra_spi\AppData\Local\Programs\Git\usr\bin\bash.exe"
            subprocess.Popen([git_bash_path, "playground.sh"], cwd=service_playground_dir)
        else:
            subprocess.Popen(["bash", "playground.sh"], cwd=service_playground_dir)
            
        log_activity_to_bq(username, "TRIGGER_SCRIPT", service, "⏳ STARTED", "Playground script processing initiated in GitBash background")
        return {
            "status": "success", 
            "message": f"🚀 Playground script triggered successfully inside {service}/playground/ folder!"
        }
    except Exception as e:
        log_activity_to_bq(username, "TRIGGER_SCRIPT", service, "🚨 CRASHED", f"Subprocess error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. API Endpoint: AD-HOC SYSTEM FILES DELETION / TRUNCATION ENGINE
@app.post("/api/delete-file")
async def delete_file(request: Request, service: str = Form(...), relative_path: str = Form(...), action: str = Form(...)):
    username = request.cookies.get("session_user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    if ".." in relative_path or relative_path.startswith("/"):
        log_activity_to_bq(username, f"FILE_{action.upper()}", service, "❌ ATTACK_BLOCKED", f"Directory traversal attempt: {relative_path}")
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
            
        log_activity_to_bq(username, f"FILE_{action.upper()}", service, "SUCCESS", f"Performed file modification on {relative_path}")
        return {"status": "success", "message": message_response}
    except Exception as e:
        log_activity_to_bq(username, f"FILE_{action.upper()}", service, "🚨 ERROR", f"FS Operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# 6. API Endpoint: SECURE CLEANUP ENGINE WITH AUTOMATIC DATA INJECTION
@app.post("/api/execute-cleanup")
async def execute_cleanup(request: Request, script_name: str = Form(...), target_date: str = Form(...)):
    username = request.cookies.get("session_user") or "Unknown_User"
        
    cleanup_dir = os.path.join(BASE_SERVER_DIR, "cleanup")
    target_script_path = os.path.join(cleanup_dir, script_name)
    
    if not os.path.exists(target_script_path):
        log_activity_to_bq(username, "RUN_CLEANUP", "CLEANUP", "❌ FAILED", f"Script {script_name} missing")
        return JSONResponse(status_code=404, content={"status": "error", "message": f"❌ Cleanup script '{script_name}' not found!"})
        
    try:
        exec_cmd = ["python3", script_name] if os.name != 'nt' else ["python", script_name]
        
        process = subprocess.Popen(
            exec_cmd,
            cwd=cleanup_dir,
            stdin=subprocess.PIPE,  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  
        )
        
        process.stdin.write(f"{target_date}\n")
        process.stdin.flush()  
        
        log_activity_to_bq(username, "RUN_CLEANUP", "CLEANUP", "⏳ STARTED", f"Executed script: {script_name} for date: {target_date}")
        return {
            "status": "success",
            "message": f"🧹 Cleanup process for '{script_name}' triggered for date {target_date} in background!"
        }
        
    except Exception as e:
        log_activity_to_bq(username, "RUN_CLEANUP", "CLEANUP", "🚨 CRASHED", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ========================================================
# 🆕 API ENDPOINT: LIVE TAIL LOG STREAMER
# ========================================================
@app.get("/api/stream-live-logs")
async def stream_live_logs(service: str, date: str):
    current_dir = os.path.join(BASE_SERVER_DIR, service)
    out_dir = os.path.join(current_dir, "out")
    target_out_file = os.path.join(out_dir, f"out-{date}.txt")
    
    if os.path.exists(target_out_file):
        try:
            with open(target_out_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                last_lines = lines[-30:] if len(lines) > 30 else lines
                return {"status": "found", "data": "".join(last_lines)}
        except Exception as e:
            return {"status": "error", "data": f"Error reading logs: {str(e)}"}
            
    return {"status": "not_found", "data": f"Waiting for live trace logs..."}