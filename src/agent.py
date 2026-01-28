import logging
from typing import Optional
from src.bluesky_utils import get_post_details
from src.post_content import PostContent
from src.provider import LLMProvider, get_provider
from config.constants import DEFAULT_PROVIDER

logger = logging.getLogger(__name__)


class BlueskyAgent:
    """A class that explains Bluesky posts using any LLM provider"""
    def __init__(self, provider: Optional[LLMProvider] = None, provider_name: Optional[str] = None, **provider_kwargs) -> None:
        """Initialize the BlueskyAgent
        
        Args:
            provider: Optional LLMProvider instance. If not provided, will create one using provider_name
            provider_name: Name of the provider to use ("openai", "anthropic", "gemini"). 
                          If None, uses DEFAULT_PROVIDER from constants.
            **provider_kwargs: Additional kwargs to pass to provider initialization
        """
        if provider is not None:
            self.provider = provider
            provider_name = provider_name or DEFAULT_PROVIDER
        else:
            self.provider = get_provider(provider_name, **provider_kwargs)
            provider_name = provider_name or DEFAULT_PROVIDER
        logger.info(f"Initialized BlueskyAgent with provider: {provider_name}")

    def explain(self, url: str, post_content: Optional[PostContent] = None) -> str:
        """The main function that explains a Bluesky post
        Args:
            url: The URL of the Bluesky post to explain
        
        Returns:
            The explanation for the Bluesky post
        """
        logger.info(f"Fetching post: {url}...")
        if post_content is None:
            post_content = get_post_details(url)
        
        # Check for errors
        if isinstance(post_content, PostContent) and post_content.text.startswith("Error:"):
            return post_content.text

        # Convert PostContent to provider messages
        messages = post_content.to_provider_messages()
        
        logger.info("Generating explanation...")
        explanation = self.provider.generate(
            messages=messages,
            tools=[{"type": "web_search"}],
            tool_choice={"type": "web_search"}
        )
        
        return explanation
