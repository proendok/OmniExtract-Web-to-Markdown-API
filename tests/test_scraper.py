import pytest
import asyncio
from app.services.scraper import extract_clean_content, estimate_tokens, is_safe_url
from app.database import init_db, create_api_key, get_api_key_details, check_ip_limit

def test_ssrf_safety():
    assert is_safe_url("http://127.0.0.1:8000") is False
    assert is_safe_url("http://localhost/admin") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("https://en.wikipedia.org/wiki/Python_(programming_language)") is True
    assert is_safe_url("https://news.ycombinator.com") is True

def test_token_estimation():
    text = "Hello world! This is a test sentence."
    tokens = estimate_tokens(text)
    assert tokens > 0
    assert tokens < len(text)

@pytest.mark.asyncio
async def test_html_extraction():
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>OmniExtract Test Article</title>
        <meta name="description" content="A test article for automated extraction.">
      </head>
      <body>
        <nav><a href="#">Home</a><a href="#">About</a></nav>
        <div class="cookie-banner">Please accept all cookies.</div>
        <article>
          <h1>The Rise of Autonomous AI Systems</h1>
          <p>Autonomous AI systems are revolutionizing software development and business operations.</p>
          <p>By automating the end-to-end workflow, teams can focus on high-level decision making.</p>
        </article>
        <footer>Copyright 2026. All rights reserved.</footer>
      </body>
    </html>
    """
    result = await extract_clean_content("https://example.com/test", html=sample_html)
    assert "The Rise of Autonomous AI Systems" in result["markdown"]
    assert "cookie" not in result["markdown"].lower()
    assert result["tokens_saved"] >= 0
    assert result["title"] == "OmniExtract Test Article"

@pytest.mark.asyncio
async def test_database_and_keys():
    await init_db()
    key = await create_api_key(tier="starter", customer_email="tester@test.com", custom_limit=5000)
    assert key.startswith("omni_sta_")
    
    details = await get_api_key_details(key)
    assert details is not None
    assert details["tier"] == "starter"
    assert details["monthly_limit"] == 5000
    assert details["requests_this_month"] == 0
    assert details["is_active"] == 1

if __name__ == "__main__":
    asyncio.run(test_database_and_keys())
    asyncio.run(test_html_extraction())
    test_ssrf_safety()
    test_token_estimation()
    print("All unit tests passed successfully!")
