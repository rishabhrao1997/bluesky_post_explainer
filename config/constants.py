# Bluesky API endpoints
BSKY_IDENTITY_API: str = "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle"
BSKY_FEED_API: str = "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread"

# Request settings
REQUEST_TIMEOUT: int = 5
MAX_RETRIES: int = 3
RETRY_DELAY: int = 1

# External URL scraping settings
MAX_EXTERNAL_CONTENT_LENGTH: int = 10000
USER_AGENT_HEADER: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# LLM provider settings
DEFAULT_PROVIDER: str = "openai"

# LLM model settings
OPENAI_MODEL: str = "gpt-5.2"
ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
GEMINI_MODEL: str = "gemini-2.5-flash"

# Evaluation models
CITATION_EVALUATION_MODEL: str = "gpt-4.1-mini"
EMBEDDING_MODEL: str = "text-embedding-3-small"
LLM_JUDGE_MODEL: str = "gpt-4.1"
