# 📄 AI Resume & Job Fit Evaluator (RAG-Powered)

An interactive Streamlit web application that compares a candidate CV with a target job description using local text analysis.

The application extracts selectable text from PDF resumes and uses Groq to produce a report showing what fits, what is missing, and practical CV improvement tips. The Groq key is configured by the app owner and is never requested from users.

---

## 🌟 Key Features

- **⚡ Groq Report Generation**: Groq's `openai/gpt-oss-20b` model turns extracted CV evidence into a structured recruiter report.
- **🎨 Polished Light-Themed UI**: Modern aesthetics built with *Plus Jakarta Sans* typography, soft gradients, clean card containers, and subtle drop shadows.
- **🧱 Modular Architecture**: Clean separation of concerns with a dedicated UI module ([`ui.py`](ui.py)) and backend pipeline ([`app.py`](app.py)).
- **✨ 1-Click Sample Testing**: Includes a built-in sample job description loader to test resume matching instantly.
- **📊 Real-Time Feedback & Metrics**: Live multi-step execution tracker (`st.status`), compatibility metrics (pages, chunks, matches), and structured report breakdown.
- **📥 Downloadable Reports**: Export complete evaluation assessments directly as Markdown (`.md`).
- **🔍 Evidence Inspector**: Inspect CV lines that support the detected matches.

---

## 🏗️ System Architecture

```text
[ Candidate Resume (PDF) ] 
            │
            ▼
[ pdfplumber: Text Extraction ]
            │
            ▼
[ Local Requirement Matching ]
            ▲
            │
[ Target Job Description ]
            │
            ▼
[ Streamlit Light-Themed Report Dashboard ]
```

---

## 📁 Project Structure

```text
├── .env                  # Local GROQ_API_KEY; ignored by git
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

### 4. Configure Groq (app owner only)
For local runs, open the root `.env` file and replace the placeholder value:

```env
GROQ_API_KEY=gsk_your_actual_key_here
```

The key is loaded server-side. Users only upload a CV and provide a job description; they never see or enter the key.

For Streamlit Cloud, open your app's **Settings → Secrets** and add:

```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
```

The deployed app cannot read your local `.env` because `.env` is intentionally ignored by Git.

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
3. **Evaluate**: Click **"⚡ Evaluate Candidate Match"**.
5. **Review Report**:
   - **Detailed Assessment**: Overall Match Verdict (Strong, Moderate, Weak), fitting requirements, missing requirements, and optimization advice.
   - **Download**: Export the report with **"📥 Download Full Assessment (.md)"**.

---

## 🧰 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`'streamlit' is not recognized`** | `streamlit` executable not in system PATH | Use `python -m streamlit run app.py` instead of bare `streamlit run`. |
| **`Failed to extract readable text`** | PDF is an image scan without text | Upload a searchable PDF containing selectable text (OCR is required for flat scans). |

---

## 🔒 Security Best Practices

- Keep `.env` private and never commit it. The CV text is sent to Groq for report generation when the user evaluates a CV.
