import os
import json
import re
from typing import Dict, Optional, Any, List
from datetime import datetime
import google.generativeai as genai
from app.core.logging import logger

class LLMGateway:
    """Centralized LLM gateway with Gemini integration, budget control, and safety measures"""
    
    def __init__(self):
        # Initialize Gemini with the provided API key
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCl9AJ7v7r49_AotBUDWVq3VpXVqwnEYwI")
        genai.configure(api_key=self.api_key)
        
        # Model configuration
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        # Budget tracking
        self.daily_token_limit = 100000
        self.daily_tokens_used = 0
        self.last_reset = datetime.utcnow()
        
        # Cost estimation (per 1000 tokens)
        self.input_token_cost = 0.00025  # $0.25 per million
        self.output_token_cost = 0.00125  # $1.25 per million

    async def transform(
        self,
        input_data: dict,
        target_schema: dict,
        run_id: str,
        examples: List[dict] = None
    ) -> Optional[dict]:
        """Transform data to match target schema using LLM"""
        
        try:
            # Check budget
            if not await self._check_budget():
                logger.warning("LLM daily token limit exceeded")
                return None
            
            # Prepare prompt
            prompt = self._build_transform_prompt(input_data, target_schema, examples)
            
            # Redact PII before sending
            prompt = self._redact_pii(prompt)
            
            # Call Gemini
            response = await self._call_gemini(prompt)
            
            if not response:
                return None
            
            # Extract JSON from response
            result = self._extract_json(response)
            
            if not result:
                return None
            
            # Validate against schema
            if await self._validate_schema(result, target_schema):
                return result
            
            # Try cleanup if validation fails
            cleaned = await self._cleanup_json(result, target_schema)
            if cleaned and await self._validate_schema(cleaned, target_schema):
                return cleaned
            
            return None
            
        except Exception as e:
            logger.error(f"LLM transform failed: {str(e)}")
            return None

    async def generate_mapping_suggestion(
        self,
        source_schema: dict,
        target_schema: dict,
        source_example: dict = None,
        target_example: dict = None
    ) -> Optional[dict]:
        """Generate mapping recipe suggestion"""
        
        prompt = self._build_mapping_prompt(
            source_schema, target_schema, 
            source_example, target_example
        )
        
        response = await self._call_gemini(prompt)
        
        if response:
            return self._extract_json(response)
        
        return None

    async def synthesize_merge(
        self,
        branch_outputs: List[dict],
        target_schema: dict,
        provenance_data: dict = None
    ) -> Optional[dict]:
        """Synthesize merged output from multiple branches"""
        
        prompt = self._build_merge_prompt(
            branch_outputs, target_schema, provenance_data
        )
        
        response = await self._call_gemini(prompt)
        
        if response:
            result = self._extract_json(response)
            if result and await self._validate_schema(result, target_schema):
                return result
        
        return None

    async def generate_verification_fixes(
        self,
        test_results: List[dict],
        output_schema: dict
    ) -> List[str]:
        """Generate actionable fixes for verification failures"""
        
        prompt = f"""You are a technical verifier assistant.
Input: List of 3 sample agent responses and the declared output JSON Schema.
Output: Up to 5 precise, actionable fixes the agent owner can implement to reach L2/L3 verification. Use bullet items, each one line maximum.

Test Results: {json.dumps(test_results, indent=2)}
Expected Schema: {json.dumps(output_schema, indent=2)}

Return bullet points only."""
        
        response = await self._call_gemini(prompt)
        
        if response:
            # Parse bullet points
            fixes = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    fixes.append(line[1:].strip())
            return fixes[:5]
        
        return []

    def _build_transform_prompt(
        self,
        input_data: dict,
        target_schema: dict,
        examples: List[dict] = None
    ) -> str:
        """Build transformation prompt"""
        
        system_prompt = """You are a JSON synthesizer. Given input_json and target_schema (JSON Schema), 
produce a single JSON object that exactly matches the schema. Only output the JSON object and nothing else. 
If a field cannot be produced, set it to null."""
        
        user_prompt = {
            "input_json": input_data,
            "target_schema": target_schema,
            "examples": examples or []
        }
        
        return f"{system_prompt}\n\nUser: {json.dumps(user_prompt, indent=2)}\n\nReturn only JSON:"

    def _build_mapping_prompt(
        self,
        source_schema: dict,
        target_schema: dict,
        source_example: dict = None,
        target_example: dict = None
    ) -> str:
        """Build mapping suggestion prompt"""
        
        return f"""You are a deterministic mapping generator.
Input: source JSON schema and example, target JSON schema and example.
Output: A JSON mapping recipe consisting only of atomic operations (rename, coerce, concat, default, truncate).
Return JSON only.

Source Schema: {json.dumps(source_schema, indent=2)}
Source Example: {json.dumps(source_example, indent=2) if source_example else 'None'}
Target Schema: {json.dumps(target_schema, indent=2)}
Target Example: {json.dumps(target_example, indent=2) if target_example else 'None'}

Return a JSON recipe array only:"""

    def _build_merge_prompt(
        self,
        branch_outputs: List[dict],
        target_schema: dict,
        provenance_data: dict = None
    ) -> str:
        """Build merge synthesis prompt"""
        
        return f"""You are a JSON synthesizer. Given branch outputs and a final target schema, 
create a final merged JSON that conforms to the schema. Also output a provenance_map mapping each field to origin and confidence. 
Output JSON only.

Branch Outputs: {json.dumps(branch_outputs, indent=2)}
Target Schema: {json.dumps(target_schema, indent=2)}
Provenance Data: {json.dumps(provenance_data, indent=2) if provenance_data else 'None'}

Return only the merged JSON:"""

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API with rate limiting and error handling"""
        
        try:
            # Estimate tokens (rough approximation)
            estimated_tokens = len(prompt.split()) * 1.3
            
            # Check budget
            if self.daily_tokens_used + estimated_tokens > self.daily_token_limit:
                logger.warning("Would exceed daily token limit")
                return None
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Track usage
            self.daily_tokens_used += estimated_tokens
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            return None

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response"""
        
        # Try to find JSON block
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try parsing entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try removing markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return None

    def _redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Credit card numbers
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', text)
        
        return text

    async def _validate_schema(self, data: dict, schema: dict) -> bool:
        """Validate data against JSON schema"""
        
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError:
            return False

    async def _cleanup_json(self, data: dict, schema: dict) -> Optional[dict]:
        """Attempt to cleanup invalid JSON"""
        
        try:
            cleaned = {}
            properties = schema.get('properties', {})
            
            for key, value_schema in properties.items():
                if key in data:
                    value = data[key]
                    
                    # Type corrections
                    expected_type = value_schema.get('type')
                    
                    if expected_type == 'string' and not isinstance(value, str):
                        cleaned[key] = str(value)
                    elif expected_type == 'number' and isinstance(value, str):
                        try:
                            cleaned[key] = float(value)
                        except:
                            cleaned[key] = None
                    elif expected_type == 'integer' and isinstance(value, str):
                        try:
                            cleaned[key] = int(value)
                        except:
                            cleaned[key] = None
                    else:
                        cleaned[key] = value
                
                # Add required fields with null
                elif key in schema.get('required', []):
                    cleaned[key] = None
            
            return cleaned
            
        except Exception as e:
            logger.error(f"JSON cleanup failed: {str(e)}")
            return None

    async def _check_budget(self) -> bool:
        """Check if within budget limits"""
        
        # Reset daily counter if needed
        now = datetime.utcnow()
        if (now - self.last_reset).days >= 1:
            self.daily_tokens_used = 0
            self.last_reset = now
        
        return self.daily_tokens_used < self.daily_token_limit

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> int:
        """Estimate cost in cents"""
        
        input_cost = (input_tokens / 1000) * self.input_token_cost * 100
        output_cost = (output_tokens / 1000) * self.output_token_cost * 100
        
        return int(input_cost + output_cost)
