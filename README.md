# CitationLint 📚✓

Verify academic paper citations by checking DOIs against CrossRef.

**Problem:** NeurIPS 2025 had 100+ hallucinated citations across 51 papers. LLMs make up references.

**Solution:** Upload PDF → extract citations → verify each DOI → get report.

## Quick Start

```bash
# Setup
cd citationlint
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run API
uvicorn src.api:app --reload --port 8000

# Test with a PDF
curl -X POST "http://localhost:8000/verify" -F "file=@paper.pdf"
```

## Features

- **PDF Parsing**: Extracts text from academic PDFs using pdfplumber
- **DOI Detection**: Finds DOIs using robust regex patterns
- **CrossRef Verification**: Validates DOIs against CrossRef's free API
- **Detailed Reports**: Returns title, authors, year for valid citations

## API Endpoints

### `POST /verify`
Upload a PDF and get a verification report.

```bash
curl -X POST "http://localhost:8000/verify" \
  -F "file=@your-paper.pdf"
```

Response:
```json
{
  "filename": "your-paper.pdf",
  "total_pages": 12,
  "total_citations": 45,
  "dois_found": 38,
  "verified_valid": 35,
  "verified_invalid": 3,
  "results": [
    {
      "citation_number": 1,
      "doi": "10.1234/example",
      "valid": true,
      "title": "Actual Paper Title",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2023
    },
    {
      "citation_number": 2,
      "doi": "10.9999/hallucinated",
      "valid": false,
      "error": "DOI not found in CrossRef"
    }
  ]
}
```

### `GET /verify-doi/{doi}`
Verify a single DOI.

```bash
curl "http://localhost:8000/verify-doi/10.1038/nature12373"
```

## CLI Usage

```bash
# Verify a PDF
python test_cli.py paper.pdf

# Test DOI verification only
python test_cli.py --test-dois
```

## Project Structure

```
citationlint/
├── src/
│   ├── __init__.py
│   ├── api.py          # FastAPI endpoints
│   ├── extractor.py    # PDF → DOI extraction
│   └── verifier.py     # DOI → CrossRef verification
├── tests/
├── test_cli.py         # CLI test script
├── requirements.txt
├── PLAN.md             # Build specification
└── README.md
```

## How It Works

1. **PDF Extraction**: Uses pdfplumber to extract text from uploaded PDFs
2. **Reference Detection**: Finds the References/Bibliography section
3. **DOI Extraction**: Regex pattern matches DOIs (10.XXXX/...)
4. **CrossRef Lookup**: Each DOI is verified against CrossRef's free API
5. **Report Generation**: Returns detailed JSON with validation results

## Limitations

- Scanned/image-based PDFs won't work (no OCR)
- Some old papers don't have DOIs
- CrossRef may not have all publications (especially non-English)
- Rate limited to ~50 requests/second

## Tech Stack

- **FastAPI**: Modern async Python web framework
- **pdfplumber**: PDF text extraction
- **CrossRef API**: DOI verification (free, no API key needed)
- **Python 3.10+**

## License

MIT

---

*Built for catching hallucinated citations* 💀🔥
