document.addEventListener('DOMContentLoaded', () => {
  const urlInput = document.getElementById('target-url');
  const extractBtn = document.getElementById('btn-extract');
  const markdownOutput = document.getElementById('markdown-output');
  const tokenSavingsVal = document.getElementById('token-savings-val');
  const tokensMarkdownVal = document.getElementById('tokens-markdown-val');
  const tokensHtmlVal = document.getElementById('tokens-html-val');
  const metadataTitle = document.getElementById('meta-title');
  const metadataDesc = document.getElementById('meta-desc');
  const copyBtn = document.getElementById('btn-copy-md');
  const snippetBox = document.getElementById('code-snippet-box');
  const tabBtns = document.querySelectorAll('.tab-btn');

  // Interactive Live Extraction
  if (extractBtn) {
    extractBtn.addEventListener('click', async () => {
      const url = urlInput.value.trim();
      if (!url) {
        alert('Please enter a valid website URL.');
        return;
      }

      extractBtn.disabled = true;
      extractBtn.innerHTML = 'Extracting... ⚡';
      markdownOutput.textContent = 'Fetching and converting to clean Markdown...';

      try {
        const response = await fetch('/v1/scrape', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url })
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.detail || 'Extraction failed');
        }

        const data = result.data;
        markdownOutput.textContent = data.markdown;
        
        // Update stats
        if (tokenSavingsVal) tokenSavingsVal.textContent = data.savings_percentage;
        if (tokensMarkdownVal) tokensMarkdownVal.textContent = `${data.tokens_markdown.toLocaleString()} tokens`;
        if (tokensHtmlVal) tokensHtmlVal.textContent = `${data.tokens_raw_html.toLocaleString()} tokens`;
        
        // Update metadata
        if (metadataTitle) metadataTitle.textContent = data.title || 'Untitled';
        if (metadataDesc) metadataDesc.textContent = data.description || 'No meta description found.';

      } catch (err) {
        markdownOutput.textContent = `Error: ${err.message}`;
      } finally {
        extractBtn.disabled = false;
        extractBtn.innerHTML = 'Extract to Markdown 🚀';
      }
    });
  }

  // Copy Markdown
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const text = markdownOutput.textContent;
      navigator.clipboard.writeText(text).then(() => {
        copyBtn.textContent = 'Copied! ✓';
        setTimeout(() => { copyBtn.textContent = 'Copy Markdown'; }, 2000);
      });
    });
  }

  // Code snippet tabs
  const snippets = {
    curl: `curl -X POST "https://your-domain.com/v1/scrape" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'`,

    python: `import requests

url = "https://your-domain.com/v1/scrape"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
payload = {"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
print("Clean Markdown:", data["data"]["markdown"])
print("Tokens saved:", data["data"]["savings_percentage"])`,

    javascript: `const response = await fetch("https://your-domain.com/v1/scrape", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ url: "https://en.wikipedia.org/wiki/Artificial_intelligence" })
});

const result = await response.json();
console.log(result.data.markdown);`
  };

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const lang = btn.getAttribute('data-lang');
      if (snippetBox && snippets[lang]) {
        snippetBox.textContent = snippets[lang];
      }
    });
  });

  // Automated Checkout Function
  window.subscribeToPlan = async function(tier) {
    const customerEmail = prompt('Enter your email for the API key delivery:');
    if (!customerEmail) return;

    try {
      const res = await fetch('/v1/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: tier,
          customer_email: customerEmail
        })
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || 'Checkout error');
        return;
      }

      // Redirect directly to Stripe hosted checkout page
      window.location.href = data.checkout_url;
    } catch (e) {
      alert(`Could not initiate checkout: ${e.message}`);
    }
  };
});
