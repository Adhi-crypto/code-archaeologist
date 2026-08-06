import unittest
import asyncio
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.git_ingestor import get_repo_id, _build_diff_summary
from app.reasoning.causal_reasoner import classify_query_intent, get_adaptive_n_results
from app.reasoning.evolution_detector import compute_importance, is_arch_change, classify_impact
from app.reasoning.confidence_scorer import extract_query_keywords, calculate_weighted_confidence
from app.temporal_rag.temporal_retriever import _detect_positional_commit_index

class TestCodeArchaeologistCore(unittest.TestCase):

    def test_repo_id_hash(self):
        url = "https://github.com/fastapi/fastapi"
        repo_id = get_repo_id(url)
        self.assertEqual(len(repo_id), 12)
        self.assertEqual(repo_id, get_repo_id(url))

    def test_intent_classifier(self):
        self.assertEqual(classify_query_intent("What is the repository about?"), "OVERVIEW")
        self.assertEqual(classify_query_intent("Why was the second commit refactored?"), "HISTORICAL")
        self.assertEqual(classify_query_intent("Explain authentication module."), "ARCHITECTURE")
        self.assertEqual(classify_query_intent("Fix bug origin crash in login"), "BUG_ORIGIN")
        self.assertEqual(classify_query_intent("How does the parser work?"), "IMPLEMENTATION")

    def test_positional_commit_detection(self):
        self.assertEqual(_detect_positional_commit_index("What does the first commit do?"), 0)
        self.assertEqual(_detect_positional_commit_index("Why was 2nd commit made?"), 1)
        self.assertEqual(_detect_positional_commit_index("What changed in third commit?"), 2)
        self.assertEqual(_detect_positional_commit_index("Explain latest commit"), -1)
        self.assertIsNone(_detect_positional_commit_index("Explain architecture"))

    def test_diff_summary_builder(self):
        files = ["a.py", "b.py", "c.py"]
        summary = _build_diff_summary(files, 10, 5)
        self.assertEqual(summary, "Changed: a.py, b.py, c.py | +10 -5")

    def test_importance_and_impact(self):
        score = compute_importance(100, 50, ["main.py", "routes.py"])
        self.assertTrue(score > 30.0)
        
        arch = is_arch_change(["docker-compose.yml", "main.py"], 200, 50)
        self.assertTrue(arch)
        
        impact = classify_impact(True, 250)
        self.assertEqual(impact, "Major Architecture Shift")

    def test_keyword_extraction_and_confidence(self):
        kw = extract_query_keywords("Fix authentication token bug in auth.py")
        self.assertIn("auth.py", kw["files"])
        self.assertIn("token", kw["keywords"])

        conf = calculate_weighted_confidence(
            semantic_score=0.9,
            file_match_score=1.0,
            recency_score=0.8,
            arch_impact_score=0.9,
            commit_importance=0.8,
            dev_frequency_score=0.7
        )
        self.assertTrue(80 <= conf <= 98)

if __name__ == "__main__":
    unittest.main()
