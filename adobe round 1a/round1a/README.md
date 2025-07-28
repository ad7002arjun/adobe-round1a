# Round 1A: PDF Outline Extractor

## Approach

This solution extracts structured outlines from PDF documents by analyzing text formatting, font characteristics, and content patterns.

### Key Components:

1. **Font Analysis**: Analyzes font size, bold formatting, and other styling cues to identify headings
2. **Pattern Recognition**: Uses regex patterns to identify numbered sections, Roman numerals, and other heading formats
3. **Heuristic Classification**: Applies multiple heuristics to determine heading levels (H1, H2, H3)
4. **Title Extraction**: Attempts to extract title from PDF metadata or document content

### Models/Libraries Used:

- **PyMuPDF (fitz)**: PDF processing and text extraction
- **Python re**: Regular expression pattern matching
- **Standard Python libraries**: os, json, collections

### Features:

- Handles multiple heading formats (numbered, bulleted, styled)
- Removes duplicates and false positives
- Works with various PDF structures
- Processes documents up to 50 pages efficiently
- No internet connectivity required

## Build and Run Instructions

```bash
# Build the Docker image
docker build --platform linux/amd64 -t pdf-outline-extractor:v1 .

# Run the container
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-outline-extractor:v1
```

The solution automatically processes all PDF files in the `/app/input` directory and generates corresponding JSON files in `/app/output`.

## Performance

- Execution time: < 10 seconds for 50-page PDFs
- Model size: < 200MB (no ML models used)
- CPU-only execution
- Offline capability