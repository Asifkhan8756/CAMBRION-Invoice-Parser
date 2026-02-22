"""Utility functions for image and PDF processing."""

import base64

from pypdf import PdfReader
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


def pdf_to_text(pdf_bytes: bytes) -> str:
    """Extract text directly from a PDF using pypdf."""
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def invoice_data_extraction(image_bytes: bytes) -> str:
    """Extract all text from an invoice image using OpenAI Vision.

    Encodes the image as base64 and sends it to GPT-4.1's vision capability.
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract all text from this invoice image exactly as it appears. "
                            "Include all numbers, dates, names, addresses, and line items."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=2000,
    )

    return response.choices[0].message.content