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
from google import genai
from groq import Groq
import os
import time

# ==========================================
# 1. Groq API Key Configuration
# ==========================================
st.set_page_config(page_title="AI Resume Evaluator", page_icon="📄")
st.title("📄 AI Resume Evaluator ")
st.write("Upload your CV or Resume and paste a Job Description to see if you are a match!")

# Input for Google API Key
api_key = st.text_input("Enter your Google Gemini API Key:", type="password")

# Input for GROQ API Key
use_groq = st.toggle("Use Groq for Evaluation (Fallback for Gemini Quota)")
groq_api_key = ""
if use_groq:
    groq_api_key = st.text_input("Enter your Groq API Key:", type="password")

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
                
                # Step 4: Retrieve relevant CV chunks using the Job Description as a query
                # We embed the JD to find the closest matching skills/experiences in the CV
                jd_embedding = get_embeddings([job_description], client)[0]
                
                results = collection.query(
                    query_embeddings=[jd_embedding],
                    n_results=5 # Retrieve the top 5 most relevant chunks
                )
                
                retrieved_context = "\n\n---\n\n".join(results['documents'][0])

                #cooldown
                st.info("Taking a brief pause to respect API speed limits...")
                time.sleep(10) # Pauses the script for 10 seconds
                
               # Step 5: Generate Final Assessment
                prompt = f"""
                You are an expert technical recruiter and HR evaluator. 
                I will provide you with a Job Description and relevant snippets retrieved from a candidate's resume.
                
                Your task is to analyze if the candidate is qualified for the role.
                
                **Job Description:**
                {job_description}
                
                **Retrieved Resume Context:**
                {retrieved_context}
                
                **Please provide your output in the following format:**
                1. **Overall Verdict:** (Are they a strong, partial, or weak match?)
                2. **Skills Met:** (List the requirements from the JD that are explicitly found in the resume)
                3. **Missing Skills:** (List the crucial requirements from the JD that are NOT found in the resume context)
                4. **Advice:** (One sentence on how they can improve their resume for this specific role)
                """
                
                # --- HYBRID GENERATION ROUTING ---
                if use_groq:
                    if not groq_api_key:
                        st.error("Please enter your Groq API Key to use the fallback.")
                        st.stop()
                        
                    st.info("Using Groq (Llama 3 70B) for evaluation...")
                    groq_client = Groq(api_key=groq_api_key)
                    
                    chat_completion = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-70b-8192", # One of the smartest models on Groq
                    )
                    
                    st.success("Evaluation Complete!")
                    st.markdown("### Evaluation Report (Powered by Groq)")
                    st.markdown(chat_completion.choices[0].message.content)
                    
                else:
                    # Original Gemini Auto-Retry Logic
                    st.info("Using Gemini for evaluation...")
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=prompt
                            )
                            st.success("Evaluation Complete!")
                            st.markdown("### Evaluation Report (Powered by Gemini)")
                            st.markdown(response.text)
                            break 
                            
                        except Exception as e:
                            error_msg = str(e)
                            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                                if attempt < max_retries - 1:
                                    st.warning(f"Google API is catching its breath. Retrying in 10 seconds... (Attempt {attempt + 1}/{max_retries})")
                                    time.sleep(10)
                                else:
                                    st.error("The Gemini API is too busy right now. Flip the toggle above to try Groq!")
                            else:
                                st.error(f"An unexpected error occurred: {e}")
                                break
                                
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                
                # Display Results
                st.success("Evaluation Complete!")
                st.markdown("### Evaluation Report")
                st.markdown(response.text)
                
            except Exception as e:
                status_box.update(label="❌ Evaluation error", state="error")
                st.error(f"Error during evaluation: {str(e)}")

# ==========================================
# 8. Render Results
# ==========================================
if "last_evaluation" in st.session_state and st.session_state.last_evaluation:
    render_results(
        st.session_state.last_evaluation,
        st.session_state.get("last_context", []),
        st.session_state.get("stats", {})
    )
