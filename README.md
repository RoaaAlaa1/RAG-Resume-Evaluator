# 📄 AI Resume & CV Evaluator (RAG-Powered)

An interactive, AI-powered Streamlit web application that benchmarks a candidate's resume against a targeted job description using **Retrieval-Augmented Generation (RAG)**. The application extracts content from PDF resumes, generates vector embeddings using Google GenAI, stores them transiently in ChromaDB, and delivers an HR assessment using Google Gemini or Groq (Llama 3 70B).

## 🌟 Key Features

* **PDF Parsing**: Automatically extracts and normalizes textual content from multi-page PDF resumes using `pdfplumber`.

* **RAG Retrieval Engine**: Chunks the resume text, generates vector embeddings, and stores them in an ephemeral vector database (`ChromaDB`).

* **Semantic Job Matching**: Uses the job description to run similarity search queries against resume chunks, isolating the most relevant qualifications.

* **Dual-Model Routing (Gemini & Groq)**:

  * Default evaluator: **Google Gemini (`gemini-2.0-flash` / `gemini-2.5-flash`)**.

  * Rate-limit fallback: **Groq (`llama3-70b-8192`)** for ultra-fast, high-throughput inference.

* **Actionable Feedback**: Delivers an evaluation covering Match Verdict, Skills Met, Missing Requirements, and tailored Resume Optimization Advice.

## 🏗️ System Architecture

```
[ User Uploads PDF ] ──> [ pdfplumber: Text Extraction ]
                                   │
                                   ▼
                         [ Text Chunking ]
                                   │
                                   ▼
             [ Google GenAI (gemini-embedding-2): Embed Chunks ]
                                   │
                                   ▼
                   [ ChromaDB Ephemeral Client ]
                                   ▲
                                   │ (Semantic Similarity Query)
[ Job Description Input ] ──> [ Embed Query ]
                                   │
                                   ▼
                   [ Top-K Relevant Resume Snippets ]
                                   │
                                   ▼
                    [ Synthesis & Assessment Prompt ]
                                   │
           ┌───────────────────────┴───────────────────────┐
           ▼                                               ▼
 [ Google Gemini API ]                           [ Groq API (Fallback) ]
 (`gemini-2.0-flash`)                             (`llama3-70b-8192`)
           │                                               │
           └───────────────────────┬───────────────────────┘
                                   ▼
                   [ Streamlit Evaluation Report ]

```

## 📋 Prerequisites

* **Python**: Version 3.10 to 3.12 recommended.

* **API Keys**:

  * [Google AI Studio API Key](https://aistudio.google.com/) (Required for Gemini embeddings and default LLM generation).

  * [Groq Cloud API Key](https://console.groq.com/) (Optional, required if switching to Groq fallback).

## 🛠️ Installation & Setup

### 1. Clone or Download the Repository

```
git clone <your-repository-url>
cd resume-evaluator

```

### 2. Create and Activate a Virtual Environment

```
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt / PowerShell)
python -m venv venv
.\venv\Scripts\activate

```

### 3. Install Dependencies

Create a `requirements.txt` file (or use the one below) and install the packages:

```
pip install -r requirements.txt

```

#### `requirements.txt`

```
streamlit
pdfplumber
chromadb
pysqlite3-binary
google-genai
groq

```

> **Note for Streamlit Cloud / Linux Deployments**:
> ChromaDB requires SQLite >= 3.35.0. The script includes a monkey-patch using `pysqlite3`:
>
> ```
> __import__('pysqlite3')
> import sys
> sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
> 
> ```
>
> Ensure `pysqlite3-binary` is listed in your `requirements.txt` when deploying to Linux-based cloud hosts.

## 🚀 Running the Application

Launch the Streamlit app locally with:

```
streamlit run app.py

```

The app will open in your default browser at `http://localhost:8501`.

## 📖 How to Use

1. **Enter API Credentials**:

   * Provide your **Google Gemini API Key** in the input field.

   * If you wish to use Groq for evaluation, flip the toggle switch and provide your **Groq API Key**.

2. **Upload Resume**: Upload your CV or resume in `.pdf` format in column 1.

3. **Paste Job Description**: Paste the target job posting into the text area in column 2.

4. **Run Evaluation**: Click **"Evaluate My CV/Resume"**.

5. **Review Report**: The app generates:

   * **Overall Verdict**: Strong, partial, or weak match.

   * **Skills Met**: Explicitly matched competencies.

   * **Missing Skills**: Crucial qualifications not discovered in the resume.

   * **Advice**: Targeted guidance to optimize the resume for the role.

## 🔍 Code Inspection & Identified Bugs

Reviewing the provided source script reveals a few bugs and optimization opportunities to address:

### 1. Unreachable Code / Execution Leak

* **Issue**: In the Gemini generation branch, `response = client.models.generate_content(...)` is called **after** the `if/else` block outside the loop indentation, causing Gemini to run twice or overwrite Groq's output.

* **Fix**: Remove the dangling redundant call at the bottom of the try-block.

### 2. Duplicate Imports

* **Issue**: `import streamlit as st` and `import pdfplumber` are imported twice at the head of the file.

* **Fix**: Consolidate imports into a single top-level block.

### 3. Non-Breaking Hardcoded Delays

* **Issue**: A hardcoded `time.sleep(10)` runs unconditionally on every execution, increasing latency for normal users.

* **Fix**: Rely on adaptive backoff (exponential backoff) during `429` responses rather than unconditional delays before calling the generation model.

### 4. Non-Standard In-Line Spaces

* **Issue**: Code copied from rich-text editors often contains non-breaking spaces (`\u00a0`), causing Python `SyntaxError: invalid character in identifier`.

* **Fix**: Run code formatters like `black` or `ruff` to sanitize whitespace.

## 🧰 Troubleshooting

| **Issue** | **Cause** | **Resolution** | 
| `pysqlite3` import error | `pysqlite3-binary` is missing on Windows/macOS | Install via `pip install pysqlite3-binary`. On systems where SQLite is already modern, the patch can be wrapped in a `try...except ImportError`. | 
| `RESOURCE_EXHAUSTED` (429) | Gemini Free tier rate limits exceeded (RPM/TPM) | Enable the Groq toggle to route text generation through Groq's high-speed inference engine. | 
| `Empty Document / 0 Chunks` | Scanned or image-only PDF uploaded | Use searchable PDFs containing text layers. `pdfplumber` does not perform OCR on raw scanned images. | 

## 🔒 Security Best Practices

* **Never hardcode API keys** directly in the script.

* For local production setups, use Streamlit secrets management by defining keys in `.streamlit/secrets.toml`:

  ```
  GEMINI_API_KEY = "your-key-here"
  GROQ_API_KEY = "your-key-here"
  
  ```

* Access them safely inside the app via `st.secrets["GEMINI_API_KEY"]`.
