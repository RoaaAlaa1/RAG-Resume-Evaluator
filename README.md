# 📄 AI Resume & Job Fit Evaluator (RAG-Powered)

An interactive, AI-powered Streamlit web application that benchmarks candidate resumes against targeted job descriptions using **Retrieval-Augmented Generation (RAG)**.

The application extracts content from PDF resumes, creates local vector embeddings with ChromaDB (`all-MiniLM-L6-v2`), and generates recruiter assessments using **Groq's ultra-fast LPU™ inference engine** (`llama-3.3-70b-versatile` and `llama-3.1-8b-instant`).

---

## 🌟 Key Features

- **⚡ Ultra-Fast Groq Inference**: Powered by Groq LPU™ running `llama-3.3-70b-versatile` (with optional `llama-3.1-8b-instant` toggle).
- **🧠 Zero-Quota Local Vector Embeddings**: Embeddings are computed locally using ChromaDB's default `all-MiniLM-L6-v2` engine—no external embedding API keys, rate limits, or costs.
- **🎨 Polished Light-Themed UI**: Modern aesthetics built with *Plus Jakarta Sans* typography, soft gradients, clean card containers, and subtle drop shadows.
- **🧱 Modular Architecture**: Clean separation of concerns with a dedicated UI module ([`ui.py`](ui.py)) and backend pipeline ([`app.py`](app.py)).
- **🔒 Seamless Key Management**: No manual API key inputs in the UI. Configure once in [`.env`](.env) or [`app.py`](app.py).
- **✨ 1-Click Sample Testing**: Includes a built-in sample job description loader to test resume matching instantly.
- **📊 Real-Time Feedback & Metrics**: Live multi-step execution tracker (`st.status`), compatibility metrics (pages, chunks, matches), and structured report breakdown.
- **📥 Downloadable Reports**: Export complete evaluation assessments directly as Markdown (`.md`).
- **🔍 Grounded Evidence Inspector**: Inspect exact resume snippets retrieved by the vector database to verify AI conclusions.

---

## 🏗️ System Architecture

```text
[ Candidate Resume (PDF) ] 
            │
            ▼
[ pdfplumber: Text Extraction ]
            │
            ▼
[ Semantic Text Chunking ]
            │
            ▼
[ ChromaDB Local Embeddings (all-MiniLM-L6-v2) ]
            │
            ▼
[ Ephemeral In-Memory Vector Store ]
            ▲
            │ (Semantic Cosine Similarity Query)
[ Target Job Description ]
            │
            ▼
[ Top-K Most Relevant Resume Snippets ]
            │
            ▼
[ Recruiter Synthesis Prompt ]
            │
            ▼
[ Groq LPU™ API (Llama 3.3 70B / 3.1 8B) ]
            │
            ▼
[ Streamlit Light-Themed Report Dashboard ]
```

---

## 📁 Project Structure

```text
├── .env                  # Stores your GROQ_API_KEY (git-ignored)
├── .gitignore            # Protects .env, secrets, and Python caches
├── .streamlit/
│   └── config.toml       # Streamlit light-theme palette settings
├── app.py                # Core application & RAG orchestration logic
├── ui.py                 # UI components, layout, and custom CSS styling
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd "RAG project"
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your Groq API Key
Open [`.env`](.env) and paste your free Groq API key (starts with `gsk_`):

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

> **Get a free Groq key**: Sign up at [console.groq.com](https://console.groq.com/) to get a free API key with generous rate limits and sub-second inference speeds.

---

## 🚀 Running the Application

Launch the Streamlit app with:

```bash
python -m streamlit run app.py
```

The app will open automatically in your browser at:
👉 **`http://localhost:8501`**

---

## 📖 How to Use

1. **Upload Resume**: Drag and drop or browse for a candidate's CV/Resume in PDF format on the left card.
2. **Set Target Job Description**:
   - Paste any target job description into the right text area, or
   - Click **"✨ Load Sample Job Description"** for a quick demonstration.
3. **Select Engine (Sidebar)**:
   - Choose between `llama-3.3-70b-versatile` (deepest reasoning) and `llama-3.1-8b-instant` (fastest response).
   - Adjust the **Top K Context Chunks** slider (default: `4`).
4. **Evaluate**: Click **"⚡ Evaluate Candidate Match"**.
5. **Review Report**:
   - **Metrics Row**: Resume pages, chunks indexed, matched snippets, and LLM engine.
   - **Detailed Assessment**: Overall Match Verdict (Strong, Moderate, Weak), Skills Met, Skill Gaps, Optimization Advice, and Recommended Interview Questions.
   - **Download**: Export the report with **"📥 Download Full Assessment (.md)"**.
   - **Inspect Context**: View the exact resume excerpts retrieved by ChromaDB in the **Retrieved Resume Context** tab.

---

## 🧰 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`⚠️ Groq API Key Required`** | Key is missing or placeholder | Add your API key into `.env` (`GROQ_API_KEY=gsk_...`) and refresh the page. |
| **`'streamlit' is not recognized`** | `streamlit` executable not in system PATH | Use `python -m streamlit run app.py` instead of bare `streamlit run`. |
| **`Failed to extract readable text`** | PDF is an image scan without text | Upload a searchable PDF containing selectable text (OCR is required for flat scans). |
| **SQLite error on Linux/Cloud** | Host SQLite version is older than 3.35 | The built-in `pysqlite3` compatibility patch in `app.py` resolves this automatically on Linux cloud hosts. |

---

## 🔒 Security Best Practices

- Your API key is stored in [`.env`](.env) and automatically ignored by [`.gitignore`](.gitignore) so it won't be leaked to version control.
- Vector database storage is **ephemeral** (`chromadb.EphemeralClient()`), meaning candidate resumes are kept in-memory during the session and wiped on shutdown.

