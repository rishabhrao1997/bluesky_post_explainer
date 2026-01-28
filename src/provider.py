import os
import base64
import urllib.request
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Set

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

from config.constants import (
    DEFAULT_PROVIDER,
    OPENAI_MODEL,
    ANTHROPIC_MODEL,
    GEMINI_MODEL
)

# Supported models per provider
SUPPORTED_MODELS: Dict[str, Set[str]] = {
    "openai": {
        "gpt-5.2",
        "gpt-4.1",
        "gpt-4.1-mini"
    },
    "anthropic": {
        "claude-sonnet-4-5",
    },
    "gemini": {
        "gemini-2.5-flash",
    },
}


def validate_provider_model(provider_name: str, model_name: str) -> None:
    """Validate that a provider supports a given model.
    
    Args:
        provider_name: Name of the provider (e.g., "openai", "anthropic", "gemini")
        model_name: Name of the model to validate
        
    Raises:
        ValueError: If the provider doesn't support the model
    """
    provider_lower = provider_name.lower()
    if provider_lower not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unknown provider: {provider_lower}. "
            f"Supported providers: {', '.join(SUPPORTED_MODELS.keys())}"
        )
    
    supported = SUPPORTED_MODELS[provider_lower]
    if model_name not in supported:
        raise ValueError(
            f"Model '{model_name}' is not supported by provider '{provider_lower}'. "
            f"Supported models: {', '.join(sorted(supported))}"
        )


def _fetch_image_as_base64(image_url: str) -> Tuple[str, str]:
    """Fetch image from URL and return base64 data with media type."""
    req = urllib.request.Request(image_url)
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            
            if content_type.startswith("image/"):
                mime_type = content_type
            else:
                ext = image_url.lower().rsplit(".", 1)[-1].split("?")[0]
                mime_map: Dict[str, str] = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "gif": "image/gif",
                    "webp": "image/webp",
                }
                mime_type = mime_map.get(ext, "image/jpeg")
            
            b64_data = base64.b64encode(data).decode("utf-8")
            return b64_data, mime_type
    except Exception as e:
        raise ValueError(f"Failed to fetch image: {e}")


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, Any]], **kwargs: Any) -> str:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        if OpenAI is None:
            raise ImportError("openai package required")
        self.client = OpenAI(api_key=key)
        model_name = model or OPENAI_MODEL
        validate_provider_model("openai", model_name)
        self.model: str = model_name
    
    def generate(self, messages: List[Dict[str, Any]], **kwargs: Any) -> str:
        tools = kwargs.get("tools", [{"type": "web_search"}])
        tool_choice = kwargs.get("tool_choice", {"type": "web_search"})
        
        resp = self.client.responses.create(
            model=self.model,
            tools=tools,
            tool_choice=tool_choice,
            input=messages
        )
        return resp.output_text


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")
        
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = Anthropic(api_key=key)
        model_name = model or ANTHROPIC_MODEL
        validate_provider_model("anthropic", model_name)
        self.model: str = model_name
    
    def generate(self, messages: List[Dict[str, Any]], **kwargs: Any) -> str:
        converted: List[Dict[str, Any]] = []
        system: Optional[str] = None
        
        for msg in messages:
            role = msg.get("role", "")
            content_items = msg.get("content", [])
            
            if role == "system":
                for item in content_items:
                    if item.get("type") == "input_text":
                        system = item.get("text")
                        break
            elif role in ("user", "assistant"):
                parts: List[Dict[str, Any]] = []
                for item in content_items:
                    if item.get("type") == "input_text":
                        parts.append({"type": "text", "text": item.get("text", "")})
                    elif item.get("type") == "input_image":
                        img_url = item.get("image_url")
                        if img_url:
                            try:
                                img_data, mime = _fetch_image_as_base64(img_url)
                                parts.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime,
                                        "data": img_data
                                    }
                                })
                            except Exception as e:
                                print(f"Warning: image load failed {img_url}: {e}")
                
                if parts:
                    converted.append({"role": role, "content": parts})
        
        params: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": converted
        }
        
        if system:
            params["system"] = system
        
        tools = kwargs.get("tools", [])
        tool_choice = kwargs.get("tool_choice")
        needs_search = (
            any(t.get("type") == "web_search" for t in tools) or
            (tool_choice and tool_choice.get("type") == "web_search")
        )
        
        if needs_search:
            # Anthropic requires the versioned web_search tool tag
            search_tool: Dict[str, Any] = {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": kwargs.get("max_uses", 5)
            }
            params["tools"] = [search_tool]
        
        resp = self.client.messages.create(**params)
        
        text_parts: List[str] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
        
        return "".join(text_parts) if text_parts else ""


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("google-genai required: pip install google-genai")
        
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
        
        self._client = genai.Client(api_key=key)
        model_name = model or GEMINI_MODEL
        validate_provider_model("gemini", model_name)
        self.model_name: str = model_name
        self._types = types
    
    def generate(self, messages: List[Dict[str, Any]], **kwargs: Any) -> str:
        types = self._types
        system_msg: Optional[str] = None
        contents: List[Any] = []
        
        for msg in messages:
            if msg.get("role") == "system":
                for item in msg.get("content", []):
                    if item.get("type") == "input_text":
                        system_msg = item.get("text")
                        break
        
        for msg in messages:
            role = msg.get("role", "")
            if role == "system":
                continue
            
            content_items = msg.get("content", [])
            parts: List[Any] = []
            
            for item in content_items:
                if item.get("type") == "input_text":
                    parts.append(types.Part(text=item.get("text", "")))
                elif item.get("type") == "input_image":
                    img_url = item.get("image_url")
                    if img_url:
                        try:
                            img_data_b64, mime = _fetch_image_as_base64(img_url)
                            img_bytes = base64.b64decode(img_data_b64)
                            parts.append(
                                types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes))
                            )
                        except Exception as e:
                            print(f"Warning: image load failed {img_url}: {e}")
            
            if not parts:
                continue
            
            gemini_role = "user" if role == "user" else "model"
            contents.append(types.Content(role=gemini_role, parts=parts))
        
        tools = kwargs.get("tools", [])
        tool_choice = kwargs.get("tool_choice")
        needs_search = (
            any(t.get("type") == "web_search" for t in tools) or
            (tool_choice and tool_choice.get("type") == "web_search")
        )
        
        config_kwargs: Dict[str, Any] = {
            "temperature": kwargs.get("temperature", 1.0),
        }
        if system_msg:
            config_kwargs["system_instruction"] = system_msg
        if needs_search:
            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch()),
                {"url_context": {}}
            ]
        
        config = types.GenerateContentConfig(**config_kwargs)
        
        if contents:
            resp = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
        else:
            prompt = system_msg or ""
            resp = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        
        if resp.text:
            return resp.text
        return ""


def get_provider(provider_name: Optional[str] = None, **kwargs: Any) -> LLMProvider:
    """Get an LLM provider instance.
    
    Args:
        provider_name: Name of the provider to use. If None, uses DEFAULT_PROVIDER from constants.
        **kwargs: Additional arguments to pass to the provider (e.g., api_key, model)
        
    Returns:
        An instance of the requested LLMProvider
        
    Raises:
        ValueError: If the provider is unknown or if the model is not supported by the provider
    """
    name = (provider_name or DEFAULT_PROVIDER).lower()
    
    # Validate model if provided
    if "model" in kwargs:
        validate_provider_model(name, kwargs["model"])
    
    if name == "openai":
        return OpenAIProvider(**kwargs)
    elif name == "anthropic":
        return AnthropicProvider(**kwargs)
    elif name == "gemini":
        return GeminiProvider(**kwargs)
    else:
        raise ValueError(
            f"Unknown provider: {name}. "
            f"Supported providers: openai, anthropic, gemini"
        )
