# Invoice Parser API

A FastAPI application that extracts structured data from invoice documents using OpenAI's vision capabilities and the DSPy framework. Upload an invoice (PNG or PDF) and receive parsed data including invoice number, date, vendor name, total amount, and line items as structured JSON.

## Architecture Overview

```
PNG Upload  → FastAPI Validation → OpenAI Vision (image → text)    → DSPy ChainOfThought → JSON Response
PDF Upload  → FastAPI Validation → pypdf (direct text extraction)  → DSPy ChainOfThought → JSON Response
```

The application follows a three-stage pipeline:

1. **Input Validation** (`main.py`): Accepts file uploads via a POST endpoint. Validates file type (PNG or PDF), file size (max 10MB), and ensures the file is not empty.

2. **Text Extraction** (`utils.py`): Uses a dual extraction strategy based on file type. PNG images are encoded as base64 and sent to OpenAI's GPT-4.1 vision model for text extraction. PDFs are processed directly using pypdf to extract embedded text — this is faster and cheaper since it avoids an API call entirely.

3. **Structured Extraction** (`dspy_parser.py`): Uses DSPy's `ChainOfThought` module with a typed `Signature` to extract specific fields from the raw text. The LLM reasons step by step through the invoice content to identify and format each field.

### DSPy Signature Design

The `InvoiceExtraction` signature defines a clear contract between input and output:

- **Input**: `invoice_text` — raw text extracted from the invoice document
- **Outputs**:
  - `invoice_number` — the invoice, order, or document number
  - `date` — document date converted to YYYY-MM-DD format
  - `vendor_name` — name of the vendor or supplier
  - `total_amount` — final total as a float
  - `currency` — currency code (EUR, USD, etc.)
  - `line_items` — JSON array of items with description, quantity, unit_price, and total

Each output field includes a detailed description that guides the LLM, with specific instructions for handling German date formats (e.g., "25. Juli 2025" → "2025-07-25") and German number formats (e.g., "14.949,38" → 14949.38).

### Key Design Decisions

- **GPT-4.1 for vision and extraction**: Chosen for reliable image reading and accurate structured extraction over cheaper alternatives. GPT-4o-mini was tested but produced inconsistent results with dense invoice images.
- **Dual extraction strategy**: PNG images use OpenAI Vision for text extraction, while PDFs use pypdf for direct text extraction. This avoids unnecessary API calls for PDFs, making PDF processing faster and cheaper.
- **Two-step pipeline (text extraction → DSPy)**: DSPy signatures work with text input, so the document is first converted to text (via Vision or pypdf), then processed by DSPy. This separates concerns and makes each step independently testable.
- **ChainOfThought over Predict**: Provides step-by-step reasoning which improves accuracy when parsing complex invoices with multiple line items, mixed languages, and varied number formats.
- **Line items as JSON string**: DSPy handles string outputs most reliably. The JSON string is parsed and validated through Pydantic models before returning to the client.

## Project Structure

```
invoice-parser/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── .dockerignore
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and endpoints
│   ├── models.py            # Pydantic response models
│   ├── dspy_parser.py       # DSPy signature and ChainOfThought module
│   └── utils.py             # Image/PDF text extraction
├── samples/                 # Sample invoices for testing
│   ├── Invoice1.png
│   ├── Inovice2.png
│   ├── Invoice3.png
│   ├── AB1.png
│   ├── AB2.png
│   └── AB3.png
└── tests/
    └── test_parser.py       # Pytest test suite
```

## Prerequisites

- Python 3.12+
- OpenAI API key with access to GPT-4.1

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Asifkhan8756/CAMBRION-Invoice-Parser.git
   cd invoice-parser
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

5. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

## Docker (Alternative Setup)

1. **Build the image**
   ```bash
   docker build -t invoice-parser .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env invoice-parser
   ```

3. The API will be available at `http://localhost:8000`.

## Usage Guide

### Swagger UI (Recommended)

Open `http://localhost:8000/docs` in your browser. Click on the POST `/parse-invoice` endpoint, select "Try it out", upload an invoice file, and click "Execute".

### curl Examples

**PNG invoice:**
```bash
curl -X POST "http://localhost:8000/parse-invoice" \
  -F "file=@samples/Invoice1.png"
```

**PDF invoice:**
```bash
curl -X POST "http://localhost:8000/parse-invoice" \
  -F "file=@samples/invoice.pdf"
```

### Example Response

```json
{
  "invoice_number": "AB-2025-07-042",
  "date": "2025-07-25",
  "vendor_name": "Präzisionsfertigung GmbH",
  "total_amount": 14949.38,
  "currency": "EUR",
  "line_items": [
    {
      "description": "CNC-gefrästes Präzisionsteil, Aluminium EN AW-6060",
      "quantity": 500,
      "unit_price": 12.5,
      "total": 6250.0
    },
    {
      "description": "Lasergeschnittene Blechplatte, Edelstahl 1.4301 (2mm)",
      "quantity": 150,
      "unit_price": 8.75,
      "total": 1312.5
    },
    {
      "description": "Schweißbaugruppe, Stahl S235JR, inkl. Pulverbeschichtung",
      "quantity": 20,
      "unit_price": 180.0,
      "total": 3600.0
    },
    {
      "description": "Oberflächenbehandlung (Eloxieren) für Pos. 1",
      "quantity": 500,
      "unit_price": 1.5,
      "total": 750.0
    },
    {
      "description": "Montagearbeiten für 10 Baugruppen (je 5 Pos. 1, 2)",
      "quantity": 10,
      "unit_price": 65.0,
      "total": 650.0
    }
  ]
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — returns server status |
| POST | `/parse-invoice` | Upload an invoice (PNG or PDF) and get structured data |

## Running Tests

```bash
python -m pytest tests/ -v
```

The test suite includes:
- **test_health_check**: Verifies the server is running
- **test_reject_invalid_file**: Ensures unsupported file types are rejected with 400
- **test_reject_empty_file**: Ensures empty files are rejected with 400
- **test_parse_invoice**: End-to-end test with a real invoice (requires OpenAI API key)

## Assumptions and Limitations

- **PNG and PDF only**: The API accepts PNG images and PDF documents. Other formats are rejected.
- **PDF text-based only**: PDF extraction uses pypdf which works with text-based PDFs. Scanned or image-based PDFs will not extract correctly.
- **Single page PDFs**: For PDFs, all pages are processed but complex multi-page layouts may affect extraction accuracy.
- **Language support**: Optimized for German and English invoices. Other languages may work but are not explicitly handled in the DSPy signature descriptions.
- **API dependency**: PNG processing requires an active OpenAI API key and internet connection. PDF processing works offline via pypdf.
- **Cost**: PNG processing uses GPT-4.1 for both vision and extraction. PDF processing only uses GPT-4.1 for DSPy extraction (no vision call needed).
- **Line item accuracy**: Complex or unusual invoice layouts may result in incomplete or incorrect line item extraction.
- **File size limit**: Maximum upload size is 10MB.
- **No authentication**: The API has no authentication or rate limiting — intended for local development and testing only.