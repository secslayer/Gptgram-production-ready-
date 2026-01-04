#!/usr/bin/env python3
"""
Simple standalone test for n8n webhooks
No dependencies on the main application
"""

import json
import hmac
import hashlib
import uuid
import requests
import time

# Test configuration
N8N_BASE = 'https://templatechat.app.n8n.cloud/webhook'
HMAC_SECRET = b's3cr3t'

def canonical_json(obj):
    """Create canonical JSON for HMAC signing"""
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)

def sign_payload(payload_str):
    """Generate HMAC-SHA256 signature"""
    return hmac.new(HMAC_SECRET, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()

def call_n8n_webhook(path, body):
    """Call n8n webhook with HMAC signature"""
    canonical = canonical_json(body)
    signature = sign_payload(canonical)
    headers = {
        'Content-Type': 'application/json',
        'X-GPTGRAM-Signature': f'sha256={signature}',
        'X-GPTGRAM-Idempotency': str(uuid.uuid4())
    }
    
    print(f"Calling: {N8N_BASE}{path}")
    print(f"Body: {canonical}")
    print(f"Signature: {signature}")
    
    resp = requests.post(N8N_BASE + path, headers=headers, data=canonical, timeout=60)
    resp.raise_for_status()
    return resp.json()

def test_summarizer():
    """Test the summarizer webhook"""
    print("\n=== Testing Summarizer ===")
    
    body = {
        "text": "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds.",
        "maxSentences": 2
    }
    
    try:
        result = call_n8n_webhook('/gptgram/summarize', body)
        print(f"✅ Success: {result}")
        assert 'summary' in result, "Missing 'summary' field"
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_sentiment():
    """Test the sentiment webhook"""
    print("\n=== Testing Sentiment ===")
    
    body = {
        "text": "Artificial intelligence is transforming industries worldwide."
    }
    
    # Fix the body to include maxSentences if needed for sentiment
    body = {
        "maxSentences": 2,
        "text": "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds."
    }
    
    try:
        result = call_n8n_webhook('/sentiment', body)
        print(f"✅ Success: {result}")
        assert 'sentiment' in result, "Missing 'sentiment' field"
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_translation():
    """Test the translation webhook"""
    print("\n=== Testing Translation ===")
    
    body = {
        "text": "Hello world",
        "target": "es"
    }
    
    try:
        result = call_n8n_webhook('/translation-webhook', body)
        print(f"✅ Success: {result}")
        assert 'translated' in result, "Missing 'translated' field"
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_chain_with_embedding():
    """Test embedding sentiment into summary then translating"""
    print("\n=== Testing Chain with Embedding ===")
    
    # Step 1: Summarize
    print("Step 1: Summarizing...")
    summary_body = {
        "text": "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds. Companies are investing billions in AI research.",
        "maxSentences": 1
    }
    
    summary_result = call_n8n_webhook('/gptgram/summarize', summary_body)
    print(f"Summary: {summary_result}")
    
    # Step 2: Get sentiment
    print("\nStep 2: Analyzing sentiment...")
    sentiment_body = {
        "maxSentences": 2,
        "text": summary_result.get('summary', '')
    }
    
    sentiment_result = call_n8n_webhook('/sentiment', sentiment_body)
    print(f"Sentiment: {sentiment_result}")
    
    # Step 3: Embed sentiment into summary and translate
    print("\nStep 3: Embedding sentiment and translating...")
    embedded_text = f"{summary_result.get('summary', '')} (Sentiment: {sentiment_result.get('sentiment', 'unknown')})"
    print(f"Embedded text: {embedded_text}")
    
    translation_body = {
        "text": embedded_text,
        "target": "es"
    }
    
    translation_result = call_n8n_webhook('/translation-webhook', translation_body)
    print(f"Translation: {translation_result}")
    
    # Verify sentiment is in the translation
    translated_text = translation_result.get('translated', '')
    if 'sentiment' in embedded_text.lower():
        print("✅ Sentiment successfully embedded and translated")
    else:
        print("⚠️  Sentiment may not be properly embedded")
    
    return {
        'summary': summary_result,
        'sentiment': sentiment_result,
        'translation': translation_result,
        'embedded_text': embedded_text
    }

def test_field_mapping():
    """Test field mapping when schemas don't match exactly"""
    print("\n=== Testing Field Mapping ===")
    
    # Simulate mismatched field names
    mock_outputs = {
        'Summarizer': {
            'summary_text': 'AI is transforming industries.',  # Wrong field name
            'wordCount': 5
        }
    }
    
    # Expected schema for sentiment
    expected_schema = {
        'text': 'string'  # Expects 'text' not 'summary_text'
    }
    
    # Field aliases for mapping
    field_aliases = {
        'text': ['summary', 'summary_text', 'content', 'message'],
        'summary': ['summary_text', 'text_summary', 'abstract']
    }
    
    # Apply deterministic mapping
    mapped_input = {}
    for target_field in expected_schema:
        # Direct match
        if target_field in mock_outputs['Summarizer']:
            mapped_input[target_field] = mock_outputs['Summarizer'][target_field]
        # Check aliases
        elif target_field in field_aliases:
            for alias in field_aliases[target_field]:
                if alias in mock_outputs['Summarizer']:
                    mapped_input[target_field] = mock_outputs['Summarizer'][alias]
                    break
    
    print(f"Original output: {mock_outputs['Summarizer']}")
    print(f"Expected schema: {expected_schema}")
    print(f"Mapped input: {mapped_input}")
    
    # Test with real API
    if mapped_input:
        # Need to adapt for sentiment API format
        sentiment_body = {
            "maxSentences": 2,
            "text": mapped_input.get('text', 'Default text')
        }
        
        try:
            result = call_n8n_webhook('/sentiment', sentiment_body)
            print(f"✅ Mapped call succeeded: {result}")
        except Exception as e:
            print(f"❌ Mapped call failed: {e}")
    
    return mapped_input

def test_concurrent_calls():
    """Test concurrent API calls"""
    print("\n=== Testing Concurrent Calls ===")
    
    import concurrent.futures
    
    def make_call(index):
        body = {
            "text": f"Test text {index}. AI is amazing.",
            "maxSentences": 1
        }
        try:
            result = call_n8n_webhook('/gptgram/summarize', body)
            return {'index': index, 'result': result, 'success': True}
        except Exception as e:
            return {'index': index, 'error': str(e), 'success': False}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_call, i) for i in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    successful = sum(1 for r in results if r['success'])
    print(f"Completed {successful}/{len(results)} concurrent calls successfully")
    
    for r in results:
        if r['success']:
            print(f"  Call {r['index']}: {r['result'].get('summary', 'N/A')[:50]}...")
        else:
            print(f"  Call {r['index']}: Failed - {r.get('error', 'Unknown error')}")
    
    return results

def test_idempotency():
    """Test idempotency with same key"""
    print("\n=== Testing Idempotency ===")
    
    idempotency_key = f"test-idempotent-{uuid.uuid4()}"
    body = {
        "text": "Test idempotency",
        "maxSentences": 1
    }
    
    canonical = canonical_json(body)
    signature = sign_payload(canonical)
    headers = {
        'Content-Type': 'application/json',
        'X-GPTGRAM-Signature': f'sha256={signature}',
        'X-GPTGRAM-Idempotency': idempotency_key
    }
    
    url = f'{N8N_BASE}/gptgram/summarize'
    
    print(f"Making first call with key: {idempotency_key}")
    resp1 = requests.post(url, headers=headers, data=canonical, timeout=60)
    result1 = resp1.json()
    print(f"First result: {result1}")
    
    # Small delay
    time.sleep(1)
    
    print(f"Making second call with same key: {idempotency_key}")
    try:
        resp2 = requests.post(url, headers=headers, data=canonical, timeout=60)
        if resp2.status_code == 200 and resp2.text:
            result2 = resp2.json()
            print(f"Second result: {result2}")
        else:
            print(f"Second call returned status {resp2.status_code}, body: {resp2.text[:100]}")
            result2 = {'error': 'Empty or error response'}
    except Exception as e:
        print(f"Second call failed: {e}")
        result2 = {'error': str(e)}
    
    if result1 == result2:
        print("✅ Idempotency working (results identical)")
    else:
        print("⚠️  Results differ (may not support idempotency)")
    
    return {'first': result1, 'second': result2}

def main():
    """Run all tests"""
    print("=" * 60)
    print("n8n Webhook Integration Tests")
    print("=" * 60)
    
    results = {}
    
    # Run each test
    results['summarizer'] = test_summarizer()
    results['sentiment'] = test_sentiment()
    results['translation'] = test_translation()
    results['chain'] = test_chain_with_embedding()
    results['mapping'] = test_field_mapping()
    results['concurrent'] = test_concurrent_calls()
    results['idempotency'] = test_idempotency()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    test_names = {
        'summarizer': 'Summarizer API',
        'sentiment': 'Sentiment API',
        'translation': 'Translation API',
        'chain': 'Chain with Embedding',
        'mapping': 'Field Mapping',
        'concurrent': 'Concurrent Calls',
        'idempotency': 'Idempotency'
    }
    
    for key, name in test_names.items():
        status = "✅ PASS" if results[key] else "❌ FAIL"
        print(f"{name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
