"""Configuration for TOD PDF Service."""

import os
from pathlib import Path

# Flask configuration
DEBUG = os.getenv("FLASK_ENV") == "development"
JSON_SORT_KEYS = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request size

# PDF configuration
TEMPLATE_PATH = Path(__file__).parent / "templates" / "TOD_A4.pdf"
MAX_IMMOBILIZATION_ROWS = 12

# MinIO configuration
MINIO_ENABLED = all(
    [
        os.getenv("MINIO_ENDPOINT"),
        os.getenv("MINIO_ACCESS_KEY"),
        os.getenv("MINIO_SECRET_KEY"),
    ]
)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "s3.dimivp.be")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "logboek-pdfs")
MINIO_FOLDER = "tod-pdfs"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# PDF generation settings
PDF_PAGE_WIDTH = 210  # A4 width in mm
PDF_PAGE_HEIGHT = 297  # A4 height in mm
PDF_FONT_FAMILY = "Helvetica-Bold"
PDF_FONT_SIZE_NORMAL = 10
PDF_FONT_SIZE_SMALL = 8

# Radio button styling
RADIO_BUTTON_RADIUS = 3  # pixels
RADIO_BUTTON_FILL_RADIUS = 1.5  # pixels for filled dot
