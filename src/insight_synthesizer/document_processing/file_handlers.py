"""File handling utilities for various document formats."""

from pathlib import Path
from typing import List
from ..config import PROCESSING_CONFIG


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from supported file types.
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file type is not supported
    """
    suffix = file_path.suffix.lower()
    
    if suffix == '.txt':
        return file_path.read_text(encoding='utf-8')
    elif suffix == '.rtf':
        from striprtf.striprtf import rtf_to_text
        return rtf_to_text(file_path.read_text(encoding='utf-8'))
    elif suffix == '.docx':
        import docx
        doc = docx.Document(file_path)
        return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
    elif suffix == '.pdf':
        import PyPDF2
        with open(file_path, 'rb') as f:
            return '\n'.join(page.extract_text() for page in PyPDF2.PdfReader(f).pages)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def find_supported_files(directory: Path) -> List[Path]:
    """
    Find all supported files in directory.
    
    Args:
        directory: Directory to search for files
        
    Returns:
        List of supported file paths, sorted by name
    """
    files = []
    for ext in PROCESSING_CONFIG['supported_extensions']:
        files.extend(directory.glob(f"*{ext}"))
    return sorted(files)


def check_dependencies() -> None:
    """
    Check if required dependencies are installed.
    
    Raises:
        SystemExit: If required dependencies are missing
    """
    missing_deps = []
    
    try:
        import docx
    except ImportError:
        missing_deps.append("python-docx")
    
    try:
        import PyPDF2
    except ImportError:
        missing_deps.append("PyPDF2")
    
    if missing_deps:
        from rich.console import Console
        console = Console()
        console.print(f"[red]Missing dependencies: {', '.join(missing_deps)}[/]")
        console.print("Install with: pip install -r requirements.txt")
        raise SystemExit(1)