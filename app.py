import os
import re
from pathlib import Path

import pdfplumber
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from streamlit.errors import StreamlitSecretNotFoundError

from ui import (
    apply_custom_css,
    render_hero_header,
    render_inputs,
    render_results,
)

DOTENV_PATH = Path(__file__).resolve().with_name(".env")
load_dotenv(dotenv_path=DOTENV_PATH, override=True)


st.set_page_config(page_title="AI Resume Evaluator", page_icon="📄", layout="wide")


def extract_text_from_pdf(file) -> tuple[str, int]:
    """Extract selectable text from an uploaded PDF."""
    text_parts = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts).strip(), len(pdf.pages)
    except Exception as exc:
        st.error(f"Could not read the PDF: {exc}")
        return "", 0


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _requirements(job_description: str) -> list[str]:
    """Extract useful requirement phrases from bullets and sentence fragments."""
    candidates = []
    for line in job_description.splitlines():
        cleaned = re.sub(r"^[\s>*\-•\d.)]+", "", line).strip()
        if cleaned:
            candidates.extend(re.split(r"[.;]", cleaned))

    if not candidates:
        candidates = re.split(r"[.;\n]", job_description)

    requirements = []
    seen = set()
    for candidate in candidates:
        phrase = re.sub(r"\s+", " ", candidate).strip(" ,:")
        if (
            len(phrase) < 3
            or len(phrase.split()) > 18
            or phrase.lower() in {"requirements", "qualifications", "responsibilities", "preferred qualifications"}
        ):
            continue
        key = _normalise(phrase)
        if key not in seen:
            seen.add(key)
            requirements.append(phrase)
    return requirements


def _keywords(text: str) -> list[str]:
    """Return meaningful terms, retaining technical names such as C++ and .NET."""
    stop_words = {
        "with", "and", "the", "for", "from", "that", "this", "have", "your",
        "years", "year", "experience", "strong", "skills", "skill", "ability",
        "work", "working", "using", "knowledge", "understanding", "including",
        "professional", "excellent", "good", "role", "team", "teams",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower())
    return list(dict.fromkeys(word for word in words if word not in stop_words and len(word) > 2))


def build_local_report(cv_text: str, job_description: str) -> tuple[str, list[str], dict]:
    """Build local matching context to ground the Groq-generated report."""
    cv_lower = _normalise(cv_text)
    requirements = _requirements(job_description)
    matched = []
    missing = []

    for requirement in requirements:
        terms = _keywords(requirement)
        meaningful_terms = [term for term in terms if len(term) > 3]
        if cv_lower and (
            _normalise(requirement) in cv_lower
            or (meaningful_terms and sum(term in cv_lower for term in meaningful_terms) >= max(1, len(meaningful_terms) // 2))
        ):
            matched.append(requirement)
        else:
            missing.append(requirement)

    total = len(matched) + len(missing)
    score = round((len(matched) / total) * 100) if total else 0
    if score >= 80:
        level = "Strong Match"
    elif score >= 50:
        level = "Moderate Match"
    else:
        level = "Weak Match"

    context = []
    for line in cv_text.splitlines():
        line = line.strip()
        line_lower = _normalise(line)
        if line and any(
            any(term in line_lower for term in _keywords(requirement))
            for requirement in matched
        ):
            context.append(line)
    context = list(dict.fromkeys(context))[:8]

    tips = [
        f"Add measurable evidence (scope, impact, or results) for: {missing[0]}."
        if missing
        else "Quantify the impact of your strongest achievements with percentages, time saved, or scale.",
        "Mirror the job description's wording for tools and responsibilities that you genuinely have experience with.",
        "Keep the most relevant projects and achievements near the top of the CV so they are easy to verify.",
    ]

    report = f"""### 1. Overall Match Verdict
- **Match Level:** {level} ({score}% of the extracted requirements found)
- **Executive Summary:** The CV shows evidence for {len(matched)} of {total} extracted job requirements. This is a local, text-based comparison; verify borderline requirements manually.

### 2. What Fits
{chr(10).join(f"- {item}" for item in matched) or "- No requirement was clearly demonstrated in the CV text."}

### 3. What Is Missing or Unclear
{chr(10).join(f"- {item}" for item in missing) or "- No major gaps were found by the text comparison."}

### 4. Tips to Improve the CV
{chr(10).join(f"- {tip}" for tip in tips)}
"""
    return report, context, {"score": score, "requirements": len(requirements)}


def generate_groq_report(
    cv_text: str,
    job_description: str,
    local_report: str,
    retrieved_context: list[str],
) -> str:
    """Generate a structured recruiter report using the server-configured Groq key."""
    api_key = os.getenv("GROQ_API_KEY", "").strip().strip("\"'")
    if not api_key:
        try:
            api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip().strip("\"'")
        except StreamlitSecretNotFoundError:
            api_key = ""

    if not api_key or api_key.startswith("gsk_your_"):
        raise RuntimeError(
            "GROQ_API_KEY is not configured. For local runs, add it to the root "
            f".env file ({DOTENV_PATH}). For Streamlit Cloud, add it under "
            "Settings > Secrets as GROQ_API_KEY = \"your_key\"."
        )

    client = Groq(api_key=api_key)
    context = "\n".join(f"- {line}" for line in retrieved_context) or "- No matching CV excerpts were found."
    prompt = f"""Evaluate this candidate CV against the job description. Use only evidence present in the CV.

JOB DESCRIPTION:
{job_description}

CV:
{cv_text[:12000]}

LOCALLY IDENTIFIED MATCHING CV EVIDENCE:
{context}

LOCAL PRE-CHECK:
{local_report}

Return concise Markdown with exactly these sections:
### 1. Overall Match Verdict
Include Strong, Moderate, or Weak Match and a percentage estimate with a 2-3 sentence summary.
### 2. What Fits
List specific job requirements supported by the CV.
### 3. What Is Missing or Unclear
List requirements not demonstrated or only weakly supported. Do not claim a skill is missing if the CV supports it.
### 4. Tips to Improve the CV
Give 3 concrete, honest suggestions, including what evidence or keywords to add.
"""
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a careful technical recruiter. Be evidence-based and constructive.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1800,
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty evaluation.")
    return content


apply_custom_css()
render_hero_header()
uploaded_file, job_description, evaluate_btn = render_inputs()

if evaluate_btn:
    if not uploaded_file:
        st.error("Please upload your CV or resume as a PDF.")
    elif not job_description.strip():
        st.error("Please provide a job description or load the example.")
    else:
        with st.status("Analyzing your CV against the job description...", expanded=True) as status:
            cv_text, page_count = extract_text_from_pdf(uploaded_file)
            if not cv_text or len(cv_text) < 40:
                status.update(label="Could not extract readable text", state="error")
                st.error("This PDF does not contain enough selectable text. Please upload a searchable PDF.")
            else:
                try:
                    status.update(label="Preparing CV evidence...", state="running")
                    local_report, retrieved_context, comparison = build_local_report(
                        cv_text, job_description
                    )
                    status.update(label="Generating report with Groq...", state="running")
                    report = generate_groq_report(
                        cv_text, job_description, local_report, retrieved_context
                    )
                    status.update(label="Report ready", state="complete", expanded=False)
                    render_results(
                        report,
                        retrieved_context,
                        {
                            "pages": page_count,
                            "chunks": comparison["requirements"],
                            "retrieved": len(retrieved_context),
                            "model": "Groq / Llama 3.3 70B",
                        },
                    )
                except Exception as exc:
                    status.update(label="Could not generate report", state="error")
                    st.error(f"Evaluation failed: {exc}")
