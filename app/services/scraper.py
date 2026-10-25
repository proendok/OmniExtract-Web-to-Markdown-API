import re
import ipaddress
import urllib.parse
from typing import Dict, Any, Optional
import httpx
import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# User agent rotation to avoid basic bot blocks
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

def is_safe_url(url: str) -> bool:
    """SSRF Protection: Ensure URL does not target localhost, private IPs, or internal cloud metadata."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Check direct IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
            # AWS / GCP metadata IP
            if str(ip) == "169.254.169.254":
                return False
        except ValueError:
            # It's a domain name
            lower_host = hostname.lower()
            if lower_host in ("localhost", "127.0.0.1", "0.0.0.0", "internal", "metadata.google.internal"):
                return False
            if lower_host.endswith(".local") or lower_host.endswith(".internal"):
                return False
                
        return True
    except Exception:
        return False

def estimate_tokens(text: str) -> int:
    """Rough token estimation for LLMs (average 4 chars or ~0.75 words per token)."""
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    return max(1, int((words * 1.3 + chars / 4) / 2))

async def fetch_html(url: str, timeout_seconds: float = 12.0) -> str:
    """Fetch raw HTML with resilience and SSRF validation."""
    if not is_safe_url(url):
        raise ValueError("Invalid or restricted URL target (SSRF prevention).")
        
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=timeout_seconds,
        verify=False  # allow scraping sites with relaxed SSL certificates
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

def extract_metadata_from_soup(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Extract OpenGraph, Twitter, and standard HTML metadata."""
    def get_tag_attr(name: str, attr: str = "content"):
        tag = (
            soup.find("meta", property=name) or 
            soup.find("meta", attrs={"name": name})
        )
        return tag.get(attr, "").strip() if tag and tag.has_attr(attr) else ""

    title = (
        get_tag_attr("og:title") or 
        get_tag_attr("twitter:title") or 
        (soup.title.string.strip() if soup.title and soup.title.string else "")
    )
    
    description = (
        get_tag_attr("og:description") or 
        get_tag_attr("description") or 
        get_tag_attr("twitter:description")
    )
    
    image = (
        get_tag_attr("og:image") or 
        get_tag_attr("twitter:image")
    )
    
    site_name = get_tag_attr("og:site_name")
    if not site_name:
        parsed = urllib.parse.urlparse(url)
        site_name = parsed.netloc.replace("www.", "")

    return {
        "title": title,
        "description": description,
        "image": image,
        "site_name": site_name,
        "url": url
    }

def clean_html_fallback(html_content: str) -> str:
    """Fallback parser: Clean HTML manually using BeautifulSoup & convert to Markdown."""
    soup = BeautifulSoup(html_content, "lxml")
    
    # Strip non-content tags
    for tag in soup(["script", "style", "nav", "footer", "aside", "iframe", "noscript", "svg", "form"]):
        tag.decompose()
        
    # Remove obvious ad/cookie elements
    for selector in [".cookie-banner", ".ad", ".advertisement", "#cookie-notice", ".social-share"]:
        for el in soup.select(selector):
            el.decompose()
            
    body = soup.find("main") or soup.find("article") or soup.body or soup
    return md(str(body), heading_style="ATX", strip=['a'] if False else [])

async def extract_clean_content(url: str, html: Optional[str] = None) -> Dict[str, Any]:
    """
    Main extraction pipeline:
    1. Fetches HTML if not provided.
    2. Runs Trafilatura for state-of-the-art article extraction.
    3. Runs fallback if Trafilatura output is too sparse.
    4. Computes token savings vs raw HTML.
    """
    if not html:
        html = await fetch_html(url)
        
    raw_html_tokens = estimate_tokens(html)
    
    # 1. Trafilatura Extraction
    trafilatura_result = trafilatura.extract(
        html,
        output_format="markdown",
        include_links=True,
        include_images=True,
        include_tables=True,
        favor_recall=True,
        url=url
    )
    
    soup = BeautifulSoup(html, "lxml")
    metadata = extract_metadata_from_soup(soup, url)
    
    # Check if trafilatura got good content
    if trafilatura_result and len(trafilatura_result.strip()) > 100:
        clean_markdown = trafilatura_result.strip()
    else:
        # Fallback
        clean_markdown = clean_html_fallback(html).strip()
        
    # Clean excessive whitespace
    clean_markdown = re.sub(r'\n{3,}', '\n\n', clean_markdown)
    
    markdown_tokens = estimate_tokens(clean_markdown)
    tokens_saved = max(0, raw_html_tokens - markdown_tokens)
    savings_percent = round((tokens_saved / max(1, raw_html_tokens)) * 100, 1)

    return {
        "url": url,
        "title": metadata.get("title") or "Untitled Document",
        "description": metadata.get("description", ""),
        "site_name": metadata.get("site_name", ""),
        "image": metadata.get("image", ""),
        "markdown": clean_markdown,
        "length_characters": len(clean_markdown),
        "tokens_markdown": markdown_tokens,
        "tokens_raw_html": raw_html_tokens,
        "tokens_saved": tokens_saved,
        "savings_percentage": f"{savings_percent}%"
    }
