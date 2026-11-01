<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./.github/assets/banner-light.svg">
  <img alt="Klara: contract review that cites its sources, in Arabic and English" src="./.github/assets/banner-light.svg" width="100%">
</picture>

<p align="center">
  <b>Upload a contract in Arabic or English. Klara finds the parties, dates, money terms and risks,<br>and points to the exact passage behind every one of them.</b>
</p>

<p align="center">
  <a href="#see-it-work">See it work</a>
  &nbsp;·&nbsp;
  <a href="#why-this-is-hard">Why this is hard</a>
  &nbsp;·&nbsp;
  <a href="#run-it-locally">Run it locally</a>
</p>

<p align="center">
  <img alt="Built at the AIX Hackathon 2025" src="https://img.shields.io/badge/AIX_Hackathon-2025-1428A0?style=for-the-badge&labelColor=0d1117">
  <img alt="Google Gemini" src="https://img.shields.io/badge/Google-Gemini-8E75FF?style=for-the-badge&logo=googlegemini&logoColor=8E75FF&labelColor=0d1117">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-009688?style=for-the-badge&logo=fastapi&logoColor=009688&labelColor=0d1117">
  <img alt="Next.js 14" src="https://img.shields.io/badge/Next.js-14-ffffff?style=for-the-badge&logo=nextdotjs&logoColor=white&labelColor=0d1117">
  <img alt="Arabic and English" src="https://img.shields.io/badge/Arabic_%2B_English-RTL-10B981?style=for-the-badge&labelColor=0d1117">
</p>

<br>

<a id="see-it-work"></a>

<img alt="A contract's risks in Klara, each linked to the clause and page it came from" src="./.github/assets/hero.png" width="100%">

<br>

## Page 31.

A legal officer in Doha opens a 40-page supply agreement. Half of it is in Arabic. The clause that caps the supplier's liability, or quietly doesn't, is somewhere around page 31.

She has two options. Read all 40 pages. Or paste it into a chatbot that gives a confident summary, with no way to check where any of it came from.

In law, an answer you can't verify is worth nothing. And more than 400 million people speak Arabic, a language most contract tools treat as an afterthought.

**Klara doesn't just summarise. It cites.**

<br>

## Meet Klara

**1. Upload.** A PDF or Word contract, in Arabic or English.

**2. Read.** Klara cleans the text and splits it into numbered passages. A short contract goes to the model whole. For a long one, Klara pulls the passages that matter for 13 legal topics, including payment, warranty, indemnity, liability caps, confidentiality, data protection under GDPR and Gulf PDPL, termination, governing law, force majeure, IP and change of control.

**3. Cite.** One Gemini call turns the numbered passages into parties, dates, money terms, risks and a summary, and every point has to name the passage it came from. Then ask questions in either language, and get answers with their sources attached.

<table>
  <tr>
    <td width="50%" valign="top">
      <img alt="Klara answering a question with citations to the contract" src="./.github/assets/chat.png" width="100%">
      <br><b>Ask, and see the source.</b> Answers come with the page and passage it is based on. Citations to text Klara never retrieved are thrown away.
    </td>
    <td width="50%" valign="top">
      <img alt="The full Klara interface in Arabic, right to left" src="./.github/assets/arabic.png" width="100%">
      <br><b>Arabic is not a translation layer.</b> An Arabic contract, analysed in Arabic, in an interface that flips fully right to left.
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img alt="Contract overview with summary, purpose, scope and risk profile" src="./.github/assets/overview.png" width="100%">
      <br><b>The contract on one screen.</b> Summary, purpose, scope and a risk profile, with parties, dates and money terms one tab away.
    </td>
    <td width="50%" valign="top">
      <img alt="Contract list with filters for industry, governing law and status" src="./.github/assets/contracts.png" width="100%">
      <br><b>The whole portfolio at a glance.</b> Filter by industry, governing law and status, with each contract's count of high and critical risks on its card.
    </td>
  </tr>
</table>

<br>

## Why this is hard

**Arabic legal text breaks off-the-shelf pipelines.** Arabic-Indic digits, decorative letter stretching (tatweel) and long signature lines confuse extraction. Klara normalises them before anything else runs, then detects the language and embeds both languages in one shared vector space.

**Language models invent clauses.** So Klara never lets the model answer from memory. It hands the model numbered passages (the whole contract when it is short, the passages retrieved for each topic when it is long) and requires a citation for every claim. In chat, any citation that points outside the supplied passages is dropped before you see it.

<br>

## Under the hood

```mermaid
flowchart LR
    A[Contract<br>PDF or DOCX] --> B[Clean text<br>Arabic normalised]
    B --> C[Passages<br>e5 + FAISS]
    C --> D[Numbered passages<br>whole or by topic]
    D --> E[Gemini<br>one JSON call]
    E --> F[(Cited risks,<br>parties, dates,<br>money, summary)]
    C --> G[Cited chat]
```

<details>
<summary><b>Real output from one run: the six risks Klara found in the sample MSP agreement</b></summary>

<br>

From [`msp-agreement.docx`](./backend/src/data_samples/english/msp-agreement.docx), a 9-page managed service provider (MSP) agreement. Every row comes with a quoted passage from the page shown. Wording varies a little between runs.

| Severity | Risk | Source |
|---|---|---|
| Critical | Overbroad and Uncapped Indemnification by MSP | page 3: *"hold harmless, defend, and fully indemnify Company against any claims..."* |
| High | Unilateral Liability Cap Favoring Company | page 5: *"IN NO EVENT SHALL COMPANY'S AGGREGATE LIABILITY FOR DIRECT DAMAGES..."* |
| High | Restrictive Conflict of Interest / Non-Compete | page 6: *"MSP will not accept work, enter into a contract..."* |
| Medium | Unrealistic 48-Hour Overage Cure Period | page 3: *"MSP shall have forty-eight (48) hours to terminate the overage..."* |
| Medium | Asymmetric Short Cure Period for Termination | page 5: *"Company may terminate this Agreement upon fifteen (15) days written notice..."* |
| Medium | Absence of Service Level Agreement and Narrow Warranty | page 3: *"for a period of ninety (90) days from the date of shipment..."* |

</details>

- **One call, not five.** Extraction, risk review and summary share one grounded prompt, which keeps every section consistent with the same evidence.
- **Scoped to you.** Every query, including cross-contract search, only ever sees the signed-in user's contracts. JWT auth on every contract and chat endpoint.
- **15 API endpoints, 8 tables, 6 screens,** with five sample contracts, each in English and Arabic, in [`backend/src/data_samples`](./backend/src/data_samples).

<br>

## Run it locally

You need Python 3.11 or 3.12, Node 18.17+ and a [Gemini API key](https://aistudio.google.com/apikey).

```bash
# 1. API
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then set GEMINI_API_KEY
python main.py                # http://localhost:8000, docs at /docs

# 2. App, in a second terminal
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                   # http://localhost:3000
```

Sign up, upload one of the sample contracts, and open it. The first upload downloads the embedding model, so give it a minute.

<br>

## What's real, and what's next

- [x] Grounded extraction, risk review and summary, saved and shown in the app
- [x] Chat about a contract with page-level citations, in English and Arabic
- [x] Full right-to-left Arabic interface
- [x] Per-user data isolation and JWT auth
- [ ] OCR for scanned PDFs (today: text-based PDFs and Word files)
- [ ] A persistent vector store (today each contract's index is rebuilt on demand)
- [ ] An accuracy benchmark on the paired English and Arabic sample contracts
- [ ] Clause library and suggested redlines

Klara was built in one weekend at the AIX Hackathon: see the [hackathon-submission](../../tree/hackathon-submission) tag. Since then I grounded chat in real passages, saved the analysis with its citations and connected the chat sidebar. It is a working prototype, not a product, and the list above is honest about the gap.

<br>

## Team

| Name | Role |
|---|---|
| **[Anas Rustom](https://github.com/anasrustom)** | Software engineering, product, Arabic interface |
| **[Mohamed Ali](https://github.com/mohamed-ali-ai)** | AI pipeline: retrieval, analysis, chat |
| **Mahmoud Ali** | AI engineering |
| **Abdulrahman Abushahba** | Product and brand design |

<p align="center">
  <sub>Built at the <b>AIX Hackathon</b>, Doha, October 2025.</sub>
</p>
