import os
import re
import json
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from openai import OpenAI
from src.utils import fetch_url_text
from src.utils import retry_on_failure
from config.constants import CITATION_EVALUATION_MODEL, EMBEDDING_MODEL, LLM_JUDGE_MODEL


class Evaluator:
    """A class that evaluates the quality of the agent's explanation of a Bluesky post"""
    def __init__(self) -> None:
        """Initialize the Evaluator"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)

    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calculate the cosine similarity between two vectors
        
        Returns:
            The cosine similarity between the two vectors
        """
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    def check_citation_quality(self, agent_text: str) -> Tuple[float, str]:
        """Check the quality of the citations in the agent's explanation by asking the LLM if the citation supports any part of the claim

        Args: 
            agent_text: The agent's explanation of a Bluesky post
        
        Returns:
            A tuple containing the score and the number of citations that were relevant
        """
        urls = re.findall(r'https?://[^\s\)]+', agent_text)
        if not urls:
            return 0.0, "No citations provided"

        valid_count = 0
        for url in urls:
            content = fetch_url_text(url)
            if not content:
                continue
            
            claim_snippet = agent_text
            content_snippet = content
            prompt = f"""You are evaluating whether a single citation URL provides factual support for an Agent's claim (a summary of a Bluesky post).

IMPORTANT: You are evaluating ONE link at a time. The agent's claim may contain multiple points, but this URL might only support one of those points - that's still valid.

AGENT CLAIM:
{claim_snippet}

CITATION CONTENT (from {url}):
{content_snippet}

Task: Determine if this citation supports ANY part of the agent's claim.

Guidelines:
- Valid if the URL supports, explains, or provides evidence for ANY point in the claim
- Valid if it provides relevant background context for the claim
- Invalid if it's unrelated, contradicts the claim, or provides no relevant information
- The citation doesn't need to support the entire claim - supporting one point is enough to be valid

Reply ONLY with 'YES' if the citation supports any part of the claim, or 'NO' if it does not.
Do not include any other helper text or explanation in your response."""
            
            try:
                res = self._call_llm(prompt, model=CITATION_EVALUATION_MODEL)
                if res and "YES" in res.upper():
                    valid_count += 1
            except Exception:
                continue
        
        score = valid_count / len(urls) if urls else 0.0
        return score, f"{valid_count}/{len(urls)} citations were relevant"

    def calculate_semantic_similarity(self, agent_text: str, expected_output: Optional[str]) -> float:
        """Calculate the semantic similarity between the agent's explanation and the expected output based on the cosine similarity of the embeddings
        
        Args:
            agent_text: The agent's explanation of a Bluesky post
            expected_output: The expected output of the Bluesky post
        
        Returns:
            The cosine similarity score between the agent's explanation and the expected output
        """
        if not expected_output:
            return 0.0
        
        try:
            resp = self.client.embeddings.create(
                input=[agent_text, expected_output],
                model=EMBEDDING_MODEL
            )
            vec_a = np.array(resp.data[0].embedding)
            vec_b = np.array(resp.data[1].embedding)
            return self._cosine_similarity(vec_a, vec_b)
        except Exception:
            return 0.0

    @retry_on_failure()
    def _call_llm(self, prompt: str, model: str, response_format: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Call the LLM to generate a response to a prompt
        
        Args:
            prompt: The prompt to generate a response to
            model: The model to use to generate the response
            response_format: The response format to use for the response.
        
        Returns:
            The response from the LLM
        """
        return self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format if response_format else None
        ).choices[0].message.content

    def llm_judge_quality(self, agent_text: str, expected_output: Optional[str] = None) -> Dict[str, Any]:
        """Judge the quality of the agent's explanation by comparing prediction to expected output.
        Only the prediction and expected output are passed; the original post is not used.

        Args:
            agent_text: The agent's explanation (prediction)
            expected_output: The expected/reference output

        Returns:
            A dictionary containing the evaluation results
        """
        if expected_output:
            ref_text = expected_output
        else:
            ref_text = "N/A - Evaluate based on general coherence."
        
        prompt = f"""You are an expert evaluator assessing the quality of an AI-generated explanation.

AGENT OUTPUT (Prediction):
{agent_text}

EXPECTED OUTPUT (Reference):
{ref_text}

EVALUATION CRITERIA:

1. Format (format_pass: bool)
   - Check if the response contains exactly 3-5 bullet points
   - Each bullet should be a clear, distinct point
   - Markdown formatting is acceptable
   - Return true if format is correct, false otherwise

2. Accuracy (accuracy: 1-5 scale)
   - 5: All facts are correct and well-supported
   - 4: Mostly accurate with minor inaccuracies or missing context
   - 3: Generally accurate but has some factual errors or omissions
   - 2: Contains significant factual errors or misunderstandings
   - 1: Mostly or completely inaccurate
   - Compare against expected output when available, or evaluate based on general knowledge and coherence

3. Clarity (clarity: 1-5 scale)
   - 5: Extremely clear, easy to understand, well-structured
   - 4: Clear with minor ambiguities
   - 3: Generally understandable but some parts are unclear
   - 2: Difficult to understand, poorly structured
   - 1: Very unclear or confusing
   - Consider: sentence structure, word choice, logical flow, use of jargon

4. Brevity (brevity: 1-5 scale)
   - 5: Perfectly concise, no unnecessary words
   - 4: Mostly concise with minor verbosity
   - 3: Somewhat verbose but acceptable
   - 2: Too wordy, could be significantly shortened
   - 1: Extremely verbose, repetitive, or rambling
   - The response should be informative but not overly long

EVALUATION GUIDELINES:
- Be objective and fair in your assessment
- Consider the context: explanations should be informative but accessible
- If expected output is not available, evaluate based on internal coherence and general knowledge
- Provide a brief reason explaining your scores in the "reason" field

Return your evaluation as JSON with this exact structure:
{{ "format_pass": bool, "accuracy": int, "clarity": int, "brevity": int, "reason": str }}"""
        
        try:
            res = self._call_llm(
                prompt=prompt,
                model=LLM_JUDGE_MODEL,
                response_format={"type": "json_object"}
            )
            if res:
                return json.loads(res)
            return {
                "format_pass": False,
                "accuracy": 0,
                "clarity": 0,
                "brevity": 0,
                "reason": "No response from LLM"
            }
        except Exception as e:
            return {
                "format_pass": False,
                "accuracy": 0,
                "clarity": 0,
                "brevity": 0,
                "reason": f"Error evaluating: {str(e)}"
            }

    def evaluate(self, agent_text: str, expected_output: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate the quality of the agent's explanation by checking citations, semantic similarity, and LLM judge.
        The LLM judge compares only the prediction and expected output.

        Args:
            agent_text: The agent's explanation (prediction)
            expected_output: The expected/reference output

        Returns:
            A dictionary containing the evaluation results
        """
        citations_score, citations_reason = self.check_citation_quality(agent_text)
        semantic_similarity_score = self.calculate_semantic_similarity(agent_text, expected_output)
        llm_judge_score = self.llm_judge_quality(agent_text, expected_output)

        return {
            "citations_score": citations_score,
            "citations_reason": citations_reason,
            "semantic_similarity_score": semantic_similarity_score,
            "llm_judge_score": llm_judge_score
        }
