# 🚨 AI Incident Reporter

Turn messy plain-language complaints into structured, prioritized incident reports — with auto-generated escalation emails.

Built solo for **Caliber 2026 Hackathon** in 6 hours using Azure OpenAI.

## ✨ Features

- **Smart Analysis** — converts free-text complaints into structured reports (What/When/Where/Who/Impact)
- **Severity Classification** — Critical / High / Medium / Low with reasoning
- **Auto-Categorization** — IT, HR, Safety, Civic, Facilities
- **Escalation Routing** — suggests the right role/department
- **AI Email Generation** — drafts a professional escalation email in one click
- **PII Anonymization** — strips names, emails, phones before AI processing (privacy-first)
- **Sample Incidents** — try IT, HR, and Civic examples instantly

## 🛠️ Tech Stack

- **Azure OpenAI** (gpt-4o-mini) — analysis + email generation
- **Streamlit** — UI
- **Python 3.12**

## 🚀 Run Locally

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

Run:

```bash
streamlit run app.py
```

## 💡 Use Cases

- HR grievance portals
- IT helpdesk triage
- Civic complaint systems (citizen grievance apps)
- Hospital incident reporting
- Workplace safety reports

## 🔒 Responsible AI

- Low-temperature structured output (no hallucinated fields)
- Optional PII anonymization before processing
- Transparent severity reasoning shown to user
