import re
from typing import List, Dict, Any


def extract_query_keywords(query: str) -> Dict[str, List[str]]:
    """Extract files, function names, error terms, and technical keywords from query."""
    query_lower = query.lower()
    
    # Extract file path mentions (e.g. auth.py, repo.py, /routes/chat)
    file_matches = re.findall(r'[\w\-/]+\.(?:py|js|ts|jsx|tsx|java|go|cpp|c|json|html|css)', query_lower)
    
    # Extract function/method names
    func_matches = re.findall(r'\b[a-zA-Z_]\w+(?=\(\))|\b[a-z]+[A-Z]\w+', query)
    
    # Extract keywords
    words = re.findall(r'\b[a-zA-Z]{3,}\b', query_lower)
    stop_words = {
        "the", "and", "for", "that", "this", "with", "after", "from", "into", "during",
        "been", "have", "were", "when", "some", "what", "which", "where", "stopped",
        "working", "fails", "failing", "issue", "bug", "broken", "became", "does", "not"
    }
    keywords = [w for w in words if w not in stop_words]
    
    return {
        "files": list(set(file_matches)),
        "functions": list(set(func_matches)),
        "keywords": list(set(keywords))
    }


def calculate_weighted_confidence(
    semantic_score: float,        # 0.0 - 1.0
    file_match_score: float,      # 0.0 - 1.0
    recency_score: float,         # 0.0 - 1.0
    arch_impact_score: float,     # 0.0 - 1.0
    commit_importance: float,     # 0.0 - 1.0
    dev_frequency_score: float    # 0.0 - 1.0
) -> float:
    """
    Weighted Confidence Scoring Formula:
    - Semantic Similarity:   40%
    - File Match:            20%
    - Temporal Context:      15%
    - Architecture Impact:   10%
    - Commit Importance:     10%
    - Developer Frequency:    5%
    Total = 100%
    Returns confidence percentage (0.0 to 100.0) rounded to 1 decimal.
    """
    weight_semantic = 0.40
    weight_file = 0.20
    weight_recency = 0.15
    weight_arch = 0.10
    weight_importance = 0.10
    weight_dev = 0.05
    
    weighted_total = (
        (semantic_score * weight_semantic) +
        (file_match_score * weight_file) +
        (recency_score * weight_recency) +
        (arch_impact_score * weight_arch) +
        (commit_importance * weight_importance) +
        (dev_frequency_score * weight_dev)
    ) * 100.0
    
    # Clamp between 20.0% and 98.5%
    final_score = max(20.0, min(98.5, round(weighted_total, 1)))
    return final_score
