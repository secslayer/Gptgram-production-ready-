#!/usr/bin/env python
"""
Setup script for investor demo
Creates demo users, agents, and chains for the 90-second presentation
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, init_db
from backend.app.models import User, Agent, Chain, Wallet
from backend.app.models.user import UserRole
from backend.app.models.agent import AgentType, VerificationLevel, AgentStatus
from backend.app.models.chain import ChainMode
from passlib.context import CryptContext
import json
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def setup_demo():
    print("🚀 Setting up GPTGram investor demo...")
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # 1. Create demo user
        print("Creating demo user...")
        demo_user = User(
            email="demo@gptgram.ai",
            username="demo",
            password_hash=pwd_context.hash("demo123"),
            role=UserRole.CREATOR
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        # 2. Create wallet with balance
        print("Setting up wallet...")
        wallet = Wallet(
            user_id=demo_user.id,
            balance_cents=5000,  # $50.00
            reserved_cents=0,
            currency="USD"
        )
        db.add(wallet)
        db.commit()
        
        # 3. Create demo agents
        print("Creating demo agents...")
        
        # n8n Text Summarizer
        summarizer = Agent(
            owner_user_id=demo_user.id,
            name="n8n Text Summarizer",
            slug="n8n-text-summarizer",
            description="Summarizes long text into concise summaries using n8n workflows",
            type=AgentType.N8N,
            endpoint_url="https://demo.n8n.io/webhook/summarize",
            auth={"type": "hmac", "secret_name": "N8N_HMAC_SECRET"},
            price_cents=50,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "maxSentences": {"type": "integer", "default": 3}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "wordCount": {"type": "integer"}
                },
                "required": ["summary"]
            },
            sample_request={
                "text": "Artificial intelligence is rapidly transforming industries...",
                "maxSentences": 2
            },
            sample_response={
                "summary": "AI is transforming industries at an unprecedented pace.",
                "wordCount": 8
            },
            verification_level=VerificationLevel.L2,
            status=AgentStatus.ACTIVE,
            metrics_cache={
                "success_rate": 0.95,
                "avg_latency_ms": 1200,
                "call_volume": 234
            }
        )
        db.add(summarizer)
        
        # Sentiment Analyzer
        sentiment = Agent(
            owner_user_id=demo_user.id,
            name="Sentiment Analyzer Pro",
            slug="sentiment-analyzer-pro",
            description="Advanced sentiment analysis with confidence scoring",
            type=AgentType.CUSTOM,
            endpoint_url="https://api.gptgram.ai/sentiment",
            auth={"type": "jwt"},
            price_cents=30,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "confidence": {"type": "number"}
                },
                "required": ["sentiment", "confidence"]
            },
            sample_request={
                "text": "This product is absolutely amazing!"
            },
            sample_response={
                "sentiment": "positive",
                "confidence": 0.98
            },
            verification_level=VerificationLevel.L3,
            status=AgentStatus.ACTIVE,
            metrics_cache={
                "success_rate": 0.98,
                "avg_latency_ms": 800,
                "call_volume": 456
            }
        )
        db.add(sentiment)
        
        # Language Translator
        translator = Agent(
            owner_user_id=demo_user.id,
            name="n8n Language Translator",
            slug="n8n-language-translator",
            description="Translates text between 50+ languages using n8n and Google Translate",
            type=AgentType.N8N,
            endpoint_url="https://demo.n8n.io/webhook/translate",
            auth={"type": "hmac", "secret_name": "N8N_HMAC_SECRET"},
            price_cents=75,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "targetLanguage": {"type": "string", "default": "fr"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "translatedText": {"type": "string"},
                    "detectedLanguage": {"type": "string"}
                },
                "required": ["translatedText"]
            },
            sample_request={
                "text": "Hello world",
                "targetLanguage": "fr"
            },
            sample_response={
                "translatedText": "Bonjour le monde",
                "detectedLanguage": "en"
            },
            verification_level=VerificationLevel.L2,
            status=AgentStatus.ACTIVE,
            metrics_cache={
                "success_rate": 0.92,
                "avg_latency_ms": 1500,
                "call_volume": 123
            }
        )
        db.add(translator)
        
        # Additional agents for marketplace
        agents_data = [
            {
                "name": "Content Moderator",
                "slug": "content-moderator",
                "description": "AI-powered content moderation for safety",
                "type": AgentType.CUSTOM,
                "price_cents": 25,
                "verification_level": VerificationLevel.L1
            },
            {
                "name": "Text Formatter",
                "slug": "text-formatter",
                "description": "Formats and cleans text data",
                "type": AgentType.CUSTOM,
                "price_cents": 15,
                "verification_level": VerificationLevel.L2
            },
            {
                "name": "Keyword Extractor",
                "slug": "keyword-extractor",
                "description": "Extracts key terms and entities",
                "type": AgentType.CUSTOM,
                "price_cents": 40,
                "verification_level": VerificationLevel.L3
            }
        ]
        
        for agent_data in agents_data:
            agent = Agent(
                owner_user_id=demo_user.id,
                name=agent_data["name"],
                slug=agent_data["slug"],
                description=agent_data["description"],
                type=agent_data["type"],
                endpoint_url=f"https://api.gptgram.ai/{agent_data['slug']}",
                auth={"type": "jwt"},
                price_cents=agent_data["price_cents"],
                input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
                verification_level=agent_data["verification_level"],
                status=AgentStatus.ACTIVE,
                metrics_cache={
                    "success_rate": 0.90,
                    "avg_latency_ms": 1000,
                    "call_volume": 50
                }
            )
            db.add(agent)
        
        db.commit()
        
        # 4. Create demo chain
        print("Creating demo chain...")
        chain = Chain(
            owner_user_id=demo_user.id,
            name="Text Processing Pipeline",
            descriptor={
                "nodes": [
                    {
                        "node_id": "node_1",
                        "agent_id": str(summarizer.id),
                        "node_name": "Summarizer"
                    },
                    {
                        "node_id": "node_2",
                        "agent_id": str(sentiment.id),
                        "node_name": "Sentiment"
                    },
                    {
                        "node_id": "node_3",
                        "agent_id": str(translator.id),
                        "node_name": "Translator"
                    }
                ],
                "edges": [
                    {
                        "from_node": "node_1",
                        "to_node": "node_2",
                        "compatibility_score": 0.87
                    },
                    {
                        "from_node": "node_2",
                        "to_node": "node_3",
                        "compatibility_score": 0.62
                    }
                ],
                "merge_strategy": "authoritative"
            },
            mode=ChainMode.BALANCED,
            estimated_cost_cents=155
        )
        db.add(chain)
        db.commit()
        
        print("✅ Demo setup complete!")
        print("\n📊 Demo Credentials:")
        print("Username: demo")
        print("Password: demo123")
        print("\n💰 Wallet Balance: $50.00")
        print("\n🤖 Agents Created:")
        print("  - n8n Text Summarizer (L2)")
        print("  - Sentiment Analyzer Pro (L3)")
        print("  - n8n Language Translator (L2)")
        print("  - Content Moderator (L1)")
        print("  - Text Formatter (L2)")
        print("  - Keyword Extractor (L3)")
        print("\n🔗 Demo Chain: Text Processing Pipeline")
        print("\n🎯 Ready for investor demo!")
        
    except Exception as e:
        print(f"❌ Error setting up demo: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(setup_demo())
