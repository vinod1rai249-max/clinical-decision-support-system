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
    /* Main Background and Font */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Premium Header */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Section Cards */
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* Text inside main cards */
    .card p, .card li, .card b, .card span, .card div {
        color: #1f2937 !important;
    }
    
    .card-header {
        font-weight: 700;
        font-size: 1.25rem;
        color: #1e3a8a !important;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Metrics and Status */
    .metric-box {
        background-color: #eff6ff;
        padding: 1rem;
        border-radius: 6px;
        text-align: center;
        border: 1px solid #bfdbfe;
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-active { background-color: #dcfce7; color: #166534; }
    
    /* --- SIDEBAR OVERHAUL --- */
    [data-testid="stSidebar"] {
        background-color: #1e3a8a !important;
        padding-top: 2rem;
    }
    
    /* Sidebar Text (Headers and Body) */
    [data-testid="stSidebar"] .stMarkdown h3, 
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #ffffff !important;
    }
    
    /* Sidebar Labels */
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar Input Fields (Readability) */
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stNumberInput input,
    [data-testid="stSidebar"] .stTextArea textarea {
        background-color: #ffffff !important;
        color: #1e3a8a !important;
        border-radius: 4px;
    }
    
    /* Known History Text Area - Specifically targeting disabled/readonly contrast */
    [data-testid="stSidebar"] .stTextArea textarea:disabled {
        background-color: #f1f5f9 !important;
        color: #1e3a8a !important;
        opacity: 1 !important; /* Ensure it doesn't dim */
        -webkit-text-fill-color: #1e3a8a !important; /* Safari fix */
    }
    
    /* Expander in Sidebar */
    [data-testid="stSidebar"] .stExpander {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
    }
    [data-testid="stSidebar"] .stExpander details summary {
        color: white !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Hide Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
if "API_BASE" in st.secrets:
    API_BASE = st.secrets["API_BASE"]
    API_KEY = st.secrets["CDSS_API_KEY"]
else:
    API_BASE = os.environ.get("API_BASE", "http://localhost:8080/api")
    API_KEY = os.environ.get("CDSS_API_KEY", "dev_default_key_123")

# URL Normalization: Ensure it ends with /api for consistency
if API_BASE.endswith("/"):
    API_BASE = API_BASE[:-1]
if not API_BASE.endswith("/api"):
    API_BASE = f"{API_BASE}/api"

HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def on_patient_change():
    # Clear session state to ensure a fresh page on patient change
    for key in ['summary', 'research', 'recommendation']:
        if key in st.session_state:
            del st.session_state[key]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏥 Patient Registry")
    selected_patient_key = st.selectbox(
        "Select Active Patient", 
        list(MOCK_PATIENTS.keys()),
        on_change=on_patient_change
    )
    
    patient_data = MOCK_PATIENTS[selected_patient_key]
    
    st.markdown("---")
    st.markdown("### 📋 Patient Details")
    st.text_input("ID", patient_data["id"], disabled=True)
    st.number_input("Age", 0, 120, patient_data["age"])
    # Known History with improved contrast
    st.text_area("Known History", patient_data["history"], disabled=True, height=100)
    
    st.markdown("---")
    with st.expander("🛠️ Connection Diagnostic"):
        if st.button("Test Backend Connection"):
            try:
                # 1. Test Health Check (No Auth)
                health_url = API_BASE.replace("/api", "/health_check")
                h_res = requests.get(health_url, timeout=5)
                if h_res.status_code == 200:
                    st.success("✅ Backend is Online")
                else:
                    st.error(f"❌ Backend unreachable ({h_res.status_code})")
                
                # 2. Test Auth
                st.write(f"Testing Auth with: `{API_KEY[:4]}***`")
                auth_res = requests.post(f"{API_BASE}/summarize", 
                                        json={"report_text": "ping"}, 
                                        headers=HEADERS, timeout=5)
                if auth_res.status_code == 200:
                    st.success("✅ API Key is Valid")
                elif auth_res.status_code == 403:
                    st.error("❌ 403: API Key Mismatch. Check your Secrets.")
                else:
                    st.warning(f"⚠️ Unexpected Status: {auth_res.status_code}")
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")

    st.markdown("---")
    with st.expander("📖 Clinical Input Guide"):
        st.markdown("""
            **How to use:**
            Include these details for best results:
            - **Symptom:** e.g., 'Chest pain'
            - **Vitals:** e.g., 'Fever 102F'
            - **Clues:** e.g., 'High glucose'
            
            **✅ Good Example:**
            "Cough and fever for 3 days. X-ray shows infiltrate."
            
            **Supported categories:**
            Respiratory, Cardiac, Diabetes, Neuro, Renal, GI, OB/GYN, Mental Health, Ortho, Derm.
        """)
    
    st.markdown("---")
    st.markdown(f"""
        <div class='metric-box' style='background-color: white;'>
            <div style='font-size: 0.8rem; color: #1e3a8a; opacity: 0.8;'>Active Session</div>
            <div style='font-weight: 700; font-size: 1.1rem; color: #1e3a8a;'>{patient_data['id']}</div>
            <div class='status-badge status-active'>Secure Connection</div>
        </div>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f"""
    <div class="main-header">
        <h1>Clinical Decision Support System (CDSS)</h1>
        <p style="opacity: 0.9; margin-bottom: 0;">Multi-Agent AI for Evidence-Based Clinical Guidance</p>
    </div>
""", unsafe_allow_html=True)

# --- MAIN INTERFACE ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    # 1. Diagnostic Input
    st.markdown("""
        <div class="card">
            <div class="card-header">🔍 1. Diagnostic Input</div>
        </div>
    """, unsafe_allow_html=True)
    
    report_text = st.text_area("Patient Lab/Imaging Report:", height=200, 
                               placeholder="e.g., Fever 102F, Cough, WBC 12.5. X-RAY: Right Lower Lobe Infiltrate.",
                               label_visibility="collapsed")
    
    if st.button("Analyze & Summarize Report"):
        with st.spinner("Processing medical data..."):
            try:
                response = requests.post(f"{API_BASE}/summarize", json={"report_text": report_text}, headers=HEADERS)
                if response.status_code == 200:
                    st.session_state['summary'] = response.json()
                    st.success("Analysis Complete")
                else:
                    st.error(f"Failed to process report: {response.status_code}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

    # 2. Analysis Results
    if 'summary' in st.session_state:
        summary = st.session_state['summary']
        st.markdown(f"""
            <div class="card">
                <div class="card-header">📊 2. Clinical Summary</div>
                <div style="margin-bottom: 1rem;">
                    <span style="font-size: 0.9rem;">Primary Concern:</span><br/>
                    <b style="font-size: 1.1rem; color: #dc2626 !important;">{summary.get('primary_concern', 'N/A')}</b>
                </div>
                <div style="margin-bottom: 1rem;">
                    <span style="font-size: 0.9rem;">Key Findings:</span>
                    <ul style="margin-top: 0.5rem;">
                        {''.join(f'<li>{item}</li>' for item in summary.get('key_findings', []))}
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)

with col_right:
    # 3. Evidence-Based Research
    if 'summary' in st.session_state:
        st.markdown("""
            <div class="card">
                <div class="card-header">📚 3. Evidence Research (CRAG)</div>
            </div>
        """, unsafe_allow_html=True)
        
        query = st.session_state['summary'].get('primary_concern', '')
        st.info(f"Researching: **{query}**")
        
        if st.button("Fetch Clinical Evidence"):
            with st.spinner("Querying PubMed & Verifying Evidence..."):
                try:
                    res_response = requests.post(f"{API_BASE}/research", json={"query": query}, headers=HEADERS)
                    if res_response.status_code == 200:
                        st.session_state['research'] = res_response.json()['research']
                        st.success("Evidence Retrieved")
                    else:
                        st.error(f"Error fetching research: {res_response.status_code}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

        if 'research' in st.session_state:
            with st.expander("📄 View Grounding Evidence", expanded=True):
                st.markdown(st.session_state['research'], unsafe_allow_html=True)

# --- FINAL RECOMMENDATION ---
if 'research' in st.session_state:
    st.markdown("---")
    st.markdown("""
        <div class="card">
            <div class="card-header">💡 4. Synthesis & Clinical Guidance</div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Generate Final Recommendation"):
        with st.spinner("Synthesizing research and clinical context..."):
            try:
                rec_response = requests.post(f"{API_BASE}/recommend", 
                                             json={"summary": st.session_state['summary'], 
                                                   "research": st.session_state['research']}, headers=HEADERS)
                if rec_response.status_code == 200:
                    rec = rec_response.json()
                    st.session_state['recommendation'] = rec
                    st.success("Guidance Generated")
                else:
                    st.error(f"Error generating guidance: {rec_response.status_code}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

    if 'recommendation' in st.session_state:
        rec = st.session_state['recommendation']
        
        r_col1, r_col2 = st.columns([1, 2])
        
        with r_col1:
            confidence_pct = int(rec['confidence'] * 100)
            st.markdown(f"""
                <div class="metric-box">
                    <div style="color: #1e3a8a; font-size: 0.9rem;">System Confidence</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: {'#16a34a' if confidence_pct > 80 else '#ea580c'};">{confidence_pct}%</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; color: #1e3a8a;">Adherence: <b>{rec['guideline_adherence']}</b></div>
                </div>
            """, unsafe_allow_html=True)
            
        with r_col2:
            st.markdown(f"""
                <div style="background-color: #f0fdf4; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #16a34a;">
                    <h4 style="margin-top: 0; color: #166534;">Recommended Action</h4>
                    <p style="font-size: 1.1rem; color: #14532d;">{rec['recommendation']}</p>
                </div>
            """, unsafe_allow_html=True)
            
        with st.expander("🔍 Clinical Rationale & Basis", expanded=True):
            st.markdown(f"""
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <div style="font-weight: 700; color: #1e3a8a; margin-bottom: 0.5rem;">Basis of Recommendation:</div>
                    <div style="color: #334155; line-height: 1.5; font-size: 0.95rem;">
                        {rec.get('clinical_basis', 'Rationale for this specific case is based on synthesized agent analysis.')}
                    </div>
                    <hr style="margin: 0.8rem 0; border: 0; border-top: 1px solid #cbd5e1;"/>
                    <div style="font-weight: 700; color: #1e3a8a; margin-bottom: 0.5rem;">Evidence Grounding:</div>
                    <div style="color: #334155; font-size: 0.9rem;">
                        {rec.get('evidence_summary', 'Detailed evidence summary not available.')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
