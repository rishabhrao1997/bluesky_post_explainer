#!/usr/bin/env python3
"""
Simple script to run the evaluator on test cases and generate a report.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path to import modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from tests.test_cases import TEST_CASES
from src.agent import BlueskyAgent
from src.bluesky_utils import get_post_details
from evaluation.evaluator import Evaluator


def run_evaluation() -> Dict[str, Any]:
    """Run evaluation on all test cases and return results."""
    agent = BlueskyAgent()
    evaluator = Evaluator()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_test_cases": len(TEST_CASES),
        "test_results": []
    }
    
    for i, test_case in enumerate(TEST_CASES, 1):
        test_id = test_case["id"]
        url = test_case["url"]
        description = test_case["description"]
        expected_output = test_case["expected_output"]
        
        print(f"\n[{i}/{len(TEST_CASES)}] Processing Test Case {test_id}: {description}")
        print(f"URL: {url}")
        
        try:
            # Get post as PostContent (get_post_details returns PostContent by default)
            post_content = get_post_details(url)
            if post_content.text.startswith("Error:"):
                err_msg = post_content.text
                print(f"  ❌ Error fetching post: {err_msg}")
                results["test_results"].append({
                    "test_id": test_id,
                    "url": url,
                    "description": description,
                    "status": "error",
                    "error": err_msg
                })
                continue
            
            # Get agent explanation (pass PostContent)
            print("  Generating explanation...")
            agent_text = agent.explain(url, post_content=post_content)
            
            # Evaluate the explanation (LLM judge uses only prediction and expected output)
            print("  Evaluating explanation...")
            evaluation = evaluator.evaluate(
                agent_text=agent_text,
                expected_output=expected_output
            )
            
            # Store results
            test_result = {
                "test_id": test_id,
                "url": url,
                "description": description,
                "status": "success",
                "original_post": post_content.text,
                "agent_explanation": agent_text,
                "expected_output": expected_output,
                "evaluation": evaluation
            }
            
            results["test_results"].append(test_result)
            
            # Print summary
            print(f"  ✓ Citations Score: {evaluation['citations_score']:.2f}")
            print(f"  ✓ Semantic Similarity: {evaluation['semantic_similarity_score']:.2f}")
            llm_judge = evaluation['llm_judge_score']
            print(f"  ✓ LLM Judge - Format: {llm_judge.get('format_pass', False)}, "
                  f"Accuracy: {llm_judge.get('accuracy', 0)}, "
                  f"Clarity: {llm_judge.get('clarity', 0)}, "
                  f"Brevity: {llm_judge.get('brevity', 0)}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results["test_results"].append({
                "test_id": test_id,
                "url": url,
                "description": description,
                "status": "error",
                "error": str(e)
            })
    
    return results


def generate_summary_report(results: Dict[str, Any]) -> str:
    """Generate a summary report from evaluation results."""
    test_results = results["test_results"]
    successful = [r for r in test_results if r.get("status") == "success"]
    failed = [r for r in test_results if r.get("status") == "error"]
    
    if not successful:
        return "No successful evaluations to summarize."
    
    # Calculate averages
    citations_scores = [r["evaluation"]["citations_score"] for r in successful]
    semantic_scores = [r["evaluation"]["semantic_similarity_score"] for r in successful]
    llm_judge_scores = [r["evaluation"]["llm_judge_score"] for r in successful]
    
    avg_citations = sum(citations_scores) / len(citations_scores) if citations_scores else 0
    avg_semantic = sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0
    avg_accuracy = sum(s.get("accuracy", 0) for s in llm_judge_scores) / len(llm_judge_scores) if llm_judge_scores else 0
    avg_clarity = sum(s.get("clarity", 0) for s in llm_judge_scores) / len(llm_judge_scores) if llm_judge_scores else 0
    avg_brevity = sum(s.get("brevity", 0) for s in llm_judge_scores) / len(llm_judge_scores) if llm_judge_scores else 0
    format_pass_count = sum(1 for s in llm_judge_scores if s.get("format_pass", False))
    
    report = f"""
{'='*60}
EVALUATION REPORT
{'='*60}
Timestamp: {results['timestamp']}
Total Test Cases: {results['total_test_cases']}
Successful: {len(successful)}
Failed: {len(failed)}

AVERAGE SCORES:
  Citations Score: {avg_citations:.3f}
  Semantic Similarity: {avg_semantic:.3f}
  LLM Judge Scores:
    Format Pass: {format_pass_count}/{len(successful)}
    Accuracy: {avg_accuracy:.2f}/5
    Clarity: {avg_clarity:.2f}/5
    Brevity: {avg_brevity:.2f}/5

{'='*60}
"""
    return report


def main():
    """Main function to run evaluation and generate report."""
    print("Starting evaluation on test cases...")
    print(f"Total test cases: {len(TEST_CASES)}\n")
    
    # Run evaluation
    results = run_evaluation()
    
    # Save to evaluation/results/ subdir
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / "evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Detailed results saved to: {output_file}")

    # Generate and print summary report
    summary = generate_summary_report(results)
    print(summary)

    summary_file = results_dir / "evaluation_summary.txt"
    with open(summary_file, "w") as f:
        f.write(summary)
    print(f"✓ Summary report saved to: {summary_file}")


if __name__ == "__main__":
    main()
