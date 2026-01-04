import json
import hashlib
from typing import Dict, Optional, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import MappingHint, TransformRecord, ChainRun
from app.models.transform import TransformMethod
from app.services.gat_service import GATService
from app.services.llm_gateway import LLMGateway
from app.core.logging import logger

class TransformPipeline:
    """Handles data transformation between agents with deterministic -> GAT -> LLM fallback"""
    
    def __init__(
        self,
        db: AsyncSession,
        gat_service: Optional[GATService] = None,
        llm_gateway: Optional[LLMGateway] = None
    ):
        self.db = db
        self.gat_service = gat_service
        self.llm_gateway = llm_gateway

    async def transform(
        self,
        input_data: dict,
        target_schema: dict,
        chain_run: ChainRun,
        source_schema: Optional[dict] = None,
        from_node: str = "",
        to_node: str = ""
    ) -> dict:
        """Main transformation pipeline"""
        
        # Calculate schema fingerprints
        source_fp = self._calculate_fingerprint(source_schema or self._infer_schema(input_data))
        target_fp = self._calculate_fingerprint(target_schema)
        
        # 1. Try deterministic mapping first
        result = await self._try_deterministic(input_data, target_schema)
        if result:
            await self._record_transform(
                chain_run.id, from_node, to_node,
                TransformMethod.DETERMINISTIC, input_data, result
            )
            return result
        
        # 2. Try cached mapping hints
        mapping_hint = await self._get_mapping_hint(source_fp, target_fp)
        if mapping_hint:
            result = await self._apply_mapping_hint(input_data, mapping_hint)
            if result and await self._validate_output(result, target_schema):
                await self._record_transform(
                    chain_run.id, from_node, to_node,
                    TransformMethod.MAPPING_HINT, input_data, result,
                    recipe_id=mapping_hint.id
                )
                mapping_hint.success_count += 1
                await self.db.commit()
                return result
            else:
                mapping_hint.fail_count += 1
                await self.db.commit()
        
        # 3. Try GAT suggestions if enabled
        if chain_run.auto_apply_gat and self.gat_service:
            gat_suggestions = await self.gat_service.suggest_mappings(
                source_fp, target_fp, input_data
            )
            
            for suggestion in gat_suggestions:
                result = await self._apply_recipe(input_data, suggestion['recipe'])
                if result and await self._validate_output(result, target_schema):
                    # Cache successful GAT suggestion
                    new_hint = MappingHint(
                        source_schema_fp=source_fp,
                        target_schema_fp=target_fp,
                        recipe=suggestion['recipe'],
                        gat_confidence=suggestion.get('confidence'),
                        attention_trace=suggestion.get('attention_trace')
                    )
                    self.db.add(new_hint)
                    await self.db.commit()
                    
                    await self._record_transform(
                        chain_run.id, from_node, to_node,
                        TransformMethod.GAT, input_data, result,
                        recipe_id=new_hint.id
                    )
                    return result
        
        # 4. LLM fallback if enabled and budget allows
        if chain_run.allow_llm and self.llm_gateway:
            if await self._check_llm_budget(chain_run):
                result = await self.llm_gateway.transform(
                    input_data, target_schema, chain_run.id
                )
                if result and await self._validate_output(result, target_schema):
                    await self._record_transform(
                        chain_run.id, from_node, to_node,
                        TransformMethod.LLM, input_data, result
                    )
                    return result
        
        # Failed all methods
        raise ValueError(f"Could not transform data to match target schema")

    async def _try_deterministic(self, input_data: dict, target_schema: dict) -> Optional[dict]:
        """Apply deterministic transformation rules"""
        
        result = {}
        target_props = target_schema.get('properties', {})
        
        for field_name, field_schema in target_props.items():
            # Exact match
            if field_name in input_data:
                result[field_name] = input_data[field_name]
                continue
            
            # Case-insensitive match
            for input_key, input_value in input_data.items():
                if input_key.lower() == field_name.lower():
                    result[field_name] = input_value
                    break
            
            # Common renames
            rename_map = {
                'text': ['document', 'body', 'content', 'message'],
                'summary': ['abstract', 'description', 'overview'],
                'title': ['name', 'heading', 'subject'],
                'id': ['_id', 'identifier', 'key']
            }
            
            if field_name in rename_map:
                for alt_name in rename_map[field_name]:
                    if alt_name in input_data:
                        result[field_name] = input_data[alt_name]
                        break
            
            # Type coercions
            if field_name in result:
                result[field_name] = await self._coerce_type(
                    result[field_name], field_schema
                )
        
        # Check if we have all required fields
        required_fields = target_schema.get('required', [])
        if all(field in result for field in required_fields):
            return result
        
        return None

    async def _coerce_type(self, value: Any, field_schema: dict) -> Any:
        """Coerce value to match field schema type"""
        
        target_type = field_schema.get('type')
        
        if target_type == 'string':
            if not isinstance(value, str):
                return str(value)
        elif target_type == 'number':
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    pass
        elif target_type == 'integer':
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    pass
        elif target_type == 'array':
            if not isinstance(value, list):
                return [value]
        elif target_type == 'boolean':
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes']
        
        return value

    async def _get_mapping_hint(self, source_fp: str, target_fp: str) -> Optional[MappingHint]:
        """Get cached mapping hint"""
        
        result = await self.db.execute(
            select(MappingHint).where(
                MappingHint.source_schema_fp == source_fp,
                MappingHint.target_schema_fp == target_fp
            ).order_by(MappingHint.success_count.desc())
        )
        return result.scalar_one_or_none()

    async def _apply_mapping_hint(self, input_data: dict, mapping_hint: MappingHint) -> Optional[dict]:
        """Apply a mapping hint recipe"""
        
        return await self._apply_recipe(input_data, mapping_hint.recipe)

    async def _apply_recipe(self, input_data: dict, recipe: List[dict]) -> Optional[dict]:
        """Apply a transformation recipe"""
        
        try:
            result = input_data.copy()
            
            for operation in recipe:
                op_type = operation.get('op')
                
                if op_type == 'rename':
                    if operation['from'] in result:
                        result[operation['to']] = result.pop(operation['from'])
                
                elif op_type == 'coerce':
                    field = operation['field']
                    if field in result:
                        to_type = operation['to']
                        if to_type == 'integer':
                            result[field] = int(result[field])
                        elif to_type == 'float':
                            result[field] = float(result[field])
                        elif to_type == 'string':
                            result[field] = str(result[field])
                
                elif op_type == 'concat':
                    fields = operation['fields']
                    separator = operation.get('separator', ' ')
                    values = [str(result.get(f, '')) for f in fields if f in result]
                    if values:
                        result[operation['into']] = separator.join(values)
                
                elif op_type == 'truncate':
                    field = operation['field']
                    max_chars = operation.get('max_chars', 1000)
                    if field in result and isinstance(result[field], str):
                        result[field] = result[field][:max_chars]
                
                elif op_type == 'default':
                    field = operation['field']
                    if field not in result or result[field] is None:
                        result[field] = operation['value']
                
                elif op_type == 'pick':
                    fields = operation.get('fields', [])
                    result = {k: v for k, v in result.items() if k in fields}
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply recipe: {str(e)}")
            return None

    async def _validate_output(self, data: dict, schema: dict) -> bool:
        """Validate output against schema"""
        
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError:
            return False

    async def _check_llm_budget(self, chain_run: ChainRun) -> bool:
        """Check if LLM usage is within budget"""
        
        # Check run budget
        if chain_run.budget_cents:
            spent = await self._calculate_spent(chain_run.id)
            estimated_llm_cost = 50  # Estimate 50 cents per LLM call
            if spent + estimated_llm_cost > chain_run.budget_cents:
                return False
        
        return True

    async def _calculate_spent(self, run_id: str) -> int:
        """Calculate spent amount for run"""
        
        result = await self.db.execute(
            select(TransformRecord).where(
                TransformRecord.run_id == run_id
            )
        )
        transforms = result.scalars().all()
        
        total = 0
        for transform in transforms:
            total += transform.cost_cents or 0
        
        return total

    async def _record_transform(
        self,
        run_id: str,
        from_node: str,
        to_node: str,
        method: TransformMethod,
        input_data: dict,
        output_data: dict,
        recipe_id: Optional[str] = None
    ):
        """Record transformation in database"""
        
        transform = TransformRecord(
            run_id=run_id,
            from_node=from_node,
            to_node=to_node,
            method=method,
            recipe_id=recipe_id,
            input_data=input_data,
            output_data=output_data,
            validated=True,
            cost_cents=0 if method != TransformMethod.LLM else 50  # Estimate
        )
        self.db.add(transform)
        await self.db.commit()

    def _calculate_fingerprint(self, schema: dict) -> str:
        """Calculate fingerprint for schema"""
        
        # Canonicalize schema
        canonical = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _infer_schema(self, data: dict) -> dict:
        """Infer basic schema from data"""
        
        properties = {}
        for key, value in data.items():
            if isinstance(value, str):
                properties[key] = {"type": "string"}
            elif isinstance(value, int):
                properties[key] = {"type": "integer"}
            elif isinstance(value, float):
                properties[key] = {"type": "number"}
            elif isinstance(value, bool):
                properties[key] = {"type": "boolean"}
            elif isinstance(value, list):
                properties[key] = {"type": "array"}
            elif isinstance(value, dict):
                properties[key] = {"type": "object"}
        
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties.keys())
        }
