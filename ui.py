import streamlit as st

SAMPLE_JOB_DESCRIPTION = """Senior Full-Stack AI Engineer
Key Requirements:
- 4+ years of professional experience with Python, FastAPI, and modern JavaScript/TypeScript (React, Next.js).
- Proven hands-on experience designing and building RAG (Retrieval-Augmented Generation) architectures with vector databases (ChromaDB, Pinecone, Qdrant).
- Strong expertise deploying and orchestrating Large Language Models (Groq, OpenAI, Anthropic, HuggingFace).
- Experience with Docker, CI/CD pipelines, and cloud platforms (AWS / GCP / Azure).
- Solid grasp of unit testing, system architecture, and REST/gRPC API design.
- Strong problem-solving, communication, and cross-functional team skills."""

def apply_custom_css():
    """Injects modern, polished light-theme styling and custom fonts."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .stApp {
            background-color: #f8fafc;
            color: #0f172a;
        }

        /* Hero Banner */
        .hero-container {
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04);
        }
        .hero-title {
            color: #0f172a;
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0 0 6px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .hero-subtitle {
            color: #64748b;
            font-size: 14px;
            font-weight: 400;
            margin: 0;
            line-height: 1.5;
        }
        .section-title {
            font-size: 15px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Metric Boxes */
        .metric-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 14px 16px;
            text-align: center;
            box-shadow: 0 2px 6px -1px rgba(0, 0, 0, 0.02);
        }
        .metric-value {
            font-size: 20px;
            font-weight: 800;
            color: #2563eb;
        }
        .metric-label {
            font-size: 11px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Primary Action Button */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
            transition: all 0.2s ease;
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
            transform: translateY(-1px);
            color: white;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
    </style>
    """, unsafe_allow_html=True)

def render_hero_header():
    """Renders top header banner with badges and description."""
    st.markdown("""
    <div class="hero-container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
            <div>
                <div class="hero-title">
                    <span>📄 AI Resume & Job Fit Evaluator</span>
                </div>
                <p class="hero-subtitle">
                    Compare your CV with a job description locally and get clear gaps and improvement tips.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renders non-input navigation controls."""
    with st.sidebar:
        st.markdown("### 🔒 Privacy")
        st.caption("Your CV is analyzed with Groq using the key configured by the app owner.")
        st.markdown("---")
        st.markdown("### 🛠️ Analysis")
        st.markdown("""
        - **Requirement matching**: Local text analysis
        - **PDF Engine**: `pdfplumber`
        """)

        st.markdown("---")
        if st.button("🔄 Reset / Clear Session", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
def render_inputs():
    """Renders the two-column inputs and evaluation trigger button."""
    if "job_description_input" not in st.session_state:
        st.session_state.job_description_input = ""

    def load_sample_job_description():
        st.session_state.job_description_input = SAMPLE_JOB_DESCRIPTION

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-title"><span>📑 1. Upload Resume / CV (PDF)</span></div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload PDF Resume",
            type=["pdf"],
            help="Upload candidate resume in PDF format.",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            file_size_kb = len(uploaded_file.getvalue()) / 1024
            st.caption(f"📁 **{uploaded_file.name}** ({file_size_kb:.1f} KB)")

    with col2:
        st.markdown('<div class="section-title"><span>🎯 2. Target Job Description</span></div>', unsafe_allow_html=True)
        
        st.button(
            "✨ Load Sample Job Description",
            key="sample_jd_btn",
            on_click=load_sample_job_description,
        )
            
        job_description = st.text_area(
            "Paste the Job Description",
            key="job_description_input",
            height=160,
            placeholder="Paste target job responsibilities, skills, and qualifications here...",
            label_visibility="collapsed"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    evaluate_btn = st.button("⚡ Evaluate Candidate Match", type="primary", use_container_width=True)
    
    return uploaded_file, job_description, evaluate_btn

def render_results(evaluation_text: str, retrieved_docs: list, stats: dict):
    """Renders the evaluation report, metrics, and context inspection tabs."""
    st.markdown("---")
    st.subheader("📊 Candidate Compatibility Report")
    
    # Metrics Row
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{stats.get('pages', 1)}</div>
            <div class="metric-label">Resume Pages</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{stats.get('chunks', 0)}</div>
            <div class="metric-label">Semantic Chunks</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{stats.get('retrieved', 0)}</div>
            <div class="metric-label">Matches Retrieved</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="font-size: 14px; padding-top: 5px;">🔒 Local</div>
            <div class="metric-label">{stats.get('model', 'GPT OSS 20B')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📑 Detailed Assessment", "🔍 Retrieved Resume Context"])
    
    with tab1:
        st.markdown(evaluation_text)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Full Assessment (.md)",
            data=evaluation_text,
            file_name="resume_evaluation_report.md",
            mime="text/markdown",
            use_container_width=True
        )
        
    with tab2:
        st.markdown("#### 📌 Top Matching Resume Excerpts")
        st.caption("The vector database retrieved these specific sections from the candidate's CV as most relevant to the JD:")
        
        for idx, doc in enumerate(retrieved_docs, start=1):
            with st.expander(f"Snippet #{idx}", expanded=(idx == 1)):
                st.markdown(f"```text\n{doc}\n```")
