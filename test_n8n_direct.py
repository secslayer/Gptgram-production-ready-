#!/usr/bin/env python3
"""
Test n8n webhooks directly with correct credentials
Verify the webhooks are working before system integration
"""

import requests
import json
import hmac
import hashlib

def generate_hmac_signature(payload: str, secret: str) -> str:
    """Generate HMAC SHA256 signature"""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def test_webhook(url: str, data: dict, name: str) -> dict:
    """Test a single webhook with HMAC"""
    secret = "s3cr3t"
    
    # Prepare payload and signature
    payload = json.dumps(data, separators=(',', ':'))
    signature = generate_hmac_signature(payload, secret)
    
    headers = {
        "Content-Type": "application/json",
        "X-GPTGRAM-Signature": f"sha256={signature}",
        "X-GPTGRAM-Idempotency": f"test-{name}-12345"
    }
    
    print(f"\n📝 Testing: {name}")
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print(f"Signature: sha256={signature}")
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Raw Response: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Success! JSON: {json.dumps(result)}")
                return result
            except json.JSONDecodeError:
                print(f"⚠️ Response is not JSON. Body: {response.text[:200]}")
                return {"raw": response.text}
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

print("="*80)
print("🔧 DIRECT N8N WEBHOOK TESTS")
print("="*80)

# Test 1: Sentiment Analysis
test_webhook(
    "https://templatechat.app.n8n.cloud/webhook/sentiment",
    {
        "text": "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds."
    },
    "sentiment"
)

# Test 2: Translation
test_webhook(
    "https://templatechat.app.n8n.cloud/webhook/translation-webhook",
    {
        "text": "Hello world",
        "target": "es"
    },
    "translator"
)

# Test 3: Summarization
test_webhook(
    "https://templatechat.app.n8n.cloud/webhook/gptgram/summarize",
    {
        "text": "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds.",
        "maxSentences": 2
    },
    "summarizer"
)

print("\n" + "="*80)
print("✅ Direct webhook tests complete!")
print("="*80)
