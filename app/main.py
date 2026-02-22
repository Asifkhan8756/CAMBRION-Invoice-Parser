"""FastAPI application for invoice document parsing."""

import json

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.models import InvoiceData, LineItem
from app.dspy_parser import setup_dspy
from app.utils import invoice_data_extraction, pdf_to_text

app = FastAPI(
    title="Invoice Parser API",
    description="Parse invoice documents and extract structured data using DSPy",
    version="1.0.0",
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = ["image/png", "application/pdf"]

# Initialize DSPy parser once at startup for reuse across requests
parser = setup_dspy()


@app.get("/health")
async def health_check() -> dict:
    """Check if the API server is running."""
    return {"status": "healthy"}


@app.post("/parse-invoice", response_model=InvoiceData)
async def parse_invoice(file: UploadFile = File(...)) -> InvoiceData:
    """Accept an invoice file (PNG or PDF) and return extracted structured data."""

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Accepted: PNG and PDF.",
        )

    # Read file bytes
    file_bytes = await file.read()

    # Validate not empty
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the 10 MB limit.",
        )

    try:
        # Extract text based on file type
        if file.content_type == "application/pdf":
            text = pdf_to_text(file_bytes)
        else:
            text = invoice_data_extraction(file_bytes)

        # Extract structured data using DSPy ChainOfThought
        result = parser(invoice_text=text)

        # Parse line items from JSON string to list of LineItem objects
        line_items: list[LineItem] = []
        if result.line_items:
            parsed_items = (
                json.loads(result.line_items)
                if isinstance(result.line_items, str)
                else result.line_items
            )
            line_items = [LineItem(**item) for item in parsed_items]

        # Build and return validated response
        return InvoiceData(
            invoice_number=result.invoice_number,
            date=result.date,
            vendor_name=result.vendor_name,
            total_amount=float(result.total_amount),
            currency=result.currency,
            line_items=line_items,
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse line items from invoice.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process invoice: {str(e)}",
        )