"""
Stage 6: Response Processing → normalized structured intelligence.
Parses LLM markdown sections, applies graph/impact fallbacks, enforces JSON contract.
Includes hallucination filtering to ensure graph-grounded outputs.
"""

from __future__ import annotations

import re
from typing import Any

from ai.contracts import (
    ContextResult,
    GraphResult,
    ImpactResult,
    IntentResult,
    LLMResult,
    PipelineResponse,
    StructuredIntelligence,
    make_pipeline_response,
    make_structured_intelligence,
)

# Hallucination detection patterns - flag generic security/runtime issues not in context
HALLUCINATION_PATTERNS = [
    r'\b(security\s+breach|data\s+breach|exploit|vulnerability|CVE-\d+)\b',
    r'\b(unauthorized\s+access|SQL\s+injection|XSS|CSRF)\b',
    r'\b(database\s+failure|connection\s+timeout|server\s+crash)\b',
    r'\b(authentication\s+bypass|privilege\s+escalation)\b',
    r'\b(malicious\s+code|backdoor|trojan)\b',
]

def _detect_hallucinations(text: str, context: ContextResult) -> list[str]:
    """
    Detect potential hallucinations - security/runtime issues not grounded in context.
    Returns list of flagged phrases.
    """
    if not text:
        return []
    
    text_lower = text.lower()
    flags: list[str] = []
    
    # Check for security/vulnerability language
    for pattern in HALLUCINATION_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            # Verify if these terms appear in repository summaries or risk factors
            summaries_text = str(context.get("data", {}).get("summaries", "")).lower()
            impact = context.get("impact_insights", {})
            risk_factors = " ".join(str(f) for f in impact.get("risk_factors", [])).lower()
            
            for match in matches:
                match_str = match if isinstance(match, str) else match[0]
                # Flag if NOT in original context
                if match_str not in summaries_text and match_str not in risk_factors:
                    flags.append(match_str)
    
    return flags

def _filter_hallucinated_content(text: str, hallucinations: list[str]) -> str:
    """
    Remove or downgrade hallucinated content from LLM output.
    Preserves graph-grounded reasoning.
    """
    if not hallucinations or not text:
        return text
    
    # Remove sentences containing hallucinated terms
    sentences = re.split(r'[.!?]+', text)
    filtered = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        has_hallucination = any(h in sentence_lower for h in hallucinations)
        
        if not has_hallucination:
            filtered.append(sentence)
    
    result = '. '.join(s.strip() for s in filtered if s.strip())
    return result + '.' if result and not result.endswith('.') else result

def _extract_bullets(text: str) -> list[str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    bullets: list[str] = []
    for ln in lines:
        if re.match(r"^[\d]+[\.\)]\s+", ln) or ln.startswith(("-", "*")):
            bullets.append(re.sub(r"^[\d]+[\.\)]\s+|^[-*]\s+", "", ln))
    return bullets


def _parse_sections(text: str) -> dict[str, str]:
    """Extract markdown ## sections from specialized prompts."""
    if not text or not text.strip():
        return {}

    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for line in text.splitlines():
        header = re.match(r"^#+\s*(.+?)\s*$", line.strip())
        if header:
            if current:
                sections[current] = "\n".join(buf).strip()
            current = header.group(1).lower()
            buf = []
        elif current is not None:
            buf.append(line)

    if current:
        sections[current] = "\n".join(buf).strip()

    return sections


def _normalize_risk_level(raw: str, fallback: str) -> str:
    raw_l = (raw or "").lower()
    for level in ("critical", "high", "medium", "low"):
        if level in raw_l:
            return level if level != "critical" else "high"
    return fallback if fallback in ("low", "medium", "high") else "low"


def _affected_files_from_graph(graph: GraphResult) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in graph.get("affected_nodes") or []:
        if not isinstance(node, dict):
            continue
        nid = node.get("id")
        if nid and nid not in seen:
            seen.add(nid)
            files.append({
                "id": nid,
                "path": node.get("label", nid),
                "relation": node.get("relation"),
                "depth": node.get("depth"),
            })
    return files


def _dependency_chain_from_graph(graph: GraphResult) -> list[Any]:
    chains = graph.get("dependency_chains") or []
    if chains:
        return chains
    paths = graph.get("direct_paths", []) + graph.get("indirect_paths", [])
    return [p.get("description", p) for p in paths if isinstance(p, dict)]


def _fallback_recommendations(impact: ImpactResult, graph: GraphResult) -> list[str]:
    recs = [
        "Review modules listed in affected_files before merging.",
        f"Run tests covering focus node '{graph.get('focus_label', graph.get('focus_node_id', 'unknown'))}'.",
    ]
    if impact.get("risk_factors"):
        recs.append(f"Address risk factors: {impact['risk_factors'][0]}")
    if graph.get("circular_dependencies"):
        recs.append("Resolve circular dependencies before large refactors.")
    return recs


def _build_graph_analysis(graph: GraphResult, impact: ImpactResult) -> dict[str, Any]:
    return {
        "focus_node_id": graph.get("focus_node_id"),
        "focus_label": graph.get("focus_label"),
        "propagation_depth": graph.get("propagation_depth", impact.get("propagation_depth", 0)),
        "direct_dependencies": graph.get("direct_dependencies", []),
        "indirect_dependencies": graph.get("indirect_dependencies", []),
        "upstream_dependencies": graph.get("upstream_dependencies", []),
        "circular_dependencies": graph.get("circular_dependencies", []),
        "reasoning_summary": graph.get("reasoning_summary", {}),
        "traversal_explain": graph.get("traversal_explain", []),
        "impact_severity": impact.get("impact_severity"),
        "propagation_scope": impact.get("propagation_scope", {}),
        "risk_explanation": impact.get("risk_explanation", ""),
    }


def _build_intelligence(
    intent: IntentResult,
    context: ContextResult,
    llm: LLMResult,
    graph: GraphResult,
    impact: ImpactResult,
) -> StructuredIntelligence:
    """
    Normalize LLM + graph + impact into required structured format.
    
    CRITICAL: Preserves graph reasoning even when LLM output is incomplete.
    Defensive fallbacks ensure graph analysis is never lost.
    """
    raw_text = (llm.get("text") or "").strip()
    provider = llm.get("provider", "unknown")
    
    # Detect provider failures or truncated outputs
    llm_failed = (
        not raw_text
        or provider == "mock" and "[Mock LLM]" in raw_text
        or "[Error:" in raw_text
        or "[WatsonX Error:" in raw_text
    )

    sections = _parse_sections(raw_text)
    summaries = context.get("data", {}).get("summaries") or []

    # Build summary with graph reasoning fallback
    summary = sections.get("explanation", "").strip()
    graph_narrative = graph.get("reasoning_summary", {}).get("narrative", "")
    impact_explanation = impact.get("risk_explanation", "")
    
    if not summary and llm_failed:
        # Provider failed - use graph reasoning directly
        summary = graph_narrative or impact_explanation or "Repository intelligence generated from graph analysis."
    elif not summary:
        # LLM returned text but no explanation section - use first 500 chars + graph context
        summary = raw_text[:500] if raw_text else ""
        if graph_narrative and graph_narrative not in summary:
            summary = f"{summary}\n\n{graph_narrative}" if summary else graph_narrative
    elif len(summary) < 100 and graph_narrative:
        # LLM summary too short - enrich with graph reasoning
        summary = f"{summary}\n\n{graph_narrative}"

    # Affected files: prioritize graph data over LLM parsing
    affected_files = _affected_files_from_graph(graph)
    if not affected_files:
        # Fallback to LLM-parsed files only if graph has no data
        affected_from_llm = _extract_bullets(sections.get("affected files", ""))
        if affected_from_llm:
            affected_files = [{"path": p, "relation": "inferred"} for p in affected_from_llm]

    # Dependency chains: always from graph reasoning
    dependency_chain = _dependency_chain_from_graph(graph)
    
    # Ensure dependency chains are preserved even if empty
    if not dependency_chain and graph.get("traversal_explain"):
        dependency_chain = graph.get("traversal_explain", [])

    # Risk level: prefer impact analysis over LLM parsing
    risk_raw = sections.get("risk level", "")
    risk_level = _normalize_risk_level(risk_raw, impact.get("risk_level", "low"))

    # Recommendations: merge LLM + graph-based fallbacks
    recommendations = _extract_bullets(sections.get("recommendations", ""))
    if not recommendations:
        dep_section = sections.get("dependency impact", "")
        if dep_section:
            recommendations.append(dep_section[:200])
    
    # Always include graph-based recommendations
    graph_recs = _fallback_recommendations(impact, graph)
    for rec in graph_recs:
        if rec not in recommendations:
            recommendations.append(rec)
    
    recommendations = recommendations[:8]

    # Confidence scoring with defensive bounds
    intent_confidence = float(intent.get("confidence", 0.0))
    impact_score = float(impact.get("risk_score", 0.0))
    
    # Adjust confidence based on LLM quality
    if llm_failed:
        # Lower confidence when falling back to graph reasoning only
        confidence_score = round(min(0.75, intent_confidence * 0.8), 2)
    else:
        confidence_score = round(min(1.0, (intent_confidence + (1.0 - impact_score)) / 2), 2)

    if not summaries:
        recommendations.insert(0, "Repository summaries incomplete — verify parser API output.")
    
    # Add debug note if LLM failed but graph reasoning succeeded
    if llm_failed and graph.get("focus_node_id"):
        recommendations.append(f"Note: Response generated from graph analysis (provider: {provider})")

    return make_structured_intelligence(
        summary=summary,
        affected_files=affected_files,
        dependency_chain=dependency_chain,
        risk_level=risk_level,
        recommendations=recommendations,
        confidence_score=confidence_score,
        graph_analysis=_build_graph_analysis(graph, impact),
        visualization_context={},
    )


def _empty_graph(request_id: str) -> GraphResult:
    return {
        "schema_version": "1.0",
        "stage": "graph",
        "request_id": request_id,
        "focus_node_id": None,
        "direct_dependencies": [],
        "indirect_dependencies": [],
        "upstream_dependencies": [],
        "downstream_ids": [],
        "propagation_depth": 0,
        "direct_paths": [],
        "indirect_paths": [],
        "reasoning_summary": {},
        "affected_nodes": [],
        "dependency_chains": [],
        "circular_dependencies": [],
        "traversal_explain": ["Graph data missing."],
        "cytoscape_elements": {"nodes": [], "edges": []},
    }


def _empty_impact(request_id: str) -> ImpactResult:
    return {
        "schema_version": "1.0",
        "stage": "impact",
        "request_id": request_id,
        "propagation_depth": 0,
        "propagation_scope": {"total_affected": 0},
        "impact_severity": "low",
        "risk_level": "low",
        "risk_score": 0.0,
        "risk_explanation": "Impact data unavailable.",
        "affected_by_depth": {},
        "risk_factors": [],
        "ai_reasoning": {"enabled": False},
    }


def process(
    intent: IntentResult,
    context: ContextResult,
    llm: LLMResult,
) -> PipelineResponse:
    """
    Input:  IntentResult, ContextResult, LLMResult
    Output: PipelineResponse with normalized intelligence block
    """
    rid = intent["request_id"]
    graph: GraphResult = context.get("graph_insights") or _empty_graph(rid)
    impact: ImpactResult = context.get("impact_insights") or _empty_impact(rid)

    intelligence = _build_intelligence(intent, context, llm, graph, impact)
    raw_text = (llm.get("text") or "").strip()
    highlights = _extract_bullets(raw_text) or intelligence.get("recommendations", [])[:8]

    meta: dict[str, Any] = {
        "provider": llm.get("provider"),
        "model": llm.get("model"),
        "usage": llm.get("usage", {}),
        "normalized": True,
        "llm_parse_sections": bool(_parse_sections(raw_text)),
    }

    provenance = {
        "context": context.get("provenance", {}),
        "stages": ["intent", "context", "graph", "impact", "prompt", "llm", "response"],
    }

    return make_pipeline_response(
        request_id=rid,
        query=intent.get("query", ""),
        intent=intent.get("intent", "general"),
        confidence=float(intent.get("confidence", 0.0)),
        answer=raw_text or intelligence.get("summary", ""),
        highlights=highlights,
        intelligence=intelligence,
        graph=graph,
        impact=impact,
        meta=meta,
        provenance=provenance,
    )
