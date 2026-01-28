import time
import logging
import requests
from typing import Callable, Any, Optional
from bs4 import BeautifulSoup
from config.constants import MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT, MAX_EXTERNAL_CONTENT_LENGTH, USER_AGENT_HEADER

logger = logging.getLogger(__name__)



def retry_on_failure(max_attempts: int = MAX_RETRIES, delay: float = RETRY_DELAY) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise last_error
            raise RuntimeError("Unexpected retry loop exit")
        return wrapper
    return decorator


@retry_on_failure(max_attempts=MAX_RETRIES)
def fetch_url_text(url: str) -> Optional[str]:
    """Fetch the text from a given URL"""
    headers = {
        "User-Agent": USER_AGENT_HEADER,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            logger.warning(f"Failed to fetch {url}: status {resp.status_code}")
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        content = soup.select_one('article, main, [role="main"], .article-body, .post-content')
        if content:
            text = content.get_text(separator=' ', strip=True)
        else:
            body = soup.find('body')
            text = body.get_text(separator=' ', strip=True) if body else soup.get_text(separator=' ', strip=True)
        
        text = ' '.join(text.split())
        
        if not text or len(text) < 50:
            return None
        
        if len(text) > MAX_EXTERNAL_CONTENT_LENGTH:
            return text[:MAX_EXTERNAL_CONTENT_LENGTH] + "..."
        
        return text
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None
