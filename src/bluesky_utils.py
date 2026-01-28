import requests
import logging
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, Optional, Callable, List, Union
from src.post_content import PostContent, ImageInfo, ExternalLinkInfo
from src.embed_types import EmbedType
from bs4 import BeautifulSoup
from config.constants import (
    BSKY_IDENTITY_API,
    BSKY_FEED_API,
    REQUEST_TIMEOUT,
)
from src.utils import retry_on_failure, fetch_url_text

logger = logging.getLogger(__name__)


def _get_embed_type(embed: Dict[str, Any]) -> Optional[EmbedType]:
    """Get the embed type from an embed dictionary"""
    embed_type_str = embed.get('$type')
    if not embed_type_str:
        return None
    try:
        return EmbedType(embed_type_str)
    except ValueError:
        return None


def _is_repost(embed: Dict[str, Any]) -> bool:
    """Check if an embed is a repost"""
    embed_type = _get_embed_type(embed)
    return embed_type == EmbedType.RECORD_VIEW


def _extract_images_from_images_embed(images_embed: Dict[str, Any], is_repost: bool) -> List[Dict[str, Any]]:
    """Extract images from an images embed structure"""
    images = []
    try:
        for image in images_embed.get('images', []):
            if 'fullsize' in image:
                images.append({
                    'url': image['fullsize'],
                    'alt': image.get('alt', ''),
                    'is_repost': is_repost
                })
    except (KeyError, TypeError):
        pass
    return images


def _extract_external_link_from_external_embed(
    external_embed: Dict[str, Any], 
    fetch_url_text_func: Callable[[str], Optional[str]],
    is_repost: bool,
    existing_urls: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Extract external link from an external embed structure"""
    external_url = external_embed.get('external', {}).get('uri')
    if not external_url:
        return None
    
    # Check if we already have this URL
    if existing_urls and external_url in existing_urls:
        return None
    
    logger.info(f"Found external link {'in reposted content' if is_repost else 'in the post'}: {external_url}")
    return {
        'url': external_url,
        'content': fetch_url_text_func(external_url),
        'is_repost': is_repost
    }


def _extract_from_embeds_array(
    embeds: List[Dict[str, Any]],
    is_repost: bool,
    fetch_url_text_func: Optional[Callable[[str], Optional[str]]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract images and external links from an embeds array
    
    Returns:
        Tuple of (images_list, external_links_list)
    """
    images = []
    external_links = []
    existing_urls = []
    
    for embed_item in embeds:
        embed_type = _get_embed_type(embed_item)
        if not embed_type:
            continue
        
        # Handle recordWithMedia type
        if embed_type == EmbedType.RECORD_WITH_MEDIA_VIEW:
            # Extract images from media
            media = embed_item.get('media', {})
            media_type = _get_embed_type(media)
            if media_type == EmbedType.IMAGES_VIEW:
                images.extend(_extract_images_from_images_embed(media, is_repost))
            
            # Extract external link from nested record if present
            if fetch_url_text_func:
                record_embed = embed_item.get('record', {})
                if isinstance(record_embed, dict):
                    record_value = record_embed.get('record', {}).get('value', {})
                    record_value_embed = record_value.get('embed', {})
                    nested_type = _get_embed_type(record_value_embed)
                    if nested_type == EmbedType.EXTERNAL:
                        link = _extract_external_link_from_external_embed(
                            record_value_embed, fetch_url_text_func, is_repost, existing_urls
                        )
                        if link:
                            external_links.append(link)
                            existing_urls.append(link['url'])
        
        # Handle direct images embed
        elif embed_type == EmbedType.IMAGES_VIEW:
            images.extend(_extract_images_from_images_embed(embed_item, is_repost))
        
        # Handle direct external embed
        elif embed_type == EmbedType.EXTERNAL_VIEW and fetch_url_text_func:
            link = _extract_external_link_from_external_embed(
                embed_item, fetch_url_text_func, is_repost, existing_urls
            )
            if link:
                external_links.append(link)
                existing_urls.append(link['url'])
    
    return images, external_links

def parse_bluesky_url(url: str) -> Tuple[str, str]:
    """Parse the Bluesky URL and return the Account handle and Post ID
    
    Args:
        url: The Bluesky URL to parse
    
    Returns:
        A tuple containing the Account handle and Post ID
    """
    path = urlparse(url).path.split('/')
    try:
        handle = path[path.index('profile') + 1]
        post_id = path[path.index('post') + 1]
        return handle, post_id
    except (ValueError, IndexError):
        raise ValueError(f"Invalid Bluesky URL format: {url}")


@retry_on_failure()
def resolve_did(handle: str) -> str:
    """Resolve the DID for a given Bluesky handle
    
    Args:
        handle: The Bluesky handle to resolve the DID for
    
    Returns:
        The DID for the given Bluesky handle
    """
    resp = requests.get(
        BSKY_IDENTITY_API,
        params={"handle": handle},
        timeout=REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()['did']


@retry_on_failure()
def get_post_thread(did: str, post_id: str) -> Dict[str, Any]:
    """Get the post thread for a given DID and Post ID
    
    Args:
        did: The DID to get the post thread for
        post_id: The Post ID to get the post thread for
    
    Returns:
        The post thread for the given DID and Post ID
    """
    uri = f"at://{did}/app.bsky.feed.post/{post_id}"
    resp = requests.get(
        BSKY_FEED_API,
        params={"uri": uri},
        timeout=REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


def extract_images(post: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all images from the post with metadata
    
    Handles both regular posts and reposts (embedded records).
    
    Args:
        post: The post to extract the images from
    
    Returns:
        A list of dictionaries containing:
        - 'url': The fullsize image URL
        - 'alt': The alt text for the image (empty string if not available)
        - 'is_repost': Boolean indicating if the image is from reposted content
    """
    images = []
    embed = post.get('embed', {})
    embed_type = _get_embed_type(embed)
    is_repost = _is_repost(embed)
    
    # Handle regular posts with direct images (legacy format - images directly in embed)
    if 'images' in embed:
        images.extend(_extract_images_from_images_embed(embed, is_repost=False))
    
    # Handle reposts
    if is_repost:
        record = embed.get('record', {})
        embeds = record.get('embeds', [])
        repost_images, _ = _extract_from_embeds_array(embeds, is_repost=True)
        images.extend(repost_images)
    
    # Handle recordWithMedia type in regular posts
    if embed_type == EmbedType.RECORD_WITH_MEDIA_VIEW:
        media = embed.get('media', {})
        media_type = _get_embed_type(media)
        if media_type == EmbedType.IMAGES_VIEW:
            images.extend(_extract_images_from_images_embed(media, is_repost=False))
    
    return images


def extract_repost_text(post: Dict[str, Any]) -> Optional[str]:
    """Extract text from reposted content
    
    Args:
        post: The post to extract reposted text from
    
    Returns:
        The text from the reposted content, or None if not a repost
    """
    embed = post.get('embed', {})
    
    if _is_repost(embed):
        record = embed.get('record', {})
        value = record.get('value', {})
        repost_text = value.get('text', '')
        if repost_text:
            return repost_text
    
    return None


def _extract_external_from_nested_record(
    record_embed: Dict[str, Any],
    fetch_url_text_func: Callable[[str], Optional[str]],
    is_repost: bool,
    existing_urls: List[str]
) -> Optional[Dict[str, Any]]:
    """Extract external link from nested record structure"""
    if not isinstance(record_embed, dict):
        return None
    
    # Try record.record.value path
    nested_record = record_embed.get('record', {})
    if isinstance(nested_record, dict):
        nested_value = nested_record.get('value', {})
        nested_embed = nested_value.get('embed', {})
        nested_type = _get_embed_type(nested_embed)
        if nested_type == EmbedType.EXTERNAL:
            return _extract_external_link_from_external_embed(
                nested_embed, fetch_url_text_func, is_repost, existing_urls
            )
    return None


def extract_external_links(post: Dict[str, Any], fetch_url_text_func: Callable[[str], Optional[str]]) -> List[Dict[str, Any]]:
    """Extract all external links from the post with metadata
    
    Handles both regular posts and reposts (embedded records).
    
    Args:
        post: The post to extract the external links from
        fetch_url_text_func: The function to fetch the text from the external link
    
    Returns:
        A list of dictionaries containing:
        - 'url': The external link URL
        - 'content': The fetched content from the external link
        - 'is_repost': Boolean indicating if the link is from reposted content
    """
    external_links = []
    embed = post.get('embed', {})
    embed_type = _get_embed_type(embed)
    is_repost = _is_repost(embed)
    existing_urls = []
    
    # Handle regular posts with direct external links
    if embed_type == EmbedType.EXTERNAL_VIEW:
        link = _extract_external_link_from_external_embed(embed, fetch_url_text_func, False, existing_urls)
        if link:
            external_links.append(link)
            existing_urls.append(link['url'])
    
    # Handle reposts
    if is_repost:
        record = embed.get('record', {})
        
        # Check embeds array for external links (processed view)
        embeds = record.get('embeds', [])
        _, repost_links = _extract_from_embeds_array(embeds, is_repost=True, fetch_url_text_func=fetch_url_text_func)
        external_links.extend(repost_links)
        existing_urls.extend([link['url'] for link in repost_links])
        
        # Also check the value.embed path (raw data structure)
        value = record.get('value', {})
        value_embed = value.get('embed', {})
        value_embed_type = _get_embed_type(value_embed)
        
        # Handle external embed in value.embed
        if value_embed_type == EmbedType.EXTERNAL:
            link = _extract_external_link_from_external_embed(
                value_embed, fetch_url_text_func, True, existing_urls
            )
            if link:
                external_links.append(link)
                existing_urls.append(link['url'])
        
        # Handle recordWithMedia in value.embed - check nested record
        if value_embed_type == EmbedType.RECORD_WITH_MEDIA:
            nested_record_embed = value_embed.get('record', {})
            link = _extract_external_from_nested_record(
                nested_record_embed, fetch_url_text_func, True, existing_urls
            )
            if link:
                external_links.append(link)
                existing_urls.append(link['url'])
    
    # Handle recordWithMedia type in regular posts (not reposts)
    if embed_type == EmbedType.RECORD_WITH_MEDIA_VIEW:
        record_embed = embed.get('record', {})
        link = _extract_external_from_nested_record(
            record_embed, fetch_url_text_func, False, existing_urls
        )
        if link:
            external_links.append(link)
    
    return external_links


def get_post_details(url: str, return_dict: bool = False) -> Union[PostContent, Dict[str, Any]]:
    """Get the details of a given Bluesky post
    
    Args:
        url: The URL of the Bluesky post to get the details of
        return_dict: If True, returns dictionary format (for backward compatibility)
    
    Returns:
        PostContent object (or dict if return_dict=True)
        Example input: https://bsky.app/profile/twins0.bsky.social/post/3mdd6n2my3s2e
    """
    try:
        handle, post_id = parse_bluesky_url(url)
        did = resolve_did(handle)
        thread_data = get_post_thread(did, post_id)
        
        post = thread_data['thread']['post']
        record = post.get('record', {})
        
        image_data = extract_images(post)
        external_link_data = extract_external_links(post, fetch_url_text)
        
        # Extract main post text
        main_text = record.get("text", "")
        
        # Extract reposted text if this is a repost
        repost_text = extract_repost_text(post)
        
        # Combine text: main post text + reposted text (if present)
        combined_text = main_text
        if repost_text:
            if main_text:
                combined_text = f"{main_text}\n\n[Reposted content]: {repost_text}"
            else:
                combined_text = f"[Reposted content]: {repost_text}"
        
        # Convert image data to ImageInfo objects
        images = [
            ImageInfo(
                url=img.get("url", ""),
                alt_text=img.get("alt", ""),
                is_repost=img.get("is_repost", False)
            )
            for img in image_data
        ]
        
        # Convert external link data to ExternalLinkInfo objects
        external_links = [
            ExternalLinkInfo(
                url=link.get("url", ""),
                content=link.get("content"),
                is_repost=link.get("is_repost", False)
            )
            for link in external_link_data
        ]
        
        post_content = PostContent(
            text=combined_text,
            author_handle=handle,
            author_name=post.get("author", {}).get("displayName"),
            images=images,
            external_links=external_links
        )
        
        if return_dict:
            return post_content.to_dict()
        return post_content
    except Exception as e:
        if return_dict:
            return {"error": f"Failed to fetch post: {str(e)}"}
        # Return a PostContent with error in text for structured format
        return PostContent(
            text=f"Error: {str(e)}",
            author_handle="",
            author_name=None,
            images=[],
            external_links=[]
        )
