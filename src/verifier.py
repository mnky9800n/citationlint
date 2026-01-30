"""
DOI Verification Module

Verifies DOIs against the CrossRef API to check if they resolve to real publications.
Uses the "polite pool" for better rate limits.
"""

import re
import time
import requests
from typing import Optional
from dataclasses import dataclass, asdict


# CrossRef API configuration
CROSSREF_API_BASE = "https://api.crossref.org/works/"
POLITE_EMAIL = "citationlint@example.com"  # Gets us in the polite pool (faster)
REQUEST_TIMEOUT = 10  # seconds
RATE_LIMIT_DELAY = 0.1  # 100ms between requests (conservative)


@dataclass
class VerificationResult:
    """Result of DOI verification."""
    doi: str
    valid: bool
    title: Optional[str] = None
    authors: Optional[list[str]] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


def clean_doi(doi: str) -> str:
    """
    Clean and normalize a DOI string.
    
    Handles common issues like:
    - Trailing punctuation
    - URL prefixes
    - Whitespace
    """
    # Remove common DOI URL prefixes
    doi = doi.strip()
    prefixes = [
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
        "DOI:",
    ]
    for prefix in prefixes:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    
    # Remove trailing punctuation that's often captured by regex
    doi = doi.rstrip(".,;:)]}")
    
    # Handle URLs that might have encoding
    doi = doi.replace("%2F", "/")
    
    return doi


def extract_authors(author_list: list) -> list[str]:
    """Extract author names from CrossRef author data."""
    authors = []
    for author in author_list[:10]:  # Limit to first 10 authors
        if "family" in author:
            name = author.get("family", "")
            if "given" in author:
                name = f"{author['given']} {name}"
            authors.append(name)
        elif "name" in author:
            authors.append(author["name"])
    return authors


def verify_doi(doi: str) -> VerificationResult:
    """
    Verify a DOI against CrossRef API.
    
    Args:
        doi: The DOI string to verify (with or without prefix)
        
    Returns:
        VerificationResult with validity status and metadata if found
    """
    cleaned_doi = clean_doi(doi)
    
    if not cleaned_doi:
        return VerificationResult(
            doi=doi,
            valid=False,
            error="Empty or invalid DOI format"
        )
    
    # Validate basic DOI format
    if not re.match(r'^10\.\d{4,}/.+$', cleaned_doi):
        return VerificationResult(
            doi=doi,
            valid=False,
            error=f"Invalid DOI format: {cleaned_doi}"
        )
    
    # Build request with polite pool headers
    url = f"{CROSSREF_API_BASE}{cleaned_doi}"
    headers = {
        "User-Agent": f"CitationLint/1.0 (mailto:{POLITE_EMAIL})",
        "Accept": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("message", {})
            
            # Extract metadata
            title = message.get("title", [None])[0]
            authors = extract_authors(message.get("author", []))
            
            # Try to get year from various date fields
            year = None
            for date_field in ["published-print", "published-online", "created"]:
                if date_field in message:
                    date_parts = message[date_field].get("date-parts", [[None]])
                    if date_parts and date_parts[0]:
                        year = date_parts[0][0]
                        break
            
            # Get journal/container title
            journal = None
            container = message.get("container-title", [])
            if container:
                journal = container[0]
            
            return VerificationResult(
                doi=cleaned_doi,
                valid=True,
                title=title,
                authors=authors if authors else None,
                year=year,
                journal=journal,
            )
            
        elif response.status_code == 404:
            return VerificationResult(
                doi=cleaned_doi,
                valid=False,
                error="DOI not found in CrossRef"
            )
        else:
            return VerificationResult(
                doi=cleaned_doi,
                valid=False,
                error=f"CrossRef API error: HTTP {response.status_code}"
            )
            
    except requests.Timeout:
        return VerificationResult(
            doi=cleaned_doi,
            valid=False,
            error="CrossRef API timeout"
        )
    except requests.RequestException as e:
        return VerificationResult(
            doi=cleaned_doi,
            valid=False,
            error=f"Request failed: {str(e)}"
        )
    except Exception as e:
        return VerificationResult(
            doi=cleaned_doi,
            valid=False,
            error=f"Unexpected error: {str(e)}"
        )


def verify_dois_batch(dois: list[str], delay: float = RATE_LIMIT_DELAY) -> list[VerificationResult]:
    """
    Verify multiple DOIs with rate limiting.
    
    Args:
        dois: List of DOI strings to verify
        delay: Delay between requests in seconds
        
    Returns:
        List of VerificationResult objects
    """
    results = []
    for i, doi in enumerate(dois):
        if i > 0:
            time.sleep(delay)
        results.append(verify_doi(doi))
    return results


if __name__ == "__main__":
    # Quick test
    test_dois = [
        "10.1038/nature12373",  # Valid - Nature paper
        "10.9999/fake.doi.12345",  # Invalid - made up
        "10.1145/3292500.3330701",  # Valid - ACM paper
    ]
    
    print("Testing DOI verification...")
    for doi in test_dois:
        result = verify_doi(doi)
        status = "✓" if result.valid else "✗"
        print(f"{status} {doi}")
        if result.valid:
            print(f"   Title: {result.title}")
            print(f"   Year: {result.year}")
        else:
            print(f"   Error: {result.error}")
        print()
