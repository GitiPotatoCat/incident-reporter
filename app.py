import os
import json
import re
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------- Azure OpenAI client ----------
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ---------- Prompts ----------
SYSTEM_PROMPT = """You are an expert incident analyst. Convert a user's plain-language complaint
into a structured incident report. Respond ONLY with valid JSON, no markdown, no commentary.

Schema:
{
  "clean_title": "short title, max 12 words",
  "category": "IT | HR | Safety | Civic | Facilities | Other",
  "severity": "Critical | High | Medium | Low",
  "severity_reason": "1 sentence justification",
  "structured_report": {
    "what": "what happened",
    "when": "when it happened (use 'Not specified' if unclear)",
    "where": "location (use 'Not specified' if unclear)",
    "who": "people involved (use 'Not specified' if unclear)",
    "impact": "business/personal impact"
  },
  "suggested_actions": ["action 1", "action 2", "action 3"],
  "escalate_to": "role/department to escalate to"
}"""

EMAIL_PROMPT = """You are a professional communication expert. Generate a clear, professional
escalation email based on the incident report provided. The email should be:
- Concise (under 150 words)
- Action-oriented
- Appropriately urgent based on severity
- Include a clear ask

Respond ONLY with valid JSON in this schema:
{
  "subject": "email subject line",
  "body": "email body with proper greeting and sign-off"
}"""

# ---------- Sample incidents ----------
SAMPLES = {
    "💻 IT": "The wifi keeps dying every 20 mins and my whole team can't work. Third time this week, nobody is responding from IT.",
    "👥 HR": "My manager has been making inappropriate comments about my appearance in team meetings for the past two weeks. I feel uncomfortable but afraid to speak up.",
    "🏛️ Civic": "Huge pothole on MG Road near the bus stop, already saw two bikes skid yesterday. Been there for over a month, no action from municipality.",
}

# ---------- PII Anonymizer ----------
def anonymize(text: str) -> str:
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", text)
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b", "[PHONE]", text)
    text = re.sub(r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?", "[PERSON]", text)
    return text


def analyze_incident(user_text: str) -> dict:
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)


def generate_email(report: dict) -> dict:
    context = f"""
Incident: {report['clean_title']}
Severity: {report['severity']} ({report['severity_reason']})
Category: {report['category']}
Escalate to: {report['escalate_to']}

Details:
- What: {report['structured_report']['what']}
- When: {report['structured_report']['when']}
- Where: {report['structured_report']['where']}
- Who: {report['structured_report']['who']}
- Impact: {report['structured_report']['impact']}

Suggested actions: {', '.join(report['suggested_actions'])}
"""
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": EMAIL_PROMPT},
            {"role": "user", "content": context},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    return json.loads(response.choices[0].message.content)


# ---------- UI ----------
st.set_page_config(page_title="AI Incident Reporter", page_icon="🚨", layout="wide")
st.title("🚨 AI Incident Reporter")
st.caption("Turn messy complaints into structured, prioritized reports — and ready-to-send escalation emails.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Options")
    anonymize_toggle = st.toggle(
        "🔒 Anonymize PII",
        value=False,
        help="Strips names, emails, phone numbers before AI processing.",
    )
    st.caption("Powered by Azure OpenAI")
    st.divider()
    st.markdown("**Built for Caliber 2026**")

# Sample buttons
st.markdown("**Try a sample:**")
cols = st.columns(len(SAMPLES))
for i, (label, text) in enumerate(SAMPLES.items()):
    if cols[i].button(label, use_container_width=True):
        st.session_state["input_text"] = text
        st.session_state.pop("report", None)
        st.session_state.pop("email", None)
        st.rerun()

user_text = st.text_area(
    "Or describe the incident in your own words:",
    value=st.session_state.get("input_text", ""),
    height=150,
    placeholder="e.g. The wifi keeps dying every 20 mins and my whole team can't work...",
)

col_a, col_b = st.columns([1, 5])
with col_a:
    if st.button("Analyze Incident", type="primary", use_container_width=True):
        if not user_text.strip():
            st.warning("Please describe the incident first.")
        else:
            processed = anonymize(user_text) if anonymize_toggle else user_text
            with st.spinner("Analyzing..."):
                try:
                    report = analyze_incident(processed)
                    st.session_state["report"] = report
                    st.session_state["processed_text"] = processed
                    st.session_state.pop("email", None)
                except Exception as e:
                    st.error(f"Error: {e}")

with col_b:
    if st.button("🗑️ Clear"):
        for k in ["report", "email", "input_text", "processed_text"]:
            st.session_state.pop(k, None)
        st.rerun()

# Show anonymized text if toggle was on
if anonymize_toggle and "processed_text" in st.session_state and "report" in st.session_state:
    with st.expander("🔒 View anonymized input sent to AI"):
        st.code(st.session_state["processed_text"])

# ---------- Render report ----------
if "report" in st.session_state:
    r = st.session_state["report"]

    severity_colors = {
        "Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"
    }

    st.divider()
    st.subheader(r["clean_title"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Severity", f"{severity_colors.get(r['severity'], '')} {r['severity']}")
    col2.metric("Category", r["category"])
    col3.metric("Escalate to", r["escalate_to"])

    st.info(f"**Why this severity?** {r['severity_reason']}")

    st.markdown("### 📋 Structured Report")
    sr = r["structured_report"]
    st.markdown(f"**What:** {sr['what']}")
    st.markdown(f"**When:** {sr['when']}")
    st.markdown(f"**Where:** {sr['where']}")
    st.markdown(f"**Who:** {sr['who']}")
    st.markdown(f"**Impact:** {sr['impact']}")

    st.markdown("### ✅ Suggested Actions")
    for action in r["suggested_actions"]:
        st.markdown(f"- {action}")

    # ---------- Escalation Email ----------
    st.divider()
    st.markdown("### 📧 Escalation Email")

    if st.button("✨ Generate Escalation Email", type="secondary"):
        with st.spinner("Drafting email..."):
            try:
                email = generate_email(r)
                st.session_state["email"] = email
            except Exception as e:
                st.error(f"Error: {e}")

    if "email" in st.session_state:
        e = st.session_state["email"]
        st.text_input("To:", value=r["escalate_to"], disabled=True)
        st.text_input("Subject:", value=e["subject"])
        st.text_area("Body:", value=e["body"], height=250)
        st.success("✅ Email draft ready — copy and send from your email client.")