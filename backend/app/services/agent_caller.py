import hashlib
import hmac
import httpx
import json
from typing import Dict, Optional, Any
from datetime import datetime
import asyncio
from jose import jwt

from app.models.agent import Agent, AgentType, AuthType
from app.core.logging import logger

class AgentCaller:
    """Handles agent invocations with n8n webhook compatibility and A2A compliance"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.max_retries = 2
        self.retry_delay = 1.0

    async def call_agent(
        self,
        agent: Agent,
        payload: dict,
        idempotency_key: str,
        trace_id: Optional[str] = None
    ) -> dict:
        """Call an agent with proper authentication and retry logic"""
        
        # Add A2A headers
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": idempotency_key,
            "X-Agent-Id": str(agent.id),
            "User-Agent": "GPTGram/1.0 A2A-Client"
        }
        
        if trace_id:
            headers["X-Trace-Id"] = trace_id
        
        # Add authentication
        auth_config = agent.auth
        if auth_config.get("type") == AuthType.HMAC:
            headers["X-HMAC-Signature"] = await self._generate_hmac(
                payload,
                auth_config.get("secret_name")
            )
        elif auth_config.get("type") == AuthType.JWT:
            headers["Authorization"] = f"Bearer {await self._generate_jwt(agent.id)}"
        
        # Handle n8n specific requirements
        if agent.type == AgentType.N8N:
            payload = await self._prepare_n8n_payload(payload, agent)
        
        # Attempt call with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(
                    agent.endpoint_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update agent metrics
                    await self._update_agent_metrics(agent, True, response.elapsed.total_seconds())
                    
                    # Validate A2A response format
                    if agent.type != AgentType.N8N:
                        result = await self._validate_a2a_response(result)
                    
                    return result
                
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    
            except httpx.TimeoutException:
                last_error = "Request timeout"
            except Exception as e:
                last_error = str(e)
            
            # Wait before retry
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed
        await self._update_agent_metrics(agent, False, 30.0)
        raise Exception(f"Agent call failed after {self.max_retries + 1} attempts: {last_error}")

    async def verify_agent(self, agent: Agent) -> dict:
        """Perform verification calls to test agent"""
        
        results = {
            "verification_level": "unverified",
            "tests": [],
            "recommendations": []
        }
        
        # Run 3 test calls
        test_payloads = [
            agent.sample_request or {},
            agent.sample_request or {},
            agent.sample_request or {}
        ]
        
        successful_calls = 0
        schema_matches = 0
        total_latency = 0
        
        for i, payload in enumerate(test_payloads):
            test_result = {
                "test_number": i + 1,
                "status": "failed",
                "latency_ms": None,
                "schema_valid": False,
                "errors": []
            }
            
            try:
                start_time = datetime.utcnow()
                response = await self.call_agent(
                    agent,
                    payload,
                    f"verify_{agent.id}_{i}",
                    f"verify_{agent.id}"
                )
                latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                test_result["status"] = "success"
                test_result["latency_ms"] = int(latency)
                total_latency += latency
                successful_calls += 1
                
                # Validate output schema
                if await self._validate_schema(response, agent.output_schema):
                    test_result["schema_valid"] = True
                    schema_matches += 1
                else:
                    test_result["errors"].append("Output schema mismatch")
                
            except Exception as e:
                test_result["errors"].append(str(e))
            
            results["tests"].append(test_result)
        
        # Calculate verification score
        if successful_calls == 0:
            score = 0
        else:
            schema_score = (schema_matches / 3) * 0.6
            stability_score = (successful_calls / 3) * 0.25
            latency_score = max(0, 1 - (total_latency / successful_calls / 5000)) * 0.15
            score = schema_score + stability_score + latency_score
        
        # Determine verification level
        if score >= 0.92:
            results["verification_level"] = "L3"
        elif score >= 0.75:
            results["verification_level"] = "L2"
        elif score >= 0.5:
            results["verification_level"] = "L1"
        
        # Generate recommendations
        if schema_matches < 3:
            results["recommendations"].append(
                "Ensure output consistently matches declared JSON schema"
            )
        if successful_calls < 3:
            results["recommendations"].append(
                "Improve endpoint stability and error handling"
            )
        if total_latency > 0 and (total_latency / successful_calls) > 2000:
            results["recommendations"].append(
                "Optimize response time (currently averaging > 2s)"
            )
        
        return results

    async def _prepare_n8n_payload(self, payload: dict, agent: Agent) -> dict:
        """Prepare payload for n8n webhook format"""
        
        # n8n expects specific structure
        n8n_payload = {
            "body": payload,
            "headers": {
                "content-type": "application/json",
                "x-agent-id": str(agent.id)
            },
            "query": {}
        }
        
        # Add any n8n specific fields from agent metadata
        if agent.capability_manifest:
            n8n_config = agent.capability_manifest.get("n8n", {})
            if n8n_config:
                n8n_payload.update(n8n_config)
        
        return n8n_payload

    async def _generate_hmac(self, payload: dict, secret_name: str) -> str:
        """Generate HMAC signature for n8n webhook authentication"""
        
        # Get secret from environment or vault
        secret = await self._get_secret(secret_name)
        
        # Create signature
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    async def _generate_jwt(self, agent_id: str) -> str:
        """Generate JWT token for authentication"""
        
        # Get JWT secret
        secret = await self._get_secret("JWT_SECRET")
        
        # Create token
        payload = {
            "agent_id": str(agent_id),
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow().timestamp() + 3600)  # 1 hour expiry
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token

    async def _get_secret(self, secret_name: str) -> str:
        """Get secret from vault or environment"""
        
        # In production, use proper secret management
        # For now, use environment variables
        import os
        return os.getenv(secret_name, "default_secret")

    async def _validate_a2a_response(self, response: dict) -> dict:
        """Validate A2A compliant response format"""
        
        # A2A responses should have specific structure
        if "data" in response:
            return response["data"]
        
        # If not A2A format, return as-is
        return response

    async def _validate_schema(self, data: dict, schema: dict) -> bool:
        """Validate data against JSON schema"""
        
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError:
            return False

    async def _update_agent_metrics(self, agent: Agent, success: bool, latency: float):
        """Update agent performance metrics"""
        
        metrics = agent.metrics_cache or {}
        
        # Update success rate
        total_calls = metrics.get("call_volume", 0) + 1
        successful_calls = metrics.get("successful_calls", 0) + (1 if success else 0)
        metrics["success_rate"] = successful_calls / total_calls
        metrics["call_volume"] = total_calls
        metrics["successful_calls"] = successful_calls
        
        # Update average latency
        avg_latency = metrics.get("avg_latency_ms", 0)
        metrics["avg_latency_ms"] = (
            (avg_latency * (total_calls - 1) + latency * 1000) / total_calls
        )
        
        # Update last called timestamp
        agent.last_called_at = datetime.utcnow()
        agent.metrics_cache = metrics

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
