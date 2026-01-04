from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from app.core.logging import logger

class ProvenanceTracker:
    """Tracks per-field provenance for data transformations"""
    
    def __init__(self):
        self.provenance_records = {}

    def generate_provenance_map(
        self,
        final_output: dict,
        node_results: dict,
        run_id: str
    ) -> dict:
        """Generate provenance map for final output"""
        
        provenance_map = {}
        
        for field_name, field_value in final_output.items():
            provenance = self._trace_field_origin(
                field_name,
                field_value,
                node_results
            )
            
            provenance_map[field_name] = {
                "origin": provenance.get("origin", "unknown"),
                "method": provenance.get("method", "direct"),
                "confidence": provenance.get("confidence", 0.5),
                "transform_chain": provenance.get("transform_chain", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Store for audit
        self.provenance_records[run_id] = provenance_map
        
        return provenance_map

    def _trace_field_origin(
        self,
        field_name: str,
        field_value: Any,
        node_results: dict
    ) -> dict:
        """Trace the origin of a specific field"""
        
        # Check each node result for matching field
        for node_id, result in node_results.items():
            if isinstance(result, dict) and field_name in result:
                if result[field_name] == field_value:
                    return {
                        "origin": node_id,
                        "method": "direct",
                        "confidence": 1.0,
                        "transform_chain": [node_id]
                    }
        
        # Check for transformed fields
        for node_id, result in node_results.items():
            if isinstance(result, dict):
                # Check similar field names
                for result_field, result_value in result.items():
                    if self._are_fields_similar(field_name, result_field):
                        if self._are_values_similar(field_value, result_value):
                            return {
                                "origin": node_id,
                                "method": "transformed",
                                "confidence": 0.8,
                                "transform_chain": [node_id, f"rename_{result_field}_to_{field_name}"]
                            }
        
        # Unknown origin
        return {
            "origin": "synthesized",
            "method": "unknown",
            "confidence": 0.3,
            "transform_chain": []
        }

    def _are_fields_similar(self, field1: str, field2: str) -> bool:
        """Check if two field names are similar"""
        
        field1_lower = field1.lower()
        field2_lower = field2.lower()
        
        # Exact match
        if field1_lower == field2_lower:
            return True
        
        # Common aliases
        aliases = {
            'text': ['content', 'body', 'message'],
            'id': ['_id', 'identifier', 'key'],
            'name': ['title', 'label'],
            'description': ['desc', 'summary', 'abstract']
        }
        
        for key, values in aliases.items():
            if field1_lower == key and field2_lower in values:
                return True
            if field2_lower == key and field1_lower in values:
                return True
        
        # Substring match
        if field1_lower in field2_lower or field2_lower in field1_lower:
            return True
        
        return False

    def _are_values_similar(self, value1: Any, value2: Any) -> bool:
        """Check if two values are similar"""
        
        if value1 == value2:
            return True
        
        # String similarity
        if isinstance(value1, str) and isinstance(value2, str):
            # Substring check
            if value1 in value2 or value2 in value1:
                return True
            
            # Case insensitive match
            if value1.lower() == value2.lower():
                return True
        
        # Numeric similarity
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            if abs(value1 - value2) < 0.001:
                return True
        
        return False

    def add_transform_provenance(
        self,
        run_id: str,
        from_node: str,
        to_node: str,
        transform_method: str,
        input_fields: List[str],
        output_fields: List[str],
        confidence: float = 0.8
    ):
        """Add transformation provenance record"""
        
        key = f"{run_id}_{from_node}_{to_node}"
        
        self.provenance_records[key] = {
            "from_node": from_node,
            "to_node": to_node,
            "transform_method": transform_method,
            "input_fields": input_fields,
            "output_fields": output_fields,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_field_lineage(
        self,
        run_id: str,
        field_name: str
    ) -> List[dict]:
        """Get complete lineage for a field"""
        
        lineage = []
        
        # Get provenance map for run
        provenance_map = self.provenance_records.get(run_id, {})
        
        if field_name in provenance_map:
            field_provenance = provenance_map[field_name]
            
            # Build lineage chain
            for step in field_provenance.get("transform_chain", []):
                lineage.append({
                    "step": step,
                    "confidence": field_provenance.get("confidence", 0.5)
                })
        
        return lineage

    def calculate_confidence(
        self,
        transform_method: str,
        validation_passed: bool,
        similarity_score: float = 0.5
    ) -> float:
        """Calculate confidence score for a transformation"""
        
        base_scores = {
            "deterministic": 0.95,
            "mapping_hint": 0.85,
            "gat": 0.75,
            "llm": 0.60
        }
        
        base = base_scores.get(transform_method, 0.5)
        
        # Adjust for validation
        if not validation_passed:
            base *= 0.7
        
        # Adjust for similarity
        base *= (0.5 + similarity_score * 0.5)
        
        return min(1.0, max(0.0, base))

    def export_provenance_report(self, run_id: str) -> dict:
        """Export complete provenance report for a run"""
        
        report = {
            "run_id": run_id,
            "generated_at": datetime.utcnow().isoformat(),
            "field_provenance": self.provenance_records.get(run_id, {}),
            "transform_records": [],
            "confidence_summary": {}
        }
        
        # Calculate confidence summary
        field_provenance = report["field_provenance"]
        if field_provenance:
            confidences = [p.get("confidence", 0) for p in field_provenance.values()]
            
            report["confidence_summary"] = {
                "average": sum(confidences) / len(confidences) if confidences else 0,
                "min": min(confidences) if confidences else 0,
                "max": max(confidences) if confidences else 0,
                "high_confidence_fields": sum(1 for c in confidences if c > 0.8),
                "low_confidence_fields": sum(1 for c in confidences if c < 0.5)
            }
        
        # Add transform records
        for key, value in self.provenance_records.items():
            if key.startswith(f"{run_id}_"):
                report["transform_records"].append(value)
        
        return report
