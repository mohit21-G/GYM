# -*- coding: utf-8 -*-
"""Verification of Cloudflare and Groq LLM Fallback Providers."""
import os
import sys
import json
import asyncio
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.config import settings
from app.services.ai_service import AIService

async def verify_providers():
    print("=== 1. VERIFYING CLOUDFLARE WORKERS AI ===")
    cf_account = settings.CF_ACCOUNT_ID
    cf_token = settings.CF_API_TOKEN
    cf_model = settings.CF_MODEL

    print(f"Account configured: {bool(cf_account)}")
    print(f"Token configured: {bool(cf_token)}")
    print(f"Model: {cf_model}")

    if cf_account and cf_token:
        url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/{cf_model}"
        headers = {
            "Authorization": f"Bearer {cf_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are a fitness parser. Return JSON: {\"intent\": \"CREATE_FOOD_LOG\", \"entities\": {\"foodItems\": [{\"food\": \"Roti\", \"quantity\": 2, \"unit\": \"piece\"}]}}"},
                {"role": "user", "content": "2 rti khadhi"}
            ],
            "temperature": 0.1,
            "max_tokens": 256,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                print(f"Cloudflare HTTP Status: {res.status_code}")
                try:
                    data = res.json()
                    print(f"Response top-level keys: {list(data.keys())}")
                    if "result" in data and isinstance(data["result"], dict):
                        print(f"Result keys: {list(data['result'].keys())}")
                        if "choices" in data["result"]:
                            msg = data["result"]["choices"][0].get("message", {})
                            print(f"Result choices message keys: {list(msg.keys())}")
                            print(f"Result choices message content: {repr(msg.get('content'))}")
                            print(f"Result choices message reasoning: {repr(msg.get('reasoning') or msg.get('reasoning_content'))}")
                        else:
                            content_val = data["result"].get("response") or data["result"].get("content")
                            print(f"Response content present: {bool(content_val)}")
                            print(f"Reasoning present: {'reasoning' in data['result']}")
                except Exception as e:
                    print(f"JSON parse error: {e}, raw text: {res.text[:200]}")
        except Exception as e:
            print(f"Cloudflare request failed: {e}")
    else:
        print("Cloudflare credentials not fully set.")

    print("\n=== 2. VERIFYING GROQ FALLBACK ===")
    groq_key = settings.GROQ_API_KEY
    groq_model = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    print(f"Groq API Key configured: {bool(groq_key)}")
    print(f"Model: {groq_model}")

    if groq_key:
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": groq_model,
            "messages": [
                {"role": "system", "content": "You are a fitness parser. Return JSON."},
                {"role": "user", "content": "2 roti"}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(groq_url, headers=headers, json=payload)
                print(f"Groq HTTP Status: {res.status_code}")
                if res.status_code == 200:
                    data = res.json()
                    print("Groq Auth Status: Valid (200 OK)")
                    print(f"Groq Response Keys: {list(data.keys())}")
                elif res.status_code == 401:
                    print("Groq Auth Status: Invalid/Expired Key (401 Unauthorized)")
                else:
                    print(f"Groq Status: {res.status_code}, Body: {res.text[:200]}")
        except Exception as e:
            print(f"Groq request error: {e}")
    else:
        print("Groq API Key not set.")

if __name__ == "__main__":
    asyncio.run(verify_providers())
