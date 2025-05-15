"""Utility functions for working with Spire.Doc documents."""

from pathlib import Path

# Constant for the Spire.Doc evaluation warning text
EVALUATION_WARNING_TEXT = "Evaluation Warning: The document was created with Spire.Doc for Python."

try:
    from docx import Document as DocxDocument
except ImportError as err:
    # Define a message for the import error
    error_msg = "python-docx package is required for this function"
    raise ImportError(error_msg) from err


def remove_evaluation_warning(file_path: str | Path) -> bool:
    """Remove 'Evaluation Warning' from a Word document created with Spire.Doc free version.

    Args:
        file_path: Path to the Word document (.docx)

    Returns:
        bool: True if warning was removed, False if no warning was found or an error occurred
    """
    # Convert to Path object if string
    if isinstance(file_path, str):
        file_path = Path(file_path)

    try:
        # Open the document using python-docx
        docx_doc = DocxDocument(file_path)

        # Check if the first paragraph contains the evaluation warning
        if docx_doc.paragraphs and EVALUATION_WARNING_TEXT in docx_doc.paragraphs[0].text:
            # Remove the first paragraph (the warning) using the parent element
            paragraph_element = docx_doc.paragraphs[0]._element  # noqa: SLF001
            parent_element = paragraph_element.getparent()
            parent_element.remove(paragraph_element)

            # Save the document without the warning
            docx_doc.save(file_path)
            return True
        else:
            return False  # No warning found

    except (OSError, ValueError, AttributeError):
        # If any error occurs during processing, return False
        return False
