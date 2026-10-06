import os

MSYS2_BIN = r"C:\msys64\ucrt64\bin"

if os.path.isdir(MSYS2_BIN):
    os.add_dll_directory(MSYS2_BIN)

from weasyprint import HTML


def generate_pdf(html_content):
    """
    Convert HTML content into PDF bytes.
    """

    return HTML(
        string=html_content
    ).write_pdf()