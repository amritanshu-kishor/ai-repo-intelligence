"""
Repository Intelligence — AI orchestration entrypoint (Phase 1 + Phase 2).

Pipeline order:
  1. User Query
  2. Intent Classification        → IntentResult
  3. Context Retrieval            → ContextResult (graph + impact reasoning)
  4. Prompt Builder               → PromptResult
  5. AI Provider Call             → LLMResult
  6. Response Processing          → PipelineResponse
  7. Visualization Context        → VisualizationContext (unified frontend payload)
  8. Final Structured Output      (PipelineResponse with visualization attached)

Future: expose run_pipeline() from Flask/FastAPI routes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.ai_provider import complete as call_ai_provider
from ai.context_builder import retrieve as retrieve_context
from ai.contracts import PipelineResponse, new_request_id
from ai.intent_classifier import classify as classify_intent
from ai.prompt_engine import build as build_prompt
from ai.response_processor import process as process_response
from ai.visualization_context import build as build_visualization


def run_pipeline(
    query: str,
    *,
    request_id: str | None = None,
    repository_id: str | None = None,
) -> PipelineResponse:
    """Each step consumes structured JSON contracts from the prior stage."""
    rid = request_id or new_request_id()

    # 1. User Query
    user_query = (query or "").strip()
    if not user_query:
        raise ValueError("Query must not be empty")

    # 2. Intent Classification
    intent_result = classify_intent(user_query, request_id=rid)

    # 3. Context Retrieval (includes Phase 2 graph_reasoner + impact_analyzer)
    context_result = retrieve_context(intent_result, repository_id=repository_id)

    # 4. Prompt Builder
    prompt_result = build_prompt(intent_result, context_result)

    # 5. AI Provider Call
    llm_result = call_ai_provider(prompt_result)

    # 6. Response Processing
    final_output = process_response(intent_result, context_result, llm_result)

    # 7. Visualization Context — merges AI + graph + impact for frontend
    visualization = build_visualization(intent_result, context_result, final_output)
    final_output["visualization"] = visualization

    # 8. Final Structured Output
    if final_output.get("provenance"):
        final_output["provenance"]["stages"].append("visualization")

    return final_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Repo AI orchestration (local)")
    parser.add_argument("query", nargs="?", help="Natural language question about the repo")
    parser.add_argument("--json", action="store_true", help="Print full pipeline JSON")
    parser.add_argument("--viz-only", action="store_true", help="Print visualization payload only")
    parser.add_argument("--repo-id", default=None, help="Repository identifier for context APIs")
    args = parser.parse_args()

    query = args.query or input("Ask about the repository: ").strip()
    if not query:
        print("No query provided.", file=sys.stderr)
        sys.exit(1)

    result = run_pipeline(query, repository_id=args.repo_id)

    if args.viz_only:
        print(json.dumps(result.get("visualization", {}), indent=2))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        intel = result.get("intelligence", {})
        print("\n--- Summary ---\n")
        print(intel.get("summary") or result.get("answer", ""))
        print(f"\n--- Risk: {intel.get('risk_level', 'unknown')} (confidence {intel.get('confidence_score', 0)}) ---")
        impact = result.get("impact", {})
        print(f"Severity: {impact.get('impact_severity')} | Propagation depth: {impact.get('propagation_depth')}")
        affected = result.get("graph", {}).get("affected_nodes", [])
        if affected:
            print("\n--- Affected nodes ---")
            for node in affected:
                print(f"  - [{node.get('relation')}] {node.get('label', node.get('id'))}")
        explain = result.get("graph", {}).get("traversal_explain", [])
        if explain:
            print("\n--- Graph debug ---")
            for line in explain:
                print(f"  • {line}")


if __name__ == "__main__":
    main()
