import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class PDFProcessorError(Exception):
    pass


class PDFProcessor(ABC):
    """Abstract base class for PDF processors"""

    @abstractmethod
    async def process_pdf(self, pdf_content: bytes, filename: str) -> str:
        """Process PDF and return extracted text

        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging/reference

        Returns:
            Extracted text from the PDF
        """
        pass

    @abstractmethod
    def get_processor_name(self) -> str:
        """Return processor name for logging"""
        pass


class DoclingPDFProcessor(PDFProcessor):
    """Docling implementation of PDF processor - 97.9% accuracy, RAG-optimized"""

    def __init__(self):
        try:
            self.converter = DocumentConverter()
            logger.info("Initialized Docling PDF processor")
        except Exception as e:
            raise PDFProcessorError(f"Failed to initialize Docling: {e}")

    async def process_pdf(self, pdf_content: bytes, filename: str) -> str:
        """Process PDF using Docling and return extracted text"""
        try:
            # Docling requires a file path, so we use a temporary file
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=True, mode="wb"
            ) as tmp_file:
                # Write PDF content to temp file
                tmp_file.write(pdf_content)
                tmp_file.flush()

                logger.info(f"Processing PDF '{filename}' with Docling")

                # Process with Docling
                result = self.converter.convert(Path(tmp_file.name))

                # Extract text from result
                # Docling returns a ConversionResult object with document content
                text = result.document.export_to_markdown()

                logger.info(
                    f"Successfully processed '{filename}' - extracted {len(text)} characters"
                )
                return text

        except Exception as e:
            raise PDFProcessorError(f"Failed to process PDF '{filename}': {e}")

    def get_processor_name(self) -> str:
        return "Docling"
