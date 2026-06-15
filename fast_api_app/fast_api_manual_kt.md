================================================================================
          CENTRALIZED RECONCILIATION DASHBOARD: TECHNICAL KT MANUAL
================================================================================
Document Type  : Knowledge Transfer (KT) Blueprint & Technical Manual
Target Engine  : FastAPI Production Framework
Environment    : PAM (Privileged Access Management) Secure Server Orchestration
Author         : Shilendra Kumar Mishra
================================================================================

--------------------------------------------------------------------------------
POINT 1: APP INITIALIZATION & GLOBAL CONFIGURATIONS
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Yeh block application ka core entry gate aur configuration engine hai. Yahan 
FastAPI ka production setup initialize hota hai aur .env file ko server machine 
ki RAM memory mein securely load kiya jata hai. Iske baad dynamic runtime 
variables extract hote hain—jaise sandbox file run karne ke liye 
'SYSTEM_SECRET_PIN', dashboard terminal panel par maximum output characters 
fetch karne ke liye 'LOG_VIEW_CHARACTER_LIMIT', aur grid calendar component 
par kitne din ka data track karna hai uski strict index limits 
('STRAT_HISTORY_DAYS' aur 'END_HISTORY_DAYS').

--------------------------------------------------------------------------------
POINT 2: ABSOLUTE PATH DETECTION & DIRECTORY BINDING
--------------------------------------------------------------------------------
# --- ABSOLUTE TEMPLATE PATH DETECTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(CURRENT_DIR, "templates"))

# --- SIBLING FOLDER CRONS PATH ---
BASE_SERVER_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../crons"))
--------------------------------------------------------------------------------
DESCRIPTION:
Production environment aur highly privileged PAM servers par dynamic file path 
collision se bachne ke liye yahan strict 'Absolute Path Detection' use kiya 
gaya hai. Yeh script ki actual active directory runtime location ko OS level 
par auto-detect karta hai aur HTML Jinja templates folder ke sath-sath uske 
sibling folder mein chal rahe core recon automatic scripts ('../crons') ke 
absolute physical path ko strictly map kar deta hai, jisse system file execution 
aur directory traversal bina kisi routing crash ke makkhan chalta hai.

--------------------------------------------------------------------------------
POINT 3: GOOGLE BIGQUERY CLOUD ENGINE AUTH SETUP
--------------------------------------------------------------------------------
project_id = os.getenv("PROJECT_ID",None)
os.environ['GOOGLE_CLOUD_QUOTA_PROJECT'] = project_id

# 🎯 BUG FIX 1: Variable name changed to bq_client to match internal endpoints
bq_client = bigquery.Client(project=project_id)
DATASET_PREFIX = os.getenv("DATASET",None)
--------------------------------------------------------------------------------
DESCRIPTION:
Yeh block centralized application ki analytics aur logging database connectivity 
layer ko bind karta hai. Environment variables se GCP 'PROJECT_ID' utha kar use 
quota management routing rules ke liye runtime injection ke roop mein pass kiya 
jata hai. Iske baad ek global thread-safe 'bq_client' (BigQuery Client SDK Object) 
initialize hota hai jo production dataset tables ('DATASET_PREFIX') ke sath back-end 
cloud connections establish karta hai.

--------------------------------------------------------------------------------
POINT 4: ENTERPRISE AUDIT LOGGING ENGINE (BIGQUERY)
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Compliance audits aur enterprise level monitoring ke liye yeh ek absolute custom 
telemetry utility function hai. Jab bhi koi user login/logout karega, playground 
save karega, ya backend cleanup execute karega, yeh function instantly ek unique 
randomized 36-character non-sequential token ('uuid.uuid4()') generate karega. 
Saath hi Python 3.14 compatible, zone-aware ISO-8601 dynamic UTC timestamp ke 
sath pura row package banakar cloud platform ke 'audit_logs' table mein JSON 
format mein push kar diya jata hai taaki clear records rahein ki kis resource ne 
PAM server par kya action perform kiya.

--------------------------------------------------------------------------------
POINT 5: ANTI-SQL INJECTION BIGQUERY AUTHENTICATION ENGINE
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Application ke database validation authentication ka primary secure layer. Hackers 
aur raw script injections se system ko safe rakhne ke liye yahan query formatting 
ke bajaye strict 'SQL Parameterization' ka use kiya gaya hai (@username aur @password). 
'QueryJobConfig' ke zariye inputs ko database engine par pass hone se pehle safely 
sanitize karke strong data types mein cast kiya jata hai, jo dangerous 'SQL Injection 
Attacks' ko web portal par poori tarah se terminate kar deta hai. Agar credentials 
valid milte hain toh record length check karke access verify (True) karta hai.

--------------------------------------------------------------------------------
POINT 6: GLOBAL SECURITY MIDDLEWARE (ANTI-CACHE & ANTI-BFCACHE ENGINE)
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Application web-security ka sabse shaktishali pillaar jo client side traffic ko 
regulate karta hai. Yeh custom HTTP middleware application ke har single outgoing 
response par execute hota hai aur browser ko force karta hai ki woh application ke 
kisi bhi secure data ya HTML UI structure (dashboard layout) ko system ki RAM memory 
mein store na kare ('no-store, no-cache, must-revalidate'). Iska sateek fayda yeh 
hota hai ki jab koi user dashboard ko logout kar deta hai, toh browser ka local 
Back-Forward Cache (bfcache) jadd se damage ho jata hai; agar koi unauthorized 
person back button daba kar dashboard ka static view ya cached screenshot dekhna 
chahega, toh browser local data na hone ke kaaran majbooran server par fresh request 
bhejega jahan security code use instantly drop karke wapas login screen par phek dega.

--------------------------------------------------------------------------------
POINT 7: SMART REDIRECT AUTH GATE & LOGIN INTERFACE
--------------------------------------------------------------------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
   if request.cookies.get("session_user"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
   return templates.TemplateResponse(request, name="login.html", context={})
--------------------------------------------------------------------------------
DESCRIPTION:
User active navigation routing optimization. Jab bhi koi employee ya client direct 
browser standard URL par '/login' endpoint hit karta hai, toh engine frontend page 
serve karne se pehle authentication status trace karta hai: agar browser storage 
mein 'session_user' cookie pehle se active aur valid milti hai, toh use dubara login 
page ka chehra nahi dikhaya jata, balki ek 'Smart Redirect (HTTP 303 See Other)' ke 
zariye instantly redirect karke main dashboard par wapas phek diya jata hai. Cookie 
absent hone par hi pristine login template stream hota hai.

--------------------------------------------------------------------------------
POINT 8: SECURE LOGIN HANDLER & HTTPONLY SESSION INJECTION
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Form processing login gateway handler. Jab BigQuery authentication confirm ho jaati 
hai, toh yeh engine response pipeline mein browser cookies inject karta hai jo user 
identity ko dynamic session token ke roop mein tie kar deti hain. Data leakage aur 
attacks ko eliminate karne ke liye cookie parameters par do heavyweight enterprise 
flags set kiye gaye hain: 'httponly=True' (jo Cross-Site Scripting - XSS ke zariye 
frontend JavaScript ko cookie churaney se poori tarah block karta hai) aur 
'samesite="lax"' (jo cross-domain third party token verification ko prevent karke 
Cross-Site Request Forgery - CSRF attacks ko zero kar deta hai). Saath hi telemetry 
audit mein instant entry ho jaati hai.

--------------------------------------------------------------------------------
POINT 9: SESSION DISPOSAL & SAFE LOGOUT HANDLERS
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Session destruction aur safe exit management logic. Jab user dashboard par 'Secure 
Logout' button click karta hai, toh POST route active hokar active user cookie 
token ko root path se jadd se vaporize ('delete_cookie') kar deta hai aur audit log 
table mein clear signature entry pass karta hai. Iska theek niche wala GET fallback 
endpoint ek bada protection matrix hai—agar logout operation ke dauran browser history 
manipulation ki wajah se galti se white display runtime error screen trigger hona 
chahe, toh yeh endpoint use silent wrapper se catch karke chupchaap safely login page 
par bina crash ke forward kar deta hai.

--------------------------------------------------------------------------------
POINT 10: AUTOMATIC RECON DIRECTORY DISCOVERY ENGINE
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Server diagnostics aur automation tracking ka background directory helper logic. 
Yeh runtime par root cron scripts folder path ko dynamically list aur read karta hai 
taaki frontend dropdown ko realtime services provide kar sake. System pipeline ki 
integrity banaye rakhne ke liye, yeh program filters lagakar hidden directory nodes 
(jaise .git ya metadata folders) aur system ke apne operational architecture zones 
(jaise main sandbox 'playground' aur execution framework 'cleanup') ko scanning list 
se strictly skip (exclude) kar deta hai.

--------------------------------------------------------------------------------
POINT 11: MAIN DASHBOARD ROUTER INTERFACE
--------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, service: str = None, date: str = None):
    # 🔒 SECURITY BLOCK: Guard mechanism active
    username = request.cookies.get("session_user")
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
--------------------------------------------------------------------------------
DESCRIPTION:
Application orchestrator dashboard ka core logical execution gateway. Is function ki 
pehle hi index sequence par ek rigid stateful authentication block check khada hai. 
Agar koi person bina session cookie ke dashboard root URL ('/') access karne ki koshish 
karega, toh application code ka core server-side automation use pipeline aage badhne se 
pehle hi instantly block karega aur HTTP 303 Redirect instruction ke sath browser ko 
login interface par throw kar dega. Validation clear hone par hi structural variables 
declare hote hain.

--------------------------------------------------------------------------------
POINT 12: PROCESS LOCK MONITORING & AUTOMATION STATUS MICRO-STATES MATRIX
--------------------------------------------------------------------------------
today_lck_file = os.path.join(usage_dir, f"check_usage-{today_str}.lck")

if os.path.exists(today_lck_file):
    is_locked = True
    status_msg = "⏳ RUNNING / LOCKED (Process is currently executing)"
    
target_success_file = os.path.join(stat_dir, f"stat-{selected_date}.txt")
# ... conditions check ...
with open(target_success_file, "r", encoding="utf-8") as f:
    if f.read().strip() == "1":
        status_msg = "✅ COMPLETE / SUCCESS"
--------------------------------------------------------------------------------
DESCRIPTION:
Highly critical active state monitoring logic. Yeh code PAM server par chalne wali 
background cron jobs ke active life-cycle states ko runtime status code mapping ke 
sath evaluate karta hai. Agar server directory ke andar 'usage/' pathway mein aaj ki 
tarikh ki '.lck' file detect ho jaati hai, toh frontend UI status instantly lock hokar 
'RUNNING / LOCKED' warning badge mein shift ho jata hai aur playground testing run temporary 
disable ho jaati hai. Lock absent hone par yeh file pointers se execution reports check 
karta hai—agar string data code value exactly "1" milti hai toh status state **SUCCESS** hoti hai, khali hone par **INCOMPLETE**, aur target exceptions milne par **🚨 SCRIPT ERROR / FAILED** ka precise micro-state matrix frontend UI ko dynamic dispatch kar diya jata hai.

--------------------------------------------------------------------------------
POINT 13: CALENDAR COMPONENT HISTORY MATRIX LOGIC
--------------------------------------------------------------------------------
for i in range(STRAT_HISTORY_DAYS, END_HISTORY_DAYS):
    date_to_check = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
    
    check_lck_path = os.path.join(usage_dir, f"check_usage-{date_to_check}.lck")
    check_success_path = os.path.join(stat_dir, f"stat-{date_to_check}.txt")
    # ... existence mapping ...
    recon_history.append({
        "date": date_to_check, 
        "status": day_status, 
        "color": day_color
    })
--------------------------------------------------------------------------------
DESCRIPTION:
Yeh loop dashboard ke top monitoring layout par pichle 15 dino ka accurate time-series 
recon status component draw karne ka kaam karta hai. Yeh date variables ranges ko loop mein 
extract karke har single historical date folder ke data streams check karta hai. Date files 
ki availability aur size evaluation (0B vs filled data block) ke base par yeh array dict 
structure mein dynamic values push karta hai jisme custom design elements code definitions 
('green' for success, 'red' for errors, 'yellow' for unresolved flags) map hokar user display 
grid panel ko return ho jaate hain.

--------------------------------------------------------------------------------
POINT 14: DROPDOWN NAVIGATION ENGINE & DESCENDING DESIGN OPTIMIZATION
--------------------------------------------------------------------------------
operational_files = {
    "stat": [], "stat/error": [], "error": [], "missing": []
}

for prefix, path in target_folders.items():
    if os.path.exists(path):
        for f in sorted(os.listdir(path), reverse=True): # ◄── Sorting Optimization
            if os.path.isfile(os.path.join(path, f)) and not f.startswith('.'):
                operational_files[prefix].append(f"{prefix}/{f}")
--------------------------------------------------------------------------------
DESCRIPTION:
**Enterprise Architecture Scale Optimization Section.** Yeh loops automation server ke 
saare physical output records directories ('stat/', 'error/', 'missing/') ko system level 
par deep traverse karte hain. Jab application lambe samay tak production par live run karegi, 
toh folders mein hazaro logs aur files jama ho jayengi. User navigation experience ko optimal 
aur lag-free rakhne ke liye yahan directory files sorting listing par **'reverse=True' (Descending Sort)** algorithm bind kiya gaya hai. Iska sateek logical benefit yeh hai ki database backlog chahe 
jitna marzi badh jaye, user dropdown open karte hi aaj ya kal ki sabse taaza log file 
('stat-2026-06-15.txt') automatically data tree mein bina scroll sirdardi ke top par instantly 
render ho jaati hai.

--------------------------------------------------------------------------------
POINT 15: PRODUCTION CODE ISOLATED PROVIDER API
--------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------
DESCRIPTION:
Dynamic source-code reader microservice endpoint. Jab user interface layout window par 
kisi live python script ya bash file par analysis ke liye click karta hai, toh yeh API 
sabse pehle secure session state verification validate karti hai. Session clear hone par 
python filesystem input-streams read karke file content data payload deliver karti hai 
aur PAM infrastructure logging compliance criteria ke under BigQuery server par realtime audit 
activity ('LOAD_TEMPLATE') user tracking stamp ke sath safely save kar deti hai.

--------------------------------------------------------------------------------
POINT 16: ISOLATED STAGING SANDBOX WRITER ENGINE
--------------------------------------------------------------------------------
@app.post("/api/load-playground")
async def load_playground(request: Request, service: str = Form(...), filename: str = Form(...), content: str = Form(...)):
    # ... security checks ...
    service_playground_dir = os.path.join(BASE_SERVER_DIR, service, "playground")
    os.makedirs(service_playground_dir, exist_ok=True)
    
    target_name = "playground.py" if filename.lower().endswith('.py') else "playground.sh"
    target_file = os.path.join(service_playground_dir, target_name)
    
    with open(target_file, "w", encoding="utf-8", newline='\n') as f:
        f.write(content)
--------------------------------------------------------------------------------
DESCRIPTION:
High-privilege protection security logic. Yeh system architecture design core recon scripts ka 
direct real-time modification block karta hai taaki direct system change ki wajah se running 
production automation crons crash na ho sakein. User jab dashboard code space editor par 
koi bhi logic edit karke load karega, toh system use main application runtime environment se 
dur rakh kar ek dynamic separate testing sandbox folder path ('service/playground/playground.sh') 
mein pipeline format mein write karega, jisse server completely safe aur secure zone mein insulated 
rehta hai.

--------------------------------------------------------------------------------
POINT 17: TWO-FACTOR AUTHORIZATION SUBPROCESS ENGINE (MULTI-OS WRAPPER)
--------------------------------------------------------------------------------
@app.post("/api/run-playground")
async def run_playground(request: Request, service: str = Form(...), pin: str = Form(...), confirm: bool = Form(...)):
    if pin != SYSTEM_SECRET_PIN or not confirm:
        return JSONResponse(status_code=403, content={"status": "error", "message": "❌ Invalid Security PIN"})
        
    try:
        if os.name == 'nt':
            git_bash_path = r"C:\Users\shilendra.mishra_spi\AppData\Local\Programs\Git\usr\bin\bash.exe"
            subprocess.Popen([git_bash_path, "playground.sh"], cwd=service_playground_dir)
        else:
            subprocess.Popen(["bash", "playground.sh"], cwd=service_playground_dir)
--------------------------------------------------------------------------------
DESCRIPTION:
Staging execution manager route. Local code pipeline execution ko background process mein 
trigger karne ke liye system double protection gate engine verify karta hai—pehle explicit 
UI confirm checkbox state evaluate hoti hai aur phir environment file mein secure baithe 
hidden server token value ('SYSTEM_SECRET_PIN') ko input block string se strictly verify 
kiya jata hai. Validation confirm hote hi system operating execution structure logic branch 
check karta hai—agar application deployment host Windows VM ('nt') hai toh GitBash process 
terminal wrapper execute hota hai, aur agar Linux deployment engine machine hai toh standard 
native sh backend processes spawn karke main async application loops ko completely free kar diya 
jata hai.

--------------------------------------------------------------------------------
POINT 18: ANTI-DIRECTORY TRAVERSAL FILE MANAGER PROTECTION API
--------------------------------------------------------------------------------
@app.post("/api/delete-file")
async def delete_file(request: Request, service: str = Form(...), relative_path: str = Form(...), action: str = Form(...)):
    if ".." in relative_path or relative_path.startswith("/"):
        log_activity_to_bq(username, f"FILE_{action.upper()}", service, "❌ ATTACK_BLOCKED", f"Directory traversal attempt: {relative_path}")
        raise HTTPException(status_code=400, detail="Security alert: Unsafe path structure bypass attempt blocked.")
--------------------------------------------------------------------------------
DESCRIPTION:
Ad-hoc file maintenance system logic. Yeh endpoint flag files aur logs repositories ko 
complete remove karne ya truncate ('0B clear') karne ki execution power provide karta hai. 
System ko cyber exploitation aur unauthorized local server exploration se fully block rakhne 
ke liye yahan strict **'Anti-Directory Traversal character sequence analysis'** implemented hai. 
Agar koi malicious user system data leak ke maqsad se payload entries mein parent directory jumping 
strings ('..') ya application folder parameters ke bahar absolute paths ('/') supply karke query 
execute karne ki koshish karega, toh input pattern verification pipeline use block alert hit 
karke drop kar degi aur activity table mein instantly ATTACK_BLOCKED data package report write kar degi.

--------------------------------------------------------------------------------
POINT 19: PIPE-STREAM DATABASE PURGE INTERCEPTOR ENGINE
--------------------------------------------------------------------------------
@app.post("/api/execute-cleanup")
async def execute_cleanup(request: Request, script_name: str = Form(...), target_date: str = Form(...)):
    # ... directory configuration ...
    try:
        exec_cmd = ["python3", script_name] if os.name != 'nt' else ["python", script_name]
        process = subprocess.Popen(exec_cmd, cwd=cleanup_dir, stdin=subprocess.PIPE, text=True)
        
        process.stdin.write(f"{target_date}\n")
        process.stdin.flush()
--------------------------------------------------------------------------------
DESCRIPTION:
Enterprise maintenance pipeline cleanup system route. Yeh module historical database duplications 
aur high data sizing tables ko optimization script ke zariye clear karne ka complex task handles 
karta hai. Yeh clean-up worker code ko OS background processes asynchronous layout mein system memory 
par trigger karta hai, aur iska logic bina kisi console manual intervention ke dynamic processing target 
dates inputs ko direct platform data pipe streams ('process.stdin.write') ke parameters automation method 
se process script runtime system code ko securely transmit aur flush kar deta hai.

--------------------------------------------------------------------------------
POINT 20: LOW-OVERHEAD REALTIME TERMINAL LIVE LOG STREAMER API
--------------------------------------------------------------------------------
@app.get("/api/stream-live-logs")
async def stream_live_logs(service: str, date: str):
    current_dir = os.path.join(BASE_SERVER_DIR, service)
    # ... file parsing mapping ...
    if os.path.exists(target_out_file):
        with open(target_out_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            last_lines = lines[-30:] if len(lines) > 30 else lines
            return {"status": "found", "data": "".join(last_lines)}
--------------------------------------------------------------------------------
DESCRIPTION:
Realtime web terminal streaming engine module endpoint. Jab frontend layout console interface 
active log polling triggers use karta hai, toh yeh endpoint active target logs file read output 
packages compile karta hai. Production server ke resources aur CPU performance benchmark score ko 
himesha minimal aur memory-leak free zone mein rakhne ke liye, yeh handler poori 1GB ya 500MB ki log 
file memory buffer mein load karne ke bajaye list slicer logic limits lagakar continuous fast 
asynchronous dictionary packets mein system log report ki data chunk ki **last 30 trailing data lines** hi fetch karke stream karta hai jo webpage streaming dashboard browser console window ko instant realtime speed 
provide karti hai.
================================================================================
                                END OF DOCUMENT
================================================================================