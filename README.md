# Bluesky Post Explanation Agent

An AI agent that explains Bluesky posts from their URLs with context-aware, search-grounded results. Supports multiple LLM providers (OpenAI, Anthropic, Gemini).

---

## Setup

**Prerequisites:** Python 3.10+, OpenAI API key (required). Optional: Anthropic or Google API keys for other providers.

1. **Install dependencies**
   ```bash
   cd bluesky_post_explainer
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   The repo includes a `.gitignore` for `venv/`, `__pycache__/`, and generated `evaluation/results/`.

2. **Set API keys**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   # Optional:
   export ANTHROPIC_API_KEY="your-key"
   export GEMINI_API_KEY="your-key"
   ```

---

## Sample Usage

**Explain a single post**
```bash
python scripts/run_agent.py --url https://bsky.app/profile/twins0.bsky.social/post/3mdd6n2my3s2e --provider openai
```
- `--provider` is optional; default is OpenAI. Values: `openai`, `anthropic`, `gemini`.
- Providers and model names are configured in `config/constants.py` (`DEFAULT_PROVIDER`, `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`).

**Run automated evaluation** (all test cases, multiple metrics)
```bash
python evaluation/run_eval_test_cases.py
```
- Results are written to `evaluation/results/`: `evaluation_results.json` (per-case details) and `evaluation_summary.txt` (averages and summary).

Sample report (`evaluation/results/evaluation_summary.txt`):

```
============================================================
EVALUATION REPORT
============================================================
Timestamp: 2026-01-29T03:34:35.660468
Total Test Cases: 12
Successful: 12
Failed: 0

AVERAGE SCORES:
  Citations Score: 0.674
  Semantic Similarity: 0.891
  LLM Judge Scores:
    Format Pass: 11/12
    Accuracy: 4.83/5
    Clarity: 5.00/5
    Brevity: 4.17/5

============================================================
```

**Human evaluation app**
```bash
streamlit run evaluation/eval_human_app.py
```
- Streamlit app for preference-based evaluation. **Two modes:**
  - **Single Model (Agent vs Expected Output):** Choose the **Agent provider** (openai, anthropic, gemini) in the sidebar before starting. For each test case, the app shows the original post, then two explanations in random order—one from the agent (using that provider), one from the ground truth in `tests/test_cases.py`. You choose which is better (Left/Right) or Tie. Agent output is generated on demand and cached.
  - **Two Models Comparison:** Choose two providers (Provider 1 and Provider 2) in the sidebar before starting. The app auto-generates outputs from both providers for each test case and shows them side by side in random order. You rate which explanation is better (Left/Right) or Tie. Which provider is left or right is never shown during evaluation.
- **Final report** reveals which provider and model had which score (e.g. "Agent (provider: openai, model: gpt-5.2) Wins: N" for single-model; "Provider 1 — openai (gpt-5.2): N wins" for two-model).
- **Test case order** is randomized each time you start a new evaluation.
- Results and caches (ratings, agent outputs, two-model outputs) are stored under `evaluation/results/human_eval/`.

---

## Flow

**Agent**

We use a small functional agent (no off-the-shelf agentic frameworks like OpenAI AgentKit, Google ADK, or LangChain) so we keep full control with minimal dependencies for this straightforward task.

1. **Input** — Bluesky post URL.
2. **Fetch** — Post text, author, images, and any external links. If the post is a repost, the original post’s text, images, and URLs are fetched. A web-scraping helper fetches the content of URLs attached to the post.
3. **Enrich** — Content from external links is fetched (as above).
4. **Generate** — The LLM explains using post + images + link content. Each provider’s **native web search tool** is used to ground answers (no custom search tool). The system prompt is in `config/prompts.py`.
5. **Output** — 3–5 bullet points with inline citations.

**Note:** Although the agent supports Anthropic and Gemini, the prompt is currently tuned for OpenAI’s GPT-style models.

**Evaluation**

- We treat explanation as abstractive generation, so ground truth is subjective. We use **12 human-vetted test cases** with expected outputs in `tests/test_cases.py`.
- **Automated evaluation** uses three signals (see *Evaluation choices* below).
- **Human evaluation** is done via the Streamlit app (see Sample Usage). Results are stored under `evaluation/results/human_eval/`.

---

## Evaluation choices

Explanation quality is multi-faceted, so we combine three metrics instead of relying on a single score.

| Metric | What it measures | How it’s computed |
|--------|------------------|-------------------|
| **Citation quality** | Whether cited URLs actually support the claims | URLs are extracted from the response (regex). For each URL we fetch the page content, then ask an LLM (see `CITATION_EVALUATION_MODEL` in `config/constants.py`) whether the content supports *any* part of the explanation. Score = (relevant citations) / (total citations). *Note: The URL context fetcher sometimes returns 403; a more robust scraper can improve this.* |
| **Semantic similarity** | Content overlap with expected output (meaning, not wording) | Agent output and expected output are embedded with `EMBEDDING_MODEL` (OpenAI). Score = cosine similarity between the two vectors. |
| **LLM judge** | Format, accuracy, clarity, brevity | An LLM (`LLM_JUDGE_MODEL`) compares agent output to the expected output only (original post is not passed). It returns: **format_pass** (bool: 3–5 bullet points), **accuracy** (1–5), **clarity** (1–5), **brevity** (1–5), and a short **reason**. Criteria and prompts live in `evaluation/evaluator.py`. |

**Why these three:** Citation quality checks verifiability; semantic similarity checks alignment with reference meaning; the LLM judge captures format and subjective quality (accuracy/clarity/brevity) that embeddings don’t. All evaluation models are configurable in `config/constants.py` so you can trade cost vs quality (e.g. use a smaller model for citation checks or the judge).

**Human evaluation** complements this: for subjective preference (e.g. “which explanation do you prefer?”), the Streamlit app collects pairwise ratings. Use it to validate that automated scores match human preferences or to compare two setups (e.g. two providers) without changing code.

---

## Configuration

All tunable behaviour is in **`config/constants.py`** and **`config/prompts.py`**. No code changes needed for routine experiments.

**Agent behaviour**

| Constant | Role | Example |
|----------|------|---------|
| `DEFAULT_PROVIDER` | Default LLM for the agent when `--provider` is not passed | `"openai"`, `"anthropic"`, `"gemini"` |
| `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL` | Model name per provider | `"gpt-5.2"`, `"claude-sonnet-4-5"`, `"gemini-2.5-flash"` |
| `MAX_EXTERNAL_CONTENT_LENGTH` | Max characters fetched from external URLs in posts | `10000` |
| `REQUEST_TIMEOUT`, `MAX_RETRIES`, `RETRY_DELAY` | Bluesky/HTTP retry and timeout | Tune if you hit rate limits or slow networks |

**Evaluation behaviour**

| Constant | Role | Example |
|----------|------|---------|
| `CITATION_EVALUATION_MODEL` | Model used to judge “does this URL support the claim?” | `"gpt-4.1-mini"` (cheaper, faster) |
| `EMBEDDING_MODEL` | Model for semantic similarity | `"text-embedding-3-small"` |
| `LLM_JUDGE_MODEL` | Model for format/accuracy/clarity/brevity | `"gpt-4.1"` |

**Prompt**

- **`config/prompts.py`** holds the agent’s system prompt (`SYSTEM_PROMPT`). Edit it to change tone, length, citation style, or instructions (e.g. “always mention the author”). The agent in `src/post_content.py` imports this prompt.

**Ways to experiment**

1. **Switch provider / model:** Set `DEFAULT_PROVIDER` and the corresponding `*_MODEL` in `constants.py`, or pass `--provider openai|anthropic|gemini` when running `scripts/run_agent.py`.
2. **Cheaper / faster evaluation:** Use a smaller model for `CITATION_EVALUATION_MODEL` or `LLM_JUDGE_MODEL` in `constants.py`.
3. **Different explanation style:** Edit `SYSTEM_PROMPT` in `config/prompts.py` (e.g. more bullets, stricter citations), then re-run the agent and `evaluation/run_eval_test_cases.py`.
4. **Compare two setups:** Use the human eval app in “Two Models Comparison” mode: select Provider 1 and Provider 2 in the sidebar, then run. The app generates both outputs per test case and lets you rate them blindly (Left/Right or Tie).

---

## Design Choices

| Area | Choice | Reason |
|------|--------|--------|
| **Agent** | Functional agent; no framework (AgentKit, ADK, LangChain) | Simple requirement; full control, fewer abstractions. |
| **LLMs** | Abstract `LLMProvider` (OpenAI, Anthropic, Gemini) | Swap providers without changing agent logic. |
| **Search** | Provider-native web search tool | Avoid maintaining a custom tool; native tools work well for most cases. |
| **Resilience** | `@retry_on_failure()` on API calls | Handles transient and rate-limit issues. |
| **Evaluation** | Citation check + semantic similarity + LLM judge | No single metric; covers facts, meaning, and style. |
| **Output** | 3–5 bullets, inline citations | Verifiable, scannable, and easy to evaluate. |
| **Context** | Post + images + link content + web search | Covers memes, slang, and external references. |

See *Configuration* above for where to change behaviour.

---

## Limitations

- **Single post only** — No threads or batch; one URL per run.
- **Rate and cost** — No caching; each run hits Bluesky, search, and LLM APIs.
- **Language** — Optimized for English; quality may drop for other languages.
- **Real-time** — Depends on web search and model knowledge; can be outdated for very recent events.

---

## Future Work

- Stronger citation parsing and more evaluation metrics.
- Support for threaded and chained posts.
- Better URL context fetching.
- More optimized search tools.

---

## Directory Structure

```
rc_assignment/
├── src/                        # Source code
│   ├── agent.py                # Main BlueskyAgent class
│   ├── bluesky_utils.py        # Bluesky API utilities
│   ├── embed_types.py          # Embed / post content types
│   ├── post_content.py         # Post content aggregation
│   ├── provider.py              # LLM providers (OpenAI, Anthropic, Gemini)
│   └── utils.py                 # General utilities (e.g. retry decorator)
├── config/
│   ├── constants.py            # API endpoints, timeouts, model names
│   └── prompts.py              # System prompts
├── tests/
│   └── test_cases.py           # Test cases and ground truth
├── evaluation/
│   ├── evaluator.py            # Evaluation logic (citations, similarity, LLM judge)
│   ├── run_eval_test_cases.py  # Run evaluation on all test cases
│   ├── eval_human_app.py       # Streamlit app for human evaluation
│   └── results/                # Generated outputs (gitignored)
│       ├── evaluation_results.json
│       ├── evaluation_summary.txt
│       └── human_eval/         # Human eval ratings and caches
├── scripts/
│   └── run_agent.py            # CLI to explain a single post
├── requirements.txt
└── .gitignore
```
