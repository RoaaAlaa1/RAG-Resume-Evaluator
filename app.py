# ==========================================
# 0. SQLite Compatibility Patch (for Linux/Streamlit Cloud)
# ==========================================
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import os
import time
import pdfplumber
import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv

from ui import (
    apply_custom_css,
    render_hero_header,
    render_setup_banner,
    render_sidebar,
    render_inputs,
    render_results
)

# Load environment variables from .env
load_dotenv()

# ==========================================
# 1. Groq API Key Configuration
# ==========================================
FIXED_GROQ_API_KEY = ""

def resolve_groq_api_key() -> str:
    """Resolves the Groq API key from .env, fixed constant, or Streamlit secrets."""
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key and not env_key.startswith("gsk_your_groq"):
        return env_key
    
    if FIXED_GROQ_API_KEY and not FIXED_GROQ_API_KEY.startswith("gsk_YourFixed"):
        return FIXED_GROQ_API_KEY.strip()
    
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            secret_key = str(st.secrets["GROQ_API_KEY"]).strip()
            if secret_key:
                return secret_key
    except Exception:
        pass
        
    return ""

# ==========================================
# 3. Helper Functions
# ==========================================
def extract_text_from_pdf(file) -> tuple[str, int]:
    """Extracts text from an uploaded PDF file and returns (text, page_count)."""
    text = ""
    page_count = 0
    try:
        with pdfplumber.open(file) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n\n"
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
    return text.strip(), page_count

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Splits the resume text into semantically cohesive, manageable chunks."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += (p + "\n\n")
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Fallback to line splitting if paragraphs are very large
    if len(chunks) <= 1 and len(text) > chunk_size:
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) < chunk_size:
                current_chunk += (line + " ")
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line + " "
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

    return [c for c in chunks if len(c) > 15]

# ==========================================
# 4. UI Layout & Controls (via ui.py)
# ==========================================
api_key = resolve_groq_api_key()
is_key_configured = bool(api_key)

# Render Sidebar & Model Settings
model_choice, top_k_chunks = render_sidebar(is_key_configured)

# Render Hero Banner & Setup Notification
render_hero_header()
if not is_key_configured:
    render_setup_banner()

# Render File Upload & Job Description
uploaded_file, job_description, evaluate_btn = render_inputs()

# ==========================================
# 5. Evaluation Logic
# ==========================================
if evaluate_btn:
    if not api_key:
        st.error("❌ Groq API Key is missing. Please add your key to `.env` (`GROQ_API_KEY=gsk_...`) or `FIXED_GROQ_API_KEY` in `app.py`.")
    elif not uploaded_file:
        st.error("⚠️ Please upload a candidate CV / Resume (PDF).")
    elif not job_description.strip():
        st.error("⚠️ Please provide a Job Description.")
    else:
        with st.status("🔍 Analyzing Resume & Evaluating Compatibility...", expanded=True) as status_box:
            try:
                # Step 1: PDF Extraction
                status_box.update(label="📄 Extracting text from PDF resume...", state="running")
                cv_text, num_pages = extract_text_from_pdf(uploaded_file)
                
                if not cv_text or len(cv_text.strip()) < 40:
                    status_box.update(label="Failed to extract readable text", state="error")
                    st.error("Could not extract readable text from the uploaded PDF. Please ensure the PDF contains selectable text.")
                    st.stop()
                
                # Step 2: Semantic Chunking
                status_box.update(label="✂️ Segmenting resume into semantic chunks...", state="running")
                cv_chunks = chunk_text(cv_text)
                
                if not cv_chunks:
                    cv_chunks = [cv_text]
                
                # Step 3: Vector Indexing with ChromaDB
                status_box.update(label="🧠 Indexing chunks into ChromaDB vector store...", state="running")
                chroma_client = chromadb.EphemeralClient()
                collection_name = f"resume_eval_{int(time.time() * 1000)}"
                
                try:
                    chroma_client.delete_collection(name=collection_name)
                except Exception:
                    pass
                
                collection = chroma_client.create_collection(name=collection_name)
                chunk_ids = [f"chunk_{i}" for i in range(len(cv_chunks))]
                
                # ChromaDB computes embeddings with default all-MiniLM-L6-v2
                collection.add(
                    documents=cv_chunks,
                    ids=chunk_ids
                )
                
                # Step 4: Semantic Query Retrieval
                status_box.update(label="🎯 Retrieving top matching resume sections for the JD...", state="running")
                effective_k = min(top_k_chunks, len(cv_chunks))
                query_results = collection.query(
                    query_texts=[job_description],
                    n_results=effective_k
                )
                
                retrieved_docs = query_results.get('documents', [[]])[0]
                retrieved_context = "\n\n---\n\n".join(retrieved_docs)
                
                # Step 5: Groq LLM Inference
                status_box.update(label=f"⚡ Generating evaluation with Groq ({model_choice})...", state="running")
                groq_client = Groq(api_key=api_key)
                
                system_prompt = (
                    "You are a Senior Technical Recruiter and Hiring Lead. "
                    "Evaluate candidate resumes against job descriptions thoroughly, objectively, and constructively."
                )
                
                user_prompt = f"""
Analyze the candidate's resume snippets retrieved via semantic search against the provided Job Description.

=========================
JOB DESCRIPTION:
=========================
{job_description}

=========================
RELEVANT RESUME CONTEXT (Retrieved from Candidate CV):
=========================
{retrieved_context}

=========================
FULL RESUME PREVIEW:
=========================
{cv_text[:1500]}

=========================
EVALUATION FORMAT:
=========================
Please evaluate the candidate strictly following this structured markdown format:

### 1. Overall Match Verdict
- **Match Level**: [Strong Match (80-100%) | Moderate Match (50-79%) | Weak Match (<50%)]
- **Executive Summary**: 2-3 concise sentences summarizing the candidate's overall qualification and alignment for this role.

### 2. Key Qualifications & Skills Met
- Bullet points listing the specific skills, tools, experience levels, and certifications explicitly found in the resume matching the JD requirements.

### 3. Missing Requirements & Skill Gaps
- Bullet points identifying crucial JD requirements that are missing, weak, or not demonstrated in the resume context.

### 4. Actionable Resume Optimization Advice
- 2-3 concrete tips on how the candidate can tailor or enhance their resume for this specific position.

### 5. Recommended Interview Verification Questions
- 2 targeted technical or behavioral questions to probe borderline or unconfirmed areas during an interview.
"""

                completion = groq_client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2048,
                )
                
                evaluation_text = completion.choices[0].message.content
                status_box.update(label="✅ Evaluation completed successfully!", state="complete", expanded=False)
                
                # Save results to session state
                st.session_state.last_evaluation = evaluation_text
                st.session_state.last_context = retrieved_docs
                st.session_state.stats = {
                    "pages": num_pages,
                    "chunks": len(cv_chunks),
                    "retrieved": len(retrieved_docs),
                    "model": model_choice
                }
                
            except Exception as e:
                status_box.update(label="❌ Evaluation error", state="error")
                st.error(f"Error during evaluation: {str(e)}")

# ==========================================
# 6. Render Results (via ui.py)
# ==========================================
if "last_evaluation" in st.session_state and st.session_state.last_evaluation:
    render_results(
        st.session_state.last_evaluation,
        st.session_state.get("last_context", []),
        st.session_state.get("stats", {})
    )
