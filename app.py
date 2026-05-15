__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import pdfplumber
import streamlit as st
import pdfplumber
import chromadb
from google import genai
import os

# ==========================================
# 1. Configuration & Setup
# ==========================================
st.set_page_config(page_title="AI Resume Evaluator", page_icon="📄")
st.title("📄 AI Resume Evaluator (RAG)")
st.write("Upload your CV and paste a Job Description to see if you are a match!")

# Input for Google API Key
api_key = st.text_input("Enter your Google Gemini API Key:", type="password")

# ==========================================
# 2. Helper Functions
# ==========================================
def extract_text_from_pdf(file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def chunk_text(text, chunk_size=500):
    """Splits the resume text into smaller, manageable chunks."""
    # A simple chunking strategy splitting by double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = p + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Filter out empty chunks
    return [c for c in chunks if len(c) > 10]

def get_embeddings(texts, client):
    """Generates vector embeddings using Gemini."""
    response = client.models.embed_content(
        model='models/text-embedding-004',
        contents=texts
    )
    return [e.values for e in response.embeddings]

# ==========================================
# 3. Main UI & App Logic
# ==========================================
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("1. Upload your Resume (PDF)", type="pdf")

with col2:
    job_description = st.text_area("2. Paste the Job Description here", height=150)

if st.button("Evaluate My Resume"):
    if not api_key:
        st.error("Please enter your Google API Key.")
    elif not uploaded_file:
        st.error("Please upload a resume.")
    elif not job_description:
        st.error("Please paste a job description.")
    else:
        with st.spinner("Analyzing your profile..."):
            try:
                # Initialize Gemini Client
                client = genai.Client(api_key=api_key)
                
                # Step 1: Extract and Chunk CV
                cv_text = extract_text_from_pdf(uploaded_file)
                cv_chunks = chunk_text(cv_text)
                
                # Step 2: Embed CV Chunks
                embeddings = get_embeddings(cv_chunks, client)
                
                # Step 3: Store in Ephemeral (In-Memory) ChromaDB
                chroma_client = chromadb.EphemeralClient()
                collection_name = "resume_chunks"
                
                # Delete collection if it exists from a previous run in the same session
                try:
                    chroma_client.delete_collection(name=collection_name)
                except Exception:
                    pass
                
                collection = chroma_client.create_collection(name=collection_name)
                
                # Prepare IDs for ChromaDB
                ids = [f"chunk_{i}" for i in range(len(cv_chunks))]
                
                # Add data to Vector DB
                collection.add(
                    documents=cv_chunks,
                    embeddings=embeddings,
                    ids=ids
                )
                
                # Step 4: Retrieve relevant CV chunks using the Job Description as a query
                # We embed the JD to find the closest matching skills/experiences in the CV
                jd_embedding = get_embeddings([job_description], client)[0]
                
                results = collection.query(
                    query_embeddings=[jd_embedding],
                    n_results=5 # Retrieve the top 5 most relevant chunks
                )
                
                retrieved_context = "\n\n---\n\n".join(results['documents'][0])
                
                # Step 5: Generate Final Assessment with Gemini
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
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                
                # Display Results
                st.success("Evaluation Complete!")
                st.markdown("### Evaluation Report")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
