import streamlit as st
import json
import logging
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Add parent directory to path to import modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from tests.test_cases import TEST_CASES
from src.bluesky_utils import get_post_details
from src.agent import BlueskyAgent
from src.provider import SUPPORTED_MODELS
from config.constants import OPENAI_MODEL, ANTHROPIC_MODEL, GEMINI_MODEL

# --- Config: human eval results live in evaluation/results/human_eval/ ---
EVAL_RESULTS_DIR = Path(__file__).parent / "results" / "human_eval"
RESULTS_FILE = "human_ratings.json"
AGENT_OUTPUTS_FILE = "agent_outputs_cache.json"
TWO_MODEL_CACHE_FILE = "agent_outputs_two_models_cache.json"
PROVIDER_OPTIONS = list(SUPPORTED_MODELS.keys())
EMPTY_RESPONSE_DISPLAY = "*(Empty response)*"

PROVIDER_TO_MODEL: Dict[str, str] = {
    "openai": OPENAI_MODEL,
    "anthropic": ANTHROPIC_MODEL,
    "gemini": GEMINI_MODEL,
}

# Ensure logs (e.g. provider errors) appear in the terminal when run via Streamlit
if not logging.getLogger().handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(_handler)


def get_model_name_for_provider(provider: str) -> str:
    """Return the default model name for a provider."""
    return PROVIDER_TO_MODEL.get(provider.lower(), provider)


def _eval_results_path(filename: str) -> Path:
    """Return path for a file in the human eval results subdir; ensure dir exists."""
    path = EVAL_RESULTS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_agent_outputs() -> Dict[str, str]:
    """Load cached agent outputs."""
    outputs_path = _eval_results_path(AGENT_OUTPUTS_FILE)
    if outputs_path.exists():
        with open(outputs_path, "r") as f:
            data = json.load(f)
            # Handle both old and new cache formats
            if isinstance(data, dict):
                return {url: data[url].get("output", "") if isinstance(data[url], dict) else data[url] 
                       for url in data.keys()}
    return {}


def generate_agent_output(url: str) -> Optional[str]:
    """Generate agent output for a given URL."""
    try:
        agent = BlueskyAgent()
        output = agent.explain(url)
        if output and not output.startswith("Error:"):
            # Cache it
            cache_path = _eval_results_path(AGENT_OUTPUTS_FILE)
            cache = load_agent_outputs()
            cache[url] = output
            with open(cache_path, "w") as f:
                json.dump(cache, f, indent=2)
            return output
    except Exception as e:
        st.error(f"Error generating agent output: {str(e)}")
        return None
    return None


def get_agent_output(url: str, use_cache: bool = True) -> Optional[str]:
    """Get agent output, from cache or generate if needed."""
    cache = load_agent_outputs() if use_cache else {}
    if url in cache and cache[url]:
        return cache[url]
    return None


def load_two_model_cache() -> Dict[str, Dict[str, str]]:
    """Load two-model cache: url -> provider_name -> output."""
    cache_path = _eval_results_path(TWO_MODEL_CACHE_FILE)
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return {}


def get_cached_output_two_models(url: str, provider_name: str) -> Optional[str]:
    """Get cached output for a url and provider in two-model mode. Returns '' if cached value is empty (don't retry)."""
    cache = load_two_model_cache()
    if url in cache and provider_name in cache[url]:
        return cache[url][provider_name]
    return None


def _generate_output_for_provider_no_cache(url: str, provider_name: str) -> Tuple[str, Optional[str]]:
    """Generate agent output for a URL and provider. Returns (provider_name, output or None). Empty string is returned so we cache it and don't retry."""
    try:
        agent = BlueskyAgent(provider_name=provider_name)
        output = agent.explain(url)
        if output is not None and not output.startswith("Error:"):
            return (provider_name, output)
    except Exception as e:
        logger.exception("Failed to generate output for provider %s: %s", provider_name, e)
    return (provider_name, None)


def _save_to_two_model_cache(url: str, provider_name: str, output: str) -> None:
    """Write a single provider output into the two-model cache."""
    cache_path = _eval_results_path(TWO_MODEL_CACHE_FILE)
    cache = load_two_model_cache()
    if url not in cache:
        cache[url] = {}
    cache[url][provider_name] = output
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


def generate_agent_output_for_provider(url: str, provider_name: str) -> Optional[str]:
    """Generate agent output for a given URL using the specified provider. Caches result (including empty string)."""
    _, output = _generate_output_for_provider_no_cache(url, provider_name)
    if output is not None:
        _save_to_two_model_cache(url, provider_name, output)
        return output
    return None


def clear_results() -> None:
    """Clear all evaluation results."""
    results_path = _eval_results_path(RESULTS_FILE)
    # Clear the file by writing empty list
    with open(results_path, "w") as f:
        json.dump([], f, indent=2)


def save_result(
    mode: str,
    test_id: int,
    url: str,
    description: str,
    winner: str,
    model_a: Optional[str] = None,
    model_b: Optional[str] = None,
    agent_provider: Optional[str] = None,
    agent_model: Optional[str] = None,
    provider_a: Optional[str] = None,
    provider_b: Optional[str] = None,
) -> None:
    """Save human evaluation result."""
    results_path = _eval_results_path(RESULTS_FILE)
    
    results: List[Dict[str, Any]] = []
    
    if results_path.exists():
        with open(results_path, "r") as f:
            results = json.load(f)
    
    result = {
        "mode": mode,
        "test_id": test_id,
        "url": url,
        "description": description,
        "winner": winner,
    }
    
    if mode == "single_model":
        if agent_provider is not None:
            result["agent_provider"] = agent_provider
        if agent_model is not None:
            result["agent_model"] = agent_model
    
    if mode == "two_models":
        result["model_a"] = model_a
        result["model_b"] = model_b
        if provider_a is not None:
            result["provider_a"] = provider_a
        if provider_b is not None:
            result["provider_b"] = provider_b
    
    results.append(result)
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)


def generate_preference_report() -> str:
    """Generate preference ratings report; reveals provider and model at the end."""
    results_path = _eval_results_path(RESULTS_FILE)
    if not results_path.exists():
        return "No results found."
    
    with open(results_path, "r") as f:
        results = json.load(f)
    
    if not results:
        return "No results found."
    
    # Separate by mode
    single_model_results = [r for r in results if r.get("mode") == "single_model"]
    two_model_results = [r for r in results if r.get("mode") == "two_models"]
    
    report = []
    report.append("=" * 60)
    report.append("PREFERENCE RATINGS REPORT")
    report.append("=" * 60)
    report.append("")
    
    if single_model_results:
        report.append("SINGLE MODEL EVALUATION (Agent vs Expected Output)")
        report.append("-" * 60)
        agent_wins = sum(1 for r in single_model_results if r.get("winner") == "Agent")
        gt_wins = sum(1 for r in single_model_results if r.get("winner") == "Expected Output")
        ties = sum(1 for r in single_model_results if r.get("winner") == "Tie")
        total = len(single_model_results)
        
        # Reveal which provider/model was the Agent
        first = single_model_results[0]
        agent_provider = first.get("agent_provider") or "unknown"
        agent_model = first.get("agent_model") or get_model_name_for_provider(agent_provider)
        agent_label = f"Agent (provider: {agent_provider}, model: {agent_model})"
        
        report.append(f"Total Evaluations: {total}")
        report.append(f"{agent_label} Wins: {agent_wins} ({agent_wins/total*100:.1f}%)")
        report.append(f"Expected Output Wins: {gt_wins} ({gt_wins/total*100:.1f}%)")
        report.append(f"Ties: {ties} ({ties/total*100:.1f}%)")
        report.append("")
    
    if two_model_results:
        report.append("TWO MODEL EVALUATION (reveal at end)")
        report.append("-" * 60)
        model_a_wins = sum(1 for r in two_model_results if r.get("winner") == "Model A")
        model_b_wins = sum(1 for r in two_model_results if r.get("winner") == "Model B")
        ties = sum(1 for r in two_model_results if r.get("winner") == "Tie")
        total = len(two_model_results)
        
        # Reveal which provider/model was Provider 1 and Provider 2
        first = two_model_results[0]
        prov_a = first.get("provider_a") or "unknown"
        prov_b = first.get("provider_b") or "unknown"
        model_a = get_model_name_for_provider(prov_a)
        model_b = get_model_name_for_provider(prov_b)
        
        report.append(f"Total Evaluations: {total}")
        report.append(f"Provider 1 — {prov_a} ({model_a}): {model_a_wins} wins ({model_a_wins/total*100:.1f}%)")
        report.append(f"Provider 2 — {prov_b} ({model_b}): {model_b_wins} wins ({model_b_wins/total*100:.1f}%)")
        report.append(f"Ties: {ties} ({ties/total*100:.1f}%)")
        report.append("")
    
    report.append("=" * 60)
    return "\n".join(report)


# --- Initialize Session State ---
if "mode" not in st.session_state:
    st.session_state.mode = "single_model"  # or "two_models"
if "num_cases" not in st.session_state:
    st.session_state.num_cases = len(TEST_CASES)
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "layout_swapped" not in st.session_state:
    st.session_state.layout_swapped = False
if "evaluation_started" not in st.session_state:
    st.session_state.evaluation_started = False
if "finished" not in st.session_state:
    st.session_state.finished = False
if "single_model_provider" not in st.session_state:
    st.session_state.single_model_provider = PROVIDER_OPTIONS[0]
if "model_a_provider" not in st.session_state:
    st.session_state.model_a_provider = PROVIDER_OPTIONS[0]
if "model_b_provider" not in st.session_state:
    st.session_state.model_b_provider = PROVIDER_OPTIONS[1] if len(PROVIDER_OPTIONS) > 1 else PROVIDER_OPTIONS[0]
if "test_case_order" not in st.session_state:
    st.session_state.test_case_order = list(range(len(TEST_CASES)))
if "show_reveal" not in st.session_state:
    st.session_state.show_reveal = False
if "last_choice" not in st.session_state:
    st.session_state.last_choice = ""  # "left", "right", "tie", "skip"

# --- UI ---
st.set_page_config(layout="wide", page_title="Bluesky Agent Human Eval")
st.title("👨‍⚖️ Bluesky Agent Human Evaluation")

# Sidebar - Always visible
with st.sidebar:
    st.header("Configuration")
    
    if not st.session_state.evaluation_started:
        mode = st.radio(
            "Evaluation Mode",
            ["single_model", "two_models"],
            format_func=lambda x: "Single Model (Agent vs Expected Output)" if x == "single_model" else "Two Models Comparison",
            index=0 if st.session_state.mode == "single_model" else 1
        )
        st.session_state.mode = mode
        
        max_cases = len(TEST_CASES)
        num_cases = st.number_input(
            "Number of Test Cases",
            min_value=1,
            max_value=max_cases,
            value=min(st.session_state.num_cases, max_cases),
            help=f"Maximum: {max_cases} test cases"
        )
        st.session_state.num_cases = num_cases
        
        if mode == "single_model":
            st.markdown("**Agent provider**")
            idx_single = PROVIDER_OPTIONS.index(st.session_state.single_model_provider) if st.session_state.single_model_provider in PROVIDER_OPTIONS else 0
            single_model_provider = st.selectbox("Provider", PROVIDER_OPTIONS, index=idx_single, key="sb_single_provider")
            st.session_state.single_model_provider = single_model_provider
        
        if mode == "two_models":
            st.markdown("**Two-model providers**")
            idx_a = PROVIDER_OPTIONS.index(st.session_state.model_a_provider) if st.session_state.model_a_provider in PROVIDER_OPTIONS else 0
            model_a_provider = st.selectbox("Provider 1", PROVIDER_OPTIONS, index=idx_a, key="sb_model_a")
            st.session_state.model_a_provider = model_a_provider
            # Provider 2: only options that are not Provider 1 (no same provider for both)
            provider_2_options = [p for p in PROVIDER_OPTIONS if p != model_a_provider]
            if st.session_state.model_b_provider == model_a_provider or st.session_state.model_b_provider not in provider_2_options:
                st.session_state.model_b_provider = provider_2_options[0]
            idx_b = provider_2_options.index(st.session_state.model_b_provider) if st.session_state.model_b_provider in provider_2_options else 0
            model_b_provider = st.selectbox("Provider 2", provider_2_options, index=idx_b, key="sb_model_b")
            st.session_state.model_b_provider = model_b_provider
        
        if st.button("🚀 Start Evaluation", use_container_width=True):
            # Clear previous results when starting a new evaluation
            clear_results()
            st.session_state.evaluation_started = True
            st.session_state.current_idx = 0
            st.session_state.finished = False
            st.session_state.show_reveal = False
            st.session_state.layout_swapped = random.choice([True, False])
            # Randomize test case order for this session
            order = list(range(min(st.session_state.num_cases, len(TEST_CASES))))
            random.shuffle(order)
            st.session_state.test_case_order = order
            st.rerun()
    
    # Progress and controls (always visible when started)
    if st.session_state.evaluation_started:
        st.markdown("---")
        st.subheader("Progress")
        
        # Fix progress calculation - clamp to [0, 1]
        progress_value = min(1.0, max(0.0, (st.session_state.current_idx + 1) / st.session_state.num_cases))
        st.progress(progress_value)
        st.write(f"**{st.session_state.current_idx + 1} / {st.session_state.num_cases} cases**")
        
        # Show current stats
        results_path = _eval_results_path(RESULTS_FILE)
        if results_path.exists():
            with open(results_path, "r") as f:
                results = json.load(f)
            
            current_mode_results = [r for r in results if r.get("mode") == st.session_state.mode]
            if current_mode_results:
                st.markdown("---")
                st.subheader("Current Session Stats")
                if st.session_state.mode == "single_model":
                    agent_wins = sum(1 for r in current_mode_results if r.get("winner") == "Agent")
                    gt_wins = sum(1 for r in current_mode_results if r.get("winner") == "Expected Output")
                    ties = sum(1 for r in current_mode_results if r.get("winner") == "Tie")
                    st.write(f"✅ Agent: {agent_wins}")
                    st.write(f"✅ Expected Output: {gt_wins}")
                    st.write(f"🤝 Ties: {ties}")
                else:
                    model_a_wins = sum(1 for r in current_mode_results if r.get("winner") == "Model A")
                    model_b_wins = sum(1 for r in current_mode_results if r.get("winner") == "Model B")
                    ties = sum(1 for r in current_mode_results if r.get("winner") == "Tie")
                    st.write(f"✅ Provider 1: {model_a_wins}")
                    st.write(f"✅ Provider 2: {model_b_wins}")
                    st.write(f"🤝 Ties: {ties}")
        
        st.markdown("---")
        if st.button("🔄 Start Over", use_container_width=True):
            # Clear results when starting over
            clear_results()
            st.session_state.evaluation_started = False
            st.session_state.finished = False
            st.session_state.current_idx = 0
            st.session_state.show_reveal = False
            st.rerun()

# Main Evaluation Interface
if st.session_state.evaluation_started and not st.session_state.finished:
    # Get current test case (order was randomized when evaluation started)
    test_case_indices = st.session_state.test_case_order[: st.session_state.num_cases]
    test_cases_to_use = [TEST_CASES[i] for i in test_case_indices]
    current_case = test_cases_to_use[st.session_state.current_idx]
    
    # Load post details
    post_details = get_post_details(current_case["url"], return_dict=True)
    post_text = post_details.get("text", "Error fetching post") if "error" not in post_details else "Error fetching post"
    
    # Load or generate agent output(s) automatically
    agent_output = None
    model_a_output = None
    model_b_output = None
    
    if st.session_state.mode == "single_model":
        provider = st.session_state.single_model_provider
        agent_output = get_cached_output_two_models(current_case["url"], provider)
        if agent_output is None:
            with st.spinner(f"🤖 Generating agent output ({provider})..."):
                agent_output = generate_agent_output_for_provider(current_case["url"], provider)
                if agent_output is not None:
                    st.rerun()
                else:
                    agent_output = EMPTY_RESPONSE_DISPLAY
        if agent_output == "":
            agent_output = EMPTY_RESPONSE_DISPLAY
    else:
        # Two-model mode: load or generate both provider outputs (in parallel when both missing)
        provider_a = st.session_state.model_a_provider
        provider_b = st.session_state.model_b_provider
        model_a_output = get_cached_output_two_models(current_case["url"], provider_a)
        model_b_output = get_cached_output_two_models(current_case["url"], provider_b)
        
        if model_a_output is None or model_b_output is None:
            with st.spinner("🤖 Generating outputs..."):
                url = current_case["url"]
                results_to_run: List[Tuple[str, Optional[str]]] = []
                with ThreadPoolExecutor(max_workers=2) as executor:
                    if model_a_output is None:
                        results_to_run.append((provider_a, executor.submit(_generate_output_for_provider_no_cache, url, provider_a)))
                    if model_b_output is None:
                        results_to_run.append((provider_b, executor.submit(_generate_output_for_provider_no_cache, url, provider_b)))
                    completed: List[Tuple[str, Optional[str]]] = []
                    for prov, future in results_to_run:
                        _prov, out = future.result()
                        completed.append((_prov, out))
                for prov, out in completed:
                    _save_to_two_model_cache(url, prov, out if out is not None else "")
                    if out is not None:
                        if prov == provider_a:
                            model_a_output = out
                        else:
                            model_b_output = out
                if model_a_output is None:
                    model_a_output = EMPTY_RESPONSE_DISPLAY
                if model_b_output is None:
                    model_b_output = EMPTY_RESPONSE_DISPLAY
                st.rerun()
        if model_a_output == "":
            model_a_output = EMPTY_RESPONSE_DISPLAY
        if model_b_output == "":
            model_b_output = EMPTY_RESPONSE_DISPLAY
    
    # Header
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader(f"Test Case {current_case['id']}: {current_case['description']}")
    with col_header2:
        st.write(f"**{st.session_state.current_idx + 1} / {st.session_state.num_cases}**")
    
    st.caption(f"URL: {current_case['url']}")
    
    # Show original post with images and external links
    with st.expander("📝 View Original Post", expanded=True):
        st.write(post_text)
        if post_details.get("author_handle"):
            st.caption(f"By: @{post_details.get('author_handle')}")
        
        # Show images if present
        if post_details.get("image_urls"):
            for idx, image_info in enumerate(post_details["image_urls"], 1):
                # Handle both old format (string) and new format (dict)
                if isinstance(image_info, dict):
                    image_url = image_info.get("url", "")
                    alt_text = image_info.get("alt", "")
                    is_repost = image_info.get("is_repost", False)
                    
                    caption_parts = [f"Image {idx}"]
                    if is_repost:
                        caption_parts.append("(Reposted)")
                    if alt_text:
                        caption_parts.append(f"- {alt_text}")
                    
                    st.image(image_url, caption=" | ".join(caption_parts), use_container_width=True)
                else:
                    # Backward compatibility with old string format
                    st.image(image_info, caption=f"Post Image {idx}", use_container_width=True)
        
        # Show external link if present
        if post_details.get("external_url"):
            st.markdown(f"🔗 **External Link:** [{post_details['external_url']}]({post_details['external_url']})")
            if post_details.get("external_content"):
                with st.expander("📄 View External Content", expanded=False):
                    st.write(post_details["external_content"][:1000] + "..." if len(post_details.get("external_content", "")) > 1000 else post_details.get("external_content", ""))
    
    st.markdown("---")
    
    # Compute labels for reveal (which side was which)
    swapped = st.session_state.layout_swapped
    if st.session_state.mode == "single_model":
        agent_label = f"Agent (provider: {st.session_state.single_model_provider}, model: {get_model_name_for_provider(st.session_state.single_model_provider)})"
        left_was = "Expected Output" if swapped else agent_label
        right_was = agent_label if swapped else "Expected Output"
    else:
        label_a = f"Provider 1 — {st.session_state.model_a_provider} ({get_model_name_for_provider(st.session_state.model_a_provider)})"
        label_b = f"Provider 2 — {st.session_state.model_b_provider} ({get_model_name_for_provider(st.session_state.model_b_provider)})"
        left_was = label_b if swapped else label_a
        right_was = label_a if swapped else label_b
    
    if st.session_state.show_reveal:
        # Reveal which side was which, then button to move to next case
        choice_text = {"left": "Left", "right": "Right", "tie": "Tie", "skip": "Skip"}.get(st.session_state.last_choice, "")
        if choice_text:
            st.info(f"**You chose:** {choice_text}")
        st.markdown("**Reveal:**")
        st.markdown(f"- **Left** was: {left_was}")
        st.markdown(f"- **Right** was: {right_was}")
        st.markdown("---")
        if st.button("➡️ Next case", key="next_case", type="primary", use_container_width=True):
            st.session_state.show_reveal = False
            st.session_state.last_choice = ""
            st.session_state.current_idx += 1
            st.session_state.layout_swapped = random.choice([True, False])
            if st.session_state.current_idx >= st.session_state.num_cases:
                st.session_state.finished = True
            st.rerun()
    else:
        # Evaluation content based on mode (blind: mix left/right)
        if st.session_state.mode == "single_model":
            # Single model: Agent vs Expected Output (blind, mixed left/right)
            col1, col2 = st.columns(2)
            agent_display = agent_output or EMPTY_RESPONSE_DISPLAY
            content_left = current_case["expected_output"] if swapped else agent_display
            content_right = agent_display if swapped else current_case["expected_output"]
            is_left_agent = not swapped
            is_right_agent = swapped
            
            with col1:
                st.markdown("### Explanation A")
                st.markdown(content_left)
            with col2:
                st.markdown("### Explanation B")
                st.markdown(content_right)
            
            st.markdown("---")
            st.write("**Which explanation is better?**")
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
            
            if btn_col1.button("👈 Left", key="left", use_container_width=True):
                winner = "Agent" if is_left_agent else "Expected Output"
                save_result("single_model", current_case["id"], current_case["url"], current_case["description"], winner, agent_provider=st.session_state.single_model_provider, agent_model=get_model_name_for_provider(st.session_state.single_model_provider))
                st.session_state.show_reveal = True
                st.session_state.last_choice = "left"
                st.rerun()
            if btn_col2.button("👉 Right", key="right", use_container_width=True):
                winner = "Agent" if is_right_agent else "Expected Output"
                save_result("single_model", current_case["id"], current_case["url"], current_case["description"], winner, agent_provider=st.session_state.single_model_provider, agent_model=get_model_name_for_provider(st.session_state.single_model_provider))
                st.session_state.show_reveal = True
                st.session_state.last_choice = "right"
                st.rerun()
            if btn_col3.button("🤝 Tie", key="tie", use_container_width=True):
                save_result("single_model", current_case["id"], current_case["url"], current_case["description"], "Tie", agent_provider=st.session_state.single_model_provider, agent_model=get_model_name_for_provider(st.session_state.single_model_provider))
                st.session_state.show_reveal = True
                st.session_state.last_choice = "tie"
                st.rerun()
            if btn_col4.button("⏭️ Skip", key="skip", use_container_width=True):
                st.session_state.show_reveal = True
                st.session_state.last_choice = "skip"
                st.rerun()
        
        else:  # two_models mode — blind, mixed left/right
            col1, col2 = st.columns(2)
            out_a = model_a_output or EMPTY_RESPONSE_DISPLAY
            out_b = model_b_output or EMPTY_RESPONSE_DISPLAY
            content_left = out_b if swapped else out_a
            content_right = out_a if swapped else out_b
            is_left_model_a = not swapped
            is_right_model_a = swapped
            
            with col1:
                st.markdown("### Explanation A")
                st.markdown(content_left)
            with col2:
                st.markdown("### Explanation B")
                st.markdown(content_right)
            
            st.markdown("---")
            st.write("**Which explanation is better?**")
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
            
            if btn_col1.button("👈 Left", key="left_2m", use_container_width=True):
                winner = "Model A" if is_left_model_a else "Model B"
                save_result("two_models", current_case["id"], current_case["url"], current_case["description"], winner, model_a_output, model_b_output, provider_a=st.session_state.model_a_provider, provider_b=st.session_state.model_b_provider)
                st.session_state.show_reveal = True
                st.session_state.last_choice = "left"
                st.rerun()
            if btn_col2.button("👉 Right", key="right_2m", use_container_width=True):
                winner = "Model A" if is_right_model_a else "Model B"
                save_result("two_models", current_case["id"], current_case["url"], current_case["description"], winner, model_a_output, model_b_output, provider_a=st.session_state.model_a_provider, provider_b=st.session_state.model_b_provider)
                st.session_state.show_reveal = True
                st.session_state.last_choice = "right"
                st.rerun()
            if btn_col3.button("🤝 Tie", key="tie_2m", use_container_width=True):
                save_result("two_models", current_case["id"], current_case["url"], current_case["description"], "Tie", model_a_output, model_b_output, provider_a=st.session_state.model_a_provider, provider_b=st.session_state.model_b_provider)
                st.session_state.show_reveal = True
                st.session_state.last_choice = "tie"
                st.rerun()
            if btn_col4.button("⏭️ Skip", key="skip_2m", use_container_width=True):
                st.session_state.show_reveal = True
                st.session_state.last_choice = "skip"
                st.rerun()
    
    # Navigation (only when not in reveal)
    if not st.session_state.show_reveal:
        st.markdown("---")
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        
        if nav_col1.button("⏮️ Previous", key="prev", disabled=st.session_state.current_idx == 0):
            st.session_state.current_idx = max(0, st.session_state.current_idx - 1)
            st.session_state.layout_swapped = random.choice([True, False])
            st.session_state.show_reveal = False
            st.rerun()
        
        nav_col2.write(f"**Case {st.session_state.current_idx + 1} of {st.session_state.num_cases}**")
        
        if nav_col3.button("⏭️ Next", key="next", disabled=st.session_state.current_idx >= st.session_state.num_cases - 1):
            st.session_state.current_idx += 1
            st.session_state.layout_swapped = random.choice([True, False])
            if st.session_state.current_idx >= st.session_state.num_cases:
                st.session_state.finished = True
            st.rerun()
        
        if nav_col4.button("✅ Finish Early", key="finish_early"):
            st.session_state.finished = True
            st.rerun()

# Finished State
elif st.session_state.finished or (st.session_state.evaluation_started and st.session_state.current_idx >= st.session_state.num_cases):
    st.success("🎉 Evaluation Complete!")
    
    # Generate and show report
    report = generate_preference_report()
    st.text(report)
    
    # Download report
    st.download_button(
        label="📥 Download Report",
        data=report,
        file_name="preference_ratings_report.txt",
        mime="text/plain"
    )
    
    # Show detailed results
    results_path = _eval_results_path(RESULTS_FILE)
    if results_path.exists():
        with open(results_path, "r") as f:
            results = json.load(f)
        
        st.subheader("Detailed Results")
        st.json(results)
        
        st.download_button(
            label="📥 Download JSON Results",
            data=json.dumps(results, indent=2),
            file_name="human_ratings.json",
            mime="application/json"
        )
    
    # Reset option (also available in sidebar)
    st.markdown("---")
    if st.button("🔄 Start New Evaluation"):
        # Clear results when starting new evaluation
        clear_results()
        st.session_state.evaluation_started = False
        st.session_state.finished = False
        st.session_state.current_idx = 0
        st.rerun()
