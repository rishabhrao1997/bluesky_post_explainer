#!/usr/bin/env python3
"""
Script to run the Bluesky agent and explain a post.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.agent import BlueskyAgent
from config.constants import DEFAULT_PROVIDER


def main() -> None:
    """Main function to run the agent."""
    parser = argparse.ArgumentParser(description="Explain Bluesky posts with context")
    parser.add_argument(
        "--url",
        help="Bluesky post URL",
        required=True,
        type=str
    )
    parser.add_argument(
        "--provider",
        help=f"LLM provider to use (default: {DEFAULT_PROVIDER})",
        required=False,
        default=DEFAULT_PROVIDER,
        type=str
    )
    args = parser.parse_args()
    
    agent = BlueskyAgent(provider_name=args.provider)
    result = agent.explain(args.url)
    print("\n--- RESULT ---")
    print(result)


if __name__ == "__main__":
    main()
