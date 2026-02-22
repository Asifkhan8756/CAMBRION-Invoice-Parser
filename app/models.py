"""Pydantic models for API request validation and response serialization."""

from pydantic import BaseModel


class LineItem(BaseModel):
    """Represents a single line item from an invoice."""

    description: str  # Item description (e.g., "Laptop Stand")
    quantity: float  # Number of units
    unit_price: float  # Price per unit
    total: float  # Total price for this line item


class InvoiceData(BaseModel):
    """Structured response containing all extracted invoice data."""

    invoice_number: str  # Invoice or order number (e.g., "INV-2024-001")
    date: str  # Invoice date in YYYY-MM-DD format
    vendor_name: str  # Name of the vendor or supplier
    total_amount: float  # Final total amount including tax
    currency: str  # Currency code (e.g., "EUR", "USD")
    line_items: list[LineItem]  # List of individual items on the invoice