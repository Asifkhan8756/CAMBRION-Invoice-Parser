"""DSPy-based invoice parsing logic using ChainOfThought reasoning."""

import os

import dspy
from dotenv import load_dotenv

load_dotenv()

class InvoiceExtraction(dspy.Signature):
    """Extract structured information from an invoice or order confirmation document.

    The document may be in German or English. All numeric values should be
    converted from German format (e.g., 14.949,38) to standard format (14949.38).
    """

    # Input field
    invoice_text: str = dspy.InputField(
        desc="Raw text extracted from an invoice or order confirmation document"
    )

    # Output fields
    invoice_number: str = dspy.OutputField(
        desc="The invoice, order, or document number (e.g. Auftrags-Nr., Rechnungsnummer)"
    )
    date: str = dspy.OutputField(
        desc="Document date in YYYY-MM-DD format. Convert from any format like '25. Juli 2025' to '2025-07-25'"
    )
    vendor_name: str = dspy.OutputField(
        desc="Name of the vendor, supplier, or issuing company"
    )
    total_amount: float = dspy.OutputField(
        desc="Final total amount (Gesamtbetrag) as a number. Convert German format like 14.949,38 to 14949.38"
    )
    currency: str = dspy.OutputField(
        desc="Currency code, e.g. EUR, USD"
    )
    line_items: str = dspy.OutputField(
        desc=(
            'JSON array of line items. Each item has: "description" (Bezeichnung), '
            '"quantity" (Menge as number), "unit_price" (Einzelpreis as number), '
            '"total" (Gesamt as number). Convert German number format to standard decimals.'
        )
    )


class InvoiceParser(dspy.Module):
    """DSPy module that uses ChainOfThought reasoning for invoice extraction.

    ChainOfThought was chosen over basic Predict because it reasons step by step,
    improving accuracy for complex invoices with multiple line items and mixed formats.
    """

    def __init__(self) -> None:
        super().__init__()
        self.extractor = dspy.ChainOfThought(InvoiceExtraction)

    def forward(self, invoice_text: str) -> dspy.Prediction:
        """Run the extraction pipeline on the given invoice text."""
        return self.extractor(invoice_text=invoice_text)


def setup_dspy() -> InvoiceParser:
    """Configure the DSPy language model and return an InvoiceParser instance.

    Uses OpenAI GPT-4.1 for reliable structured extraction.
    Called once at application startup.
    """
    lm = dspy.LM("openai/gpt-4.1", api_key=os.getenv("OPENAI_API_KEY"))
    dspy.configure(lm=lm)
    return InvoiceParser()