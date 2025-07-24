import fitz
from typing import List, Optional
import logging
from dataclasses import dataclass
from typing import Tuple

# Configure logging
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SpanInfo:
    """Immutable data class for text span information"""
    text: str
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    size: float
    page: int
    font: str = ""
    is_bold: bool = False
    is_italic: bool = False
    color: str = ""
    
    def __post_init__(self):
        # Validate data integrity
        if self.page < 1:
            raise ValueError("Page number must be positive")
        if self.size <= 0:
            raise ValueError("Font size must be positive")
        if len(self.bbox) != 4:
            raise ValueError("BBox must have 4 coordinates")

class PDFTextExtractor:
    """Enhanced PDF text extraction with robust error handling and filtering"""
    
    def __init__(self, min_font_size: float = 6.0, max_font_size: float = 72.0):
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
    
    def extract_text_spans(self, pdf_path: str) -> List[SpanInfo]:
        """
        Extract text spans from PDF and return SpanInfo objects.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of SpanInfo objects containing text and formatting information
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is corrupted or invalid
            RuntimeError: If extraction fails
        """
        try:
            with fitz.open(pdf_path) as doc:
                spans = []
                logger.info(f"Extracting text spans from {pdf_path} ({doc.page_count} pages)")
                for page_num, page in enumerate(doc, 1):
                    try:
                        page_spans = self._extract_page_spans(page, page_num)
                        spans.extend(page_spans)
                        if page_num % 10 == 0:  # Log progress every 10 pages
                            logger.debug(f"Processed {page_num}/{doc.page_count} pages")
                    except Exception as e:
                        logger.warning(f"Error processing page {page_num}: {e}")
                        continue
                # Filter and validate spans
                filtered_spans = self._filter_spans(spans)
                logger.info(f"Extracted {len(filtered_spans)} valid text spans from {doc.page_count} pages")
                return filtered_spans
            
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {pdf_path}: {e}")
    
    def _extract_page_spans(self, page: fitz.Page, page_num: int) -> List[SpanInfo]:
        """Extract spans from a single page"""
        spans = []
        
        try:
            # Get text with detailed formatting information
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        
                        # Skip empty or whitespace-only text
                        if not text or text.isspace():
                            continue
                        
                        # Extract formatting information
                        font_info = self._parse_font_info(span)
                        color = self._parse_color(span)
                        
                        # Create SpanInfo object
                        span_info = SpanInfo(
                            text=text,
                            bbox=tuple(span["bbox"]),
                            size=span["size"],
                            page=page_num,
                            font=font_info["font_name"],
                            is_bold=font_info["is_bold"],
                            is_italic=font_info["is_italic"],
                            color=color
                        )
                        
                        spans.append(span_info)
                        
        except Exception as e:
            logger.warning(f"Error extracting spans from page {page_num}: {e}")
        
        return spans
    
    def _parse_font_info(self, span: dict) -> dict:
        """Parse font information from span"""
        font_name = span.get("font", "")
        flags = span.get("flags", 0)
        
        is_bold = bool(flags & 16) or "bold" in font_name.lower()
        is_italic = bool(flags & 2) or "italic" in font_name.lower()
        
        return {
            "font_name": font_name,
            "is_bold": is_bold,
            "is_italic": is_italic,
            "flags": flags
        }
    
    def _parse_color(self, span: dict) -> str:
        """Parse color information from span"""
        color = span.get("color", 0)
        if color == 0:
            return "black"
        
        #color integer to hex
        try:
            return f"#{color:06x}"
        except (ValueError, TypeError):
            return "black"
    
    def _filter_spans(self, spans: List[SpanInfo]) -> List[SpanInfo]:
        """Filter and validate spans"""
        filtered = []
        
        for span in spans:
            # Skip if font size is out of reasonable range
            if not (self.min_font_size <= span.size <= self.max_font_size):
                logger.debug(f"Skipping span with font size {span.size}: {span.text[:50]}...")
                continue
            
            # Skip very short text (likely artifacts)
            if len(span.text) < 2:
                continue
            
            # Skip spans that are mostly special characters
            if self._is_mostly_special_chars(span.text):
                continue
            
            # Skip spans with invalid bounding boxes
            if not self._is_valid_bbox(span.bbox):
                logger.debug(f"Skipping span with invalid bbox {span.bbox}: {span.text[:50]}...")
                continue
            
            filtered.append(span)
        
        return filtered
    
    def _is_mostly_special_chars(self, text: str) -> bool:
        """Check if text is mostly special characters"""
        if len(text) < 3:
            return False
        
        alphanumeric_count = sum(1 for c in text if c.isalnum())
        return alphanumeric_count / len(text) < 0.3
    
    def _is_valid_bbox(self, bbox: Tuple[float, float, float, float]) -> bool:
        """Validate bounding box coordinates"""
        x1, y1, x2, y2 = bbox
        
        # Check if bbox has valid dimensions
        if x2 <= x1 or y2 <= y1:
            return False
        
        # Check if bbox coordinates are reasonable
        if any(coord < 0 or coord > 10000 for coord in bbox):
            return False
        
        return True

# Convenience function for backward compatibility
def extract_text_spans(pdf_path: str) -> List[SpanInfo]:
    """
    Extract text spans from PDF using default settings.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of SpanInfo objects
    """
    extractor = PDFTextExtractor()
    return extractor.extract_text_spans(pdf_path)

# Enhanced extractor with custom settings
def extract_text_spans_enhanced(pdf_path: str, 
                               min_font_size: float = 6.0,
                               max_font_size: float = 72.0) -> List[SpanInfo]:
    """
    Extract text spans with custom filtering settings.
    
    Args:
        pdf_path: Path to PDF file
        min_font_size: Minimum font size to include
        max_font_size: Maximum font size to include
        
    Returns:
        List of SpanInfo objects
    """
    extractor = PDFTextExtractor(min_font_size, max_font_size)
    return extractor.extract_text_spans(pdf_path)

# Example usage and testing
if __name__ == "__main__":
    # Test the extraction
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        
        try:
            # Extract spans
            spans = extract_text_spans(pdf_path)
            
            print(f"Extracted {len(spans)} text spans")
            print("\nFirst 5 spans:")
            
            for i, span in enumerate(spans[:5]):
                print(f"\n{i+1}. Text: '{span.text[:100]}...' if len(span.text) > 100 else span.text")
                print(f"   Font: {span.font}, Size: {span.size}")
                print(f"   Bold: {span.is_bold}, Italic: {span.is_italic}")
                print(f"   Page: {span.page}, BBox: {span.bbox}")
                print(f"   Color: {span.color}")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python pdf_extractor.py <pdf_path>")