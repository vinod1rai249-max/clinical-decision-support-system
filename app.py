import streamlit as st
import requests
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Clinical Decision Support System",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MOCK PATIENT REGISTRY ---
MOCK_PATIENTS = {
    "P-1001: John Doe (Geriatric)": {"age": 78, "history": "Hypertension, T2DM", "id": "P-1001"},
    "P-1002: Jane Smith (Pediatric)": {"age": 8, "history": "Asthma, Nut Allergy", "id": "P-1002"},
    "P-1003: Robert Chen (Cardiac)": {"age": 62, "history": "Post-MI, Stented 2022", "id": "P-1003"},
    "P-1004: Sarah Miller (Obstetric)": {"age": 31, "history": "28 weeks pregnant", "id": "P-1004"},
    "P-1005: David Wilson (Trauma)": {"age": 24, "history": "No significant PMH", "id": "P-1005"},
    "P-1006: Emily Brown (Endocrine)": {"age": 45, "history": "Hypothyroidism", "id": "P-1006"},
    "P-1007: Michael Garcia (Renal)": {"age": 55, "history": "CKD Stage 3", "id": "P-1007"},
    "P-1008: Linda Taylor (Neurologic)": {"age": 82, "history": "Dementia, AFib", "id": "P-1008"},
    "P-1009: James Lee (Infectious)": {"age": 19, "history": "Recent travel to SE Asia", "id": "P-1009"},
    "P-1010: Maria Hernandez (Oncology)": {"age": 52, "history": "Breast Cancer (Remission)", "id": "P-1010"}
}

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
    .main-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }
    .card { background-color: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); margin-bottom: 1.5rem; }
    .card p, .card li, .card b, .card span, .card div { color: #1f2937 !important; }
    .card-header { font-weight: 700; font-size: 1.25rem; color: #1e3a8a !important; margin-bottom: 1rem; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
    .metric-box { background-color: #eff6ff; padding: 1rem; border-radius: 6px; text-align: center; border: 1px solid #bfdbfe; }
    .status-badge { padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; }
    .status-active { background-color: #dcfce7; color: #166534; }
    [data-testid="stSidebar"] { background-color: #1e3a8a !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stTextArea textarea:disabled { background-color: #f1f5f9 !important; color: #1e3a8a !important; opacity: 1 !important; }
    .stButton>button { background-color: #3b82f6; color: white; border-radius: 6px; font-weight: 600; width: 100%; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
if "API_BASE" in st.secrets:
    API_BASE = st.secrets["API_BASE"]
    API_KEY = st.secrets.get("PROD_AUTH_KEY", st.secrets.get("CDSS_API_KEY", "clinical_access_999"))
else:
    API_BASE = os.environ.get("API_BASE", "http://localhost:8080/api")
    API_KEY = os.environ.get("PROD_AUTH_KEY", os.environ.get("CDSS_API_KEY", "clinical_access_999"))

API_BASE = API_BASE.strip().rstrip("/")
if not API_BASE.endswith("/api"): API_BASE = f"{API_BASE}/api"
HEADERS = {"X-API-Key": API_KEY.strip(), "Content-Type": "application/json"}

def display_backend_error(response):
    try:
        error_json = response.json()
        st.error(f"❌ Backend Error: {error_json.get('detail', 'Unknown')}")
        if 'traceback' in error_json:
            with st.expander("🛠️ View Technical Traceback"):
                st.code(error_json['traceback'])
    except:
        st.error(f"❌ Critical Backend Failure (Status {response.status_code})")
        st.write(response.text)

def on_patient_change():
    for key in ['summary', 'research', 'recommendation']:
        if key in st.session_state: del st.session_state[key]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏥 Patient Registry")
    selected_patient_key = st.selectbox("Select Active Patient", list(MOCK_PATIENTS.keys()), on_change=on_patient_change)
    patient_data = MOCK_PATIENTS[selected_patient_key]
    st.markdown("---")
    st.markdown("### 📋 Patient Details")
    st.text_input("ID", patient_data["id"], disabled=True)
    st.number_input("Age", 0, 120, patient_data["age"])
    st.text_area("Known History", patient_data["history"], disabled=True, height=100)
    st.markdown("---")
    with st.expander("🛠️ Connection Diagnostic"):
        if st.button("Test Backend Connection"):
            try:
                health_url = API_BASE.replace("/api", "/health_check")
                h_res = requests.get(health_url, timeout=10)
                if h_res.status_code == 200: st.success("✅ Backend Online")
                else: st.error(f"❌ Unreachable ({h_res.status_code})")
                auth_res = requests.post(f"{API_BASE}/summarize", json={"report_text": "ping"}, headers=HEADERS, timeout=15)
                if auth_res.status_code == 200: st.success("✅ API Key Valid")
                else: display_backend_error(auth_res)
            except Exception as e: st.error(f"❌ Connection Error: {str(e)}")
        if st.button("Clear Cache"):
            st.session_state.clear()
            st.rerun()

# --- HEADER ---
st.markdown(f'<div class="main-header"><h1>Clinical Decision Support System (CDSS)</h1><p>AI for Evidence-Based Clinical Guidance</p></div>', unsafe_allow_html=True)

# --- MAIN INTERFACE ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="card"><div class="card-header">🔍 1. Diagnostic Input</div></div>', unsafe_allow_html=True)
    report_text = st.text_area("Report:", height=200, placeholder="Paste clinical data here...", label_visibility="collapsed")
    
    if st.button("Analyze & Summarize Report"):
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(f"{API_BASE}/summarize", json={"report_text": report_text}, headers=HEADERS)
                if response.status_code == 200:
                    st.session_state['summary'] = response.json()
                    st.success("Analysis Complete")
                else: display_backend_error(response)
            except Exception as e: st.error(f"Error: {e}")

    if 'summary' in st.session_state:
        summary = st.session_state['summary']
        st.markdown(f'<div class="card"><div class="card-header">📊 2. Clinical Summary</div><div><b>Primary Concern:</b> <span style="color:red;">{summary.get("primary_concern")}</span></div><ul>' + 
                    ''.join(f'<li>{i}</li>' for i in summary.get('key_findings', [])) + '</ul></div>', unsafe_allow_html=True)

with col_right:
    if 'summary' in st.session_state:
        st.markdown('<div class="card"><div class="card-header">📚 3. Evidence Research</div></div>', unsafe_allow_html=True)
        query = st.session_state['summary'].get('primary_concern', '')
        if st.button("Fetch Clinical Evidence"):
            with st.spinner("Researching..."):
                try:
                    res = requests.post(f"{API_BASE}/research", json={"query": query}, headers=HEADERS)
                    if res.status_code == 200:
                        st.session_state['research'] = res.json()['research']
                        st.success("Evidence Retrieved")
                    else: display_backend_error(res)
                except Exception as e: st.error(f"Error: {e}")

        if 'research' in st.session_state:
            with st.expander("📄 View Grounding Evidence", expanded=True):
                st.markdown(st.session_state['research'], unsafe_allow_html=True)

if 'research' in st.session_state:
    st.markdown("---")
    st.markdown('<div class="card"><div class="card-header">💡 4. Synthesis & Clinical Guidance</div></div>', unsafe_allow_html=True)
    if st.button("Generate Final Recommendation"):
        with st.spinner("Synthesizing..."):
            try:
                rec_res = requests.post(f"{API_BASE}/recommend", json={"summary": st.session_state['summary'], "research": st.session_state['research']}, headers=HEADERS)
                if rec_res.status_code == 200:
                    st.session_state['recommendation'] = rec_res.json()
                    st.success("Guidance Generated")
                else: display_backend_error(rec_res)
            except Exception as e: st.error(f"Error: {e}")

    if 'recommendation' in st.session_state:
        rec = st.session_state['recommendation']
        st.markdown(f'<div class="metric-box">Confidence: <b>{int(rec["confidence"]*100)}%</b> | Adherence: <b>{rec["guideline_adherence"]}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:#f0fdf4; padding:1rem; border-radius:8px; border-left:5px solid #16a34a; margin-top:1rem;">{rec["recommendation"]}</div>', unsafe_allow_html=True)
        with st.expander("🔍 Clinical Rationale", expanded=True):
            st.write(rec.get('clinical_basis', 'Rationale available in detailed report.'))
