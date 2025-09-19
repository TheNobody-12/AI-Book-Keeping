# AI‑Book‑Keeping
Automating extraction and analysis of bank statements, receipts, and invoices using Azure AI Document Intelligence, with a simple Flask dashboard and optional FastAPI API.

## What’s Inside

- Flask dashboard for exploring parsed data: `backend/app.py`
- Azure Document Intelligence batch processors: `backend/doc_intel_quickstart.py`, `backend/batch_processor.py`
- Optional FastAPI programmatic API: `backend/main.py`
- Heuristic categorization + stubs for LLM use: `backend/categorize.py`
- Minimal frontend template served by Flask: `backend/templates/index.html`

Expected I/O folders under `backend/`:

- Input: `backend/input/{bank_statements,receipts,invoices}` (PDF/PNG/JPG/TIFF)
- Output: `backend/output/{bank_statements,receipts,invoices}` (JSON and summaries)

## Prerequisites

- Python 3.10+
- Azure AI Document Intelligence resource (endpoint + key)

Recommended Python packages (install as needed):

```
pip install flask pandas plotly python-dotenv azure-ai-documentintelligence azure-core fastapi uvicorn pydantic
```

## Configuration

Create a `.env` file in `backend/` with your credentials (do not commit secrets):

```
AZURE_DOC_ENDPOINT=<your-azure-doc-intelligence-endpoint>
AZURE_DOC_KEY=<your-azure-doc-intelligence-key>
OPENAI_API_KEY=<optional-if-using-LLM-categorization>
```

`.env` files are ignored by git (see `.gitignore`).

## Run the Dashboard (Flask)

The dashboard loads data from `backend/output/` and renders basic visuals and tables.

```
cd backend
python app.py
```

Then open http://127.0.0.1:5000

Key routes provided by the Flask app:

- `GET /` – dashboard UI
- `GET /api/bank-statements` – parsed statements + visuals
- `GET /api/receipts` – receipt data with filters (merchant/date/amount)
- `GET /api/invoices` – invoice data + vendor chart
- `GET /debug/bank-statements` – quick sanity/debug info

Notes on bank statement loading:

- Preferred source: structured JSON files created by the analyzer, named like `*_bank_statement.json` under `output/bank_statements/`.
- Fallback: pairs of CSVs named `*_summary.csv` and `*_all_transactions.csv` in `output/` or `output/bank_statements/` are combined to reconstruct accounts and transactions.

## Analyze Documents (Azure)

Use the quickstart/analyzers to process files from `backend/input/` and save structured JSON to `backend/output/`.

- Bank statements: `python backend/doc_intel_quickstart.py` (default sample), or call `analyze_bank_statement(input_file, output_dir)`
- Receipts: `analyze_receipt(input_file, output_dir)`
- Invoices: `analyze_invoice(input_file, output_dir)`

Batch processing helper:

```
cd backend
python batch_processor.py
```

This scans `input/bank_statements`, `input/receipts`, and `input/invoices` and writes results into the corresponding `output/*` folders with a batch summary JSON per run.

## Programmatic API (FastAPI, optional)

A small API exists for uploads, extraction, and categorization if you prefer an API-first flow.

```
uvicorn AI-Book-Keeping.backend.main:app --reload
```

Endpoints:

- `GET /health` – service status
- `POST /upload` – upload a file, stored locally under `backend/uploads/`
- `POST /extract/{file_id}` – run stub extraction (`extract.py`) for MVP
- `POST /categorize` – categorize transactions (heuristics; LLM-ready)

## Project Layout

```
AI-Book-Keeping/
├── backend/
│   ├── app.py                      # Flask dashboard + JSON APIs
│   ├── main.py                     # Optional FastAPI API
│   ├── doc_intel_quickstart.py     # Azure Doc Intelligence analyzers
│   ├── batch_processor.py          # Batch runner over input/*
│   ├── categorize.py               # Categorization logic
│   ├── extract.py                  # Extraction stubs/helpers
│   ├── templates/
│   │   └── index.html              # Dashboard template
│   ├── input/                      # Place PDFs/images here
│   └── output/                     # Analyzer outputs (JSON/CSV)
├── frontend/                       # Placeholder (not required for Flask UI)
├── scripts/                        # Deployment/setup placeholders
├── LICENSE
└── README.md
```

## Tips & Caveats

- Ensure your Azure resource has the prebuilt models used here: `prebuilt-bankStatement.us`, `prebuilt-receipt`, `prebuilt-invoice`.
- The dashboard expects analyzer outputs; run a batch first if the UI shows “No data found”.
- Keep `.env` out of source control. Rotate keys if accidentally committed.

## References

- Azure AI Document Intelligence SDK for Python: https://learn.microsoft.com/azure/ai-services/document-intelligence/
