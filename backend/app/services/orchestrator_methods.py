"""
Additional methods for AdvancedOrchestrator
Split for file size management
"""

from typing import Dict, List, Any, Tuple
import json
import hashlib
from jsonschema import validate, ValidationError
from app.core.logging import logger

class OrchestratorMethods:
    """Mixin class with orchestrator methods"""
    
    def _compute_compatibility_score(
        self,
        data: Dict,
        schema: Dict
    ) -> Tuple[float, bool, List[str]]:
        """
        Compute compatibility score between data and schema
        
        Returns:
            (score, is_valid, errors)
        """
        errors = []
        score = 0.0
        
        # Check required fields (weight 0.6)
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})
        
        required_score = 1.0
        if required_fields:
            missing = [f for f in required_fields if f not in data]
            if missing:
                errors.append(f"Missing required fields: {missing}")
                required_score = (len(required_fields) - len(missing)) / len(required_fields)
        
        score += required_score * 0.6
        
        # Check type compatibility (weight 0.2)
        type_score = 1.0
        type_matches = 0
        type_total = 0
        
        for field, spec in properties.items():
            if field in data:
                type_total += 1
                expected_type = spec.get('type')
                actual_value = data[field]
                
                if self._check_type_match(actual_value, expected_type):
                    type_matches += 1
                else:
                    errors.append(f"Type mismatch for {field}: expected {expected_type}")
        
        if type_total > 0:
            type_score = type_matches / type_total
        
        score += type_score * 0.2
        
        # Schema validation (weight 0.2)
        try:
            validate(data, schema)
            score += 0.2
            is_valid = True
        except ValidationError as e:
            errors.append(str(e))
            is_valid = False
        
        return score, is_valid and len(errors) == 0, errors

    def _check_type_match(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        
        return True

    async def _try_deterministic_mappings(
        self,
        node: Dict,
        data: Dict,
        schema: Dict
    ) -> Dict:
        """Try deterministic field mappings using aliases"""
        
        best_result = {'success': False, 'score': 0}
        
        # Build mapping candidates
        mappings = self._build_deterministic_mappings(data, schema)
        
        for mapping in mappings:
            transformed = self._apply_mapping(data, mapping)
            score, is_valid, _ = self._compute_compatibility_score(transformed, schema)
            
            if is_valid and score > best_result['score']:
                best_result = {
                    'success': True,
                    'score': score,
                    'transformed': transformed,
                    'mapping': mapping
                }
                
                if score >= 0.95:  # Good enough
                    break
        
        return best_result

    def _build_deterministic_mappings(self, data: Dict, schema: Dict) -> List[Dict]:
        """Build deterministic mapping rules based on field aliases"""
        
        mappings = []
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        # Strategy 1: Direct field matching with aliases
        mapping = {}
        for target_field in properties:
            # Check if field exists directly
            if target_field in data:
                mapping[target_field] = target_field
                continue
            
            # Check aliases
            if hasattr(self, 'field_aliases') and target_field in self.field_aliases:
                for alias in self.field_aliases[target_field]:
                    if alias in data:
                        mapping[alias] = target_field
                        break
        
        if mapping:
            mappings.append({'type': 'rename', 'mapping': mapping})
        
        # Strategy 2: Type coercion
        coercion_map = {}
        for field, spec in properties.items():
            if field in data:
                expected_type = spec.get('type')
                if expected_type and not self._check_type_match(data[field], expected_type):
                    coercion_map[field] = expected_type
        
        if coercion_map:
            mappings.append({'type': 'coerce', 'fields': coercion_map})
        
        # Strategy 3: Field extraction from nested
        extraction_map = {}
        for target_field in required:
            if target_field not in data:
                # Search in nested objects
                for key, value in data.items():
                    if isinstance(value, dict) and target_field in value:
                        extraction_map[f"{key}.{target_field}"] = target_field
                        break
        
        if extraction_map:
            mappings.append({'type': 'extract', 'mapping': extraction_map})
        
        return mappings

    def _apply_mapping(self, data: Dict, mapping: Dict) -> Dict:
        """Apply a mapping rule to transform data"""
        
        result = data.copy()
        
        if mapping['type'] == 'rename':
            # Rename fields
            new_data = {}
            for source, target in mapping['mapping'].items():
                if source in result:
                    new_data[target] = result[source]
                elif target in result:
                    new_data[target] = result[target]
            
            # Keep unmapped fields
            for key, value in result.items():
                if key not in mapping['mapping'] and key not in new_data:
                    new_data[key] = value
            
            result = new_data
        
        elif mapping['type'] == 'coerce':
            # Type coercion
            for field, target_type in mapping['fields'].items():
                if field in result:
                    result[field] = self._coerce_type(result[field], target_type)
        
        elif mapping['type'] == 'extract':
            # Extract from nested
            for source_path, target in mapping['mapping'].items():
                parts = source_path.split('.')
                value = result
                
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        break
                
                if value is not None:
                    result[target] = value
        
        return result

    def _coerce_type(self, value: Any, target_type: str) -> Any:
        """Coerce value to target type"""
        
        try:
            if target_type == 'string':
                return str(value)
            elif target_type == 'integer':
                return int(value)
            elif target_type == 'number':
                return float(value)
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes']
                return bool(value)
            elif target_type == 'array':
                if not isinstance(value, list):
                    return [value]
                return value
            elif target_type == 'object':
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value)
        except:
            pass
        
        return value

    async def _try_gat_mappings(
        self,
        node: Dict,
        data: Dict,
        schema: Dict
    ) -> Dict:
        """Try GAT-suggested mappings"""
        
        # Get fingerprints
        source_fp = hashlib.md5(
            json.dumps(sorted(data.keys())).encode()
        ).hexdigest()
        
        target_fp = hashlib.md5(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest()
        
        # Get GAT suggestions
        suggestions = await self.gat_service.suggest_mappings(
            source_fp,
            target_fp,
            data
        )
        
        best_result = {'success': False, 'score': 0}
        
        for suggestion in suggestions[:5]:  # Try top 5
            recipe = suggestion.get('recipe', [])
            
            # Apply recipe
            transformed = data.copy()
            for step in recipe:
                if step['op'] == 'rename':
                    if step['from'] in transformed:
                        transformed[step['to']] = transformed.pop(step['from'])
                elif step['op'] == 'coerce':
                    if step['field'] in transformed:
                        transformed[step['field']] = self._coerce_type(
                            transformed[step['field']], 
                            step['to']
                        )
                elif step['op'] == 'merge':
                    # Merge multiple fields
                    values = [transformed.get(f, '') for f in step['fields']]
                    transformed[step['to']] = ' '.join(str(v) for v in values if v)
            
            # Validate
            score, is_valid, _ = self._compute_compatibility_score(transformed, schema)
            
            if is_valid and score > best_result['score']:
                best_result = {
                    'success': True,
                    'score': score,
                    'transformed': transformed,
                    'mapping': {
                        'type': 'gat',
                        'recipe': recipe,
                        'confidence': suggestion.get('confidence', 0)
                    }
                }
                
                if score >= 0.9:
                    break
        
        return best_result

    async def _try_llm_synthesis(
        self,
        node: Dict,
        data: Dict,
        schema: Dict
    ) -> Dict:
        """Try LLM synthesis as last resort"""
        
        # Prepare strict prompt
        system_prompt = """You are a JSON-only transformer. INPUT: a JSON object named "source" and a JSON Schema named "target_schema". 
TASK: Produce exactly one JSON object that validates against "target_schema", using only information derivable from "source" or null for missing fields. 
DO NOT invent data (no dates, no names not present in source). 
REPLY: Only the JSON object, nothing else."""
        
        user_prompt = {
            "source": data,
            "target_schema": schema,
            "example_inputs": node.get('example_inputs', [])
        }
        
        # Call LLM with temperature=0
        from app.core.config import settings
        max_retries = settings.MAX_LLM_RETRY
        
        for attempt in range(max_retries):
            try:
                response = await self.llm_gateway.generate_transform(
                    system_prompt,
                    json.dumps(user_prompt),
                    temperature=0.0
                )
                
                # Parse response
                if isinstance(response, str):
                    transformed = json.loads(response)
                else:
                    transformed = response
                
                # Validate
                score, is_valid, errors = self._compute_compatibility_score(
                    transformed, 
                    schema
                )
                
                if is_valid:
                    return {
                        'success': True,
                        'score': score,
                        'transformed': transformed,
                        'tokens_used': len(json.dumps(user_prompt)) // 4  # Rough estimate
                    }
                
                # If validation failed, add error to prompt for retry
                if attempt < max_retries - 1:
                    user_prompt['fix_errors'] = errors
                    
            except Exception as e:
                logger.error(f"LLM synthesis attempt {attempt + 1} failed: {str(e)}")
        
        return {'success': False, 'score': 0}

    # Merge policy implementations
    def _merge_concat_text(self, parents: List[Dict]) -> Dict:
        """Concatenate text fields with deduplication"""
        
        result = {}
        text_parts = []
        
        for parent in parents:
            # Collect text fields
            for key, value in parent.items():
                if 'text' in key.lower() or 'summary' in key.lower():
                    if isinstance(value, str):
                        text_parts.append(value)
                elif key not in result:
                    result[key] = value
        
        # Deduplicate sentences
        sentences = []
        seen = set()
        
        for text in text_parts:
            for sentence in text.split('.'):
                sentence = sentence.strip()
                if sentence and sentence not in seen:
                    sentences.append(sentence)
                    seen.add(sentence)
        
        result['text'] = '. '.join(sentences)
        return result

    def _merge_json_by_key(self, parents: List[Dict]) -> Dict:
        """Merge JSON objects by key, preferring non-null values"""
        
        result = {}
        
        for parent in parents:
            for key, value in parent.items():
                if key not in result or result[key] is None:
                    result[key] = value
                elif isinstance(value, list) and isinstance(result[key], list):
                    # Append lists
                    result[key].extend(value)
                elif isinstance(value, dict) and isinstance(result[key], dict):
                    # Merge dicts recursively
                    result[key] = self._merge_json_by_key([result[key], value])
        
        return result

    def _merge_prefer_high_confidence(self, parents: List[Dict]) -> Dict:
        """Prefer fields from parent with higher confidence"""
        
        # If parents have _confidence metadata
        parents_with_conf = [
            (p, p.get('_confidence', 0.5)) 
            for p in parents
        ]
        
        # Sort by confidence
        parents_with_conf.sort(key=lambda x: x[1], reverse=True)
        
        # Start with highest confidence
        result = parents_with_conf[0][0].copy()
        
        # Fill missing from others
        for parent, _ in parents_with_conf[1:]:
            for key, value in parent.items():
                if key not in result:
                    result[key] = value
        
        return result

    def _merge_authoritative(self, parents: List[Dict]) -> Dict:
        """Use first parent as authoritative, fill gaps from others"""
        
        if not parents:
            return {}
        
        result = parents[0].copy()
        
        for parent in parents[1:]:
            for key, value in parent.items():
                if key not in result or result[key] is None:
                    result[key] = value
        
        return result

    async def _analyze_and_adapt(
        self,
        telemetry: List[Dict],
        validation_reports: Dict
    ):
        """Analyze execution telemetry and adapt for future runs"""
        
        # Track method usage
        method_counts = {'direct': 0, 'deterministic': 0, 'gat': 0, 'llm': 0}
        failed_mappings = []
        
        for entry in telemetry:
            method = entry.get('method')
            if method:
                method_counts[method] += 1
            
            # Track failures requiring LLM
            if method == 'llm':
                failed_mappings.append({
                    'node_id': entry['node_id'],
                    'tokens_used': entry.get('tokens', 0)
                })
        
        # Calculate metrics
        total_executions = sum(method_counts.values())
        if total_executions > 0:
            llm_percentage = (method_counts['llm'] / total_executions) * 100
            
            # Alert if LLM usage is high
            if llm_percentage > 5:
                logger.warning(
                    f"High LLM usage: {llm_percentage:.1f}% of transforms. "
                    f"Consider adding deterministic mappings for: {failed_mappings}"
                )
            
            # Log metrics
            logger.info(
                f"Transform methods used - Direct: {method_counts['direct']}, "
                f"Deterministic: {method_counts['deterministic']}, "
                f"GAT: {method_counts['gat']}, LLM: {method_counts['llm']}"
            )
