import os
import json
import re
import fitz  # PyMuPDF
from typing import List, Dict, Any
import sys
from collections import Counter

class PDFOutlineExtractor:
    def __init__(self):
        self.heading_patterns = [
            # Pattern for numbered headings like "1.", "1.1", "1.1.1"
            r'^(\d+\.(?:\d+\.)*)\s*(.+)$',
            # Pattern for Roman numerals
            r'^([IVX]+\.)\s*(.+)$',
            # Pattern for lettered headings
            r'^([A-Z]\.)\s*(.+)$',
            # Pattern for capitalized headings
            r'^([A-Z][A-Z\s]+)$',
            # Pattern for title case headings
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$'
        ]
    
    def extract_title(self, doc) -> str:
        """Extract title from PDF metadata or first page"""
        # Try metadata first
        metadata = doc.metadata
        if metadata.get('title') and metadata['title'].strip():
            return metadata['title'].strip()
        
        # Try first page
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look for title in first few lines
            for i, line in enumerate(lines[:5]):
                if len(line) > 10 and len(line) < 100:
                    # Check if it looks like a title (not too short, not too long)
                    if not re.match(r'^\d', line) and not line.lower().startswith('abstract'):
                        return line
        
        return "Untitled Document"
    
    def is_heading(self, text: str, font_size: float, font_flags: int, avg_font_size: float) -> tuple:
        """Determine if text is a heading and its level"""
        text = text.strip()
        
        # Skip if too short or too long
        if len(text) < 3 or len(text) > 200:
            return False, None
        
        # Skip common non-heading patterns
        skip_patterns = [
            r'^\d+$',  # Just numbers
            r'^page \d+',  # Page numbers
            r'^figure \d+',  # Figure captions
            r'^table \d+',  # Table captions
            r'^\w+@\w+\.\w+',  # Email addresses
            r'^http',  # URLs
            r'^\(.*\)$',  # Text in parentheses
            r'^\[.*\]$',  # Text in brackets
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, text.lower()):
                return False, None
        
        # Check font characteristics
        is_bold = bool(font_flags & 2**4)  # Bold flag
        font_size_ratio = font_size / avg_font_size if avg_font_size > 0 else 1
        
        # Heading level determination
        level = None
        
        # Check for numbered patterns
        for pattern in self.heading_patterns:
            match = re.match(pattern, text)
            if match:
                if '.' in match.group(1):
                    dots = match.group(1).count('.')
                    if dots == 1:
                        level = "H1"
                    elif dots == 2:
                        level = "H2"
                    else:
                        level = "H3"
                else:
                    level = "H1"
                break
        
        # Check font size and style
        if not level:
            if font_size_ratio > 1.5 or (is_bold and font_size_ratio > 1.2):
                level = "H1"
            elif font_size_ratio > 1.2 or is_bold:
                level = "H2"
            elif font_size_ratio > 1.0 and (is_bold or text.isupper()):
                level = "H3"
        
        # Check for all caps (likely heading)
        if not level and text.isupper() and len(text) > 5:
            level = "H2"
        
        # Check for title case
        if not level and text.istitle() and len(text.split()) <= 8:
            level = "H3"
        
        return level is not None, level
    
    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """Extract outline from PDF"""
        try:
            doc = fitz.open(pdf_path)
            title = self.extract_title(doc)
            outline = []
            
            # Collect all text with font information
            all_texts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_dict = page.get_text("dict")
                
                for block in text_dict["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:
                                    all_texts.append({
                                        'text': text,
                                        'font_size': span["size"],
                                        'font_flags': span["flags"],
                                        'page': page_num + 1
                                    })
            
            # Calculate average font size
            font_sizes = [t['font_size'] for t in all_texts]
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
            
            # Process each text span
            seen_headings = set()
            for text_info in all_texts:
                text = text_info['text']
                is_head, level = self.is_heading(
                    text, 
                    text_info['font_size'], 
                    text_info['font_flags'], 
                    avg_font_size
                )
                
                if is_head and level and text not in seen_headings:
                    outline.append({
                        "level": level,
                        "text": text,
                        "page": text_info['page']
                    })
                    seen_headings.add(text)
            
            # Sort by page number and clean up
            outline.sort(key=lambda x: (x['page'], x['text']))
            
            # Remove duplicates while preserving order
            unique_outline = []
            seen = set()
            for item in outline:
                key = (item['level'], item['text'])
                if key not in seen:
                    unique_outline.append(item)
                    seen.add(key)
            
            doc.close()
            
            return {
                "title": title,
                "outline": unique_outline
            }
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            return {
                "title": "Error Processing Document",
                "outline": []
            }

def main():
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    extractor = PDFOutlineExtractor()
    
    # Process all PDF files in input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_filename = filename.replace('.pdf', '.json')
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Processing {filename}...")
            result = extractor.extract_outline(input_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Saved outline to {output_filename}")

if __name__ == "__main__":
    main()