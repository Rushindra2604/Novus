
import os

from flask import current_app
from weasyprint import HTML

MSYS2_BIN = r"C:\msys64\ucrt64\bin"

if os.path.isdir(MSYS2_BIN):
    os.add_dll_directory(MSYS2_BIN)


def generate_pdf(html_content):
    """
    Convert HTML content into PDF bytes.
    Resolve static CSS and other assets from the Flask application.
    """
    return HTML(
        string=html_content,
        base_url=current_app.root_path
    ).write_pdf()
