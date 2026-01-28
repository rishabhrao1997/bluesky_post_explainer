"""Structured data model for Bluesky post content"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from config.prompts import SYSTEM_PROMPT


@dataclass
class ImageInfo:
    """Information about an image in a post"""
    url: str
    alt_text: str
    is_repost: bool


@dataclass
class ExternalLinkInfo:
    """Information about an external link in a post"""
    url: str
    content: Optional[str]
    is_repost: bool


@dataclass
class PostContent:
    """Structured representation of a Bluesky post with all collated information"""
    text: str
    author_handle: str
    author_name: Optional[str]
    images: List[ImageInfo]
    external_links: List[ExternalLinkInfo]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format (for backward compatibility)"""
        result = {
            "text": self.text,
            "author_handle": self.author_handle,
            "author_name": self.author_name,
            "image_urls": [
                {
                    "url": img.url,
                    "alt": img.alt_text,
                    "is_repost": img.is_repost
                }
                for img in self.images
            ],
            "external_content": [link.content for link in self.external_links] if isinstance(self.external_links, list) else self.external_links.content if self.external_links else None
        }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostContent":
        """Create PostContent from dictionary format"""
        images = []
        for img_data in data.get("image_urls", []):
            if isinstance(img_data, dict):
                images.append(ImageInfo(
                    url=img_data.get("url", ""),
                    alt_text=img_data.get("alt", ""),
                    is_repost=img_data.get("is_repost", False)
                ))
        
        external_links = []
        # Handle new format with external_links list
        if "external_links" in data:
            for link_data in data.get("external_links", []):
                if isinstance(link_data, dict):
                    external_links.append(ExternalLinkInfo(
                        url=link_data.get("url", ""),
                        content=link_data.get("content"),
                        is_repost=link_data.get("is_repost", False)
                    ))
        # Handle old format with single external_url/external_content
        elif data.get("external_url"):
            external_links.append(ExternalLinkInfo(
                url=data.get("external_url", ""),
                content=data.get("external_content"),
                is_repost=False  # Old format doesn't have this info
            ))
        
        return cls(
            text=data.get("text", ""),
            author_handle=data.get("author_handle", ""),
            author_name=data.get("author_name"),
            images=images,
            external_links=external_links
        )
    
    def to_provider_messages(self) -> List[Dict[str, Any]]:
        """Convert PostContent to provider-agnostic message format
        
        Returns:
            List of messages in the format:
            [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "..."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "..."},
                        {"type": "input_text", "text": "Image 1 description"},
                        {"type": "input_image", "image_url": "..."},
                        ...
                    ]
                }
            ]
        """
        # Build main post text
        main_text = f"Post by @{self.author_handle} ({self.author_name or 'Unknown'}): '{self.text}'"
        
        # Build user content with interleaved images
        user_content: List[Dict[str, Any]] = []
        
        # Add external links with their descriptions interleaved
        for idx, link in enumerate(self.external_links, 1):
            if not link.content:
                continue

            link_type = "reposted" if link.is_repost else "original"
            
            # Build external link description
            link_description = f"External Link {idx} ({link_type}): {link.url}"            
            
            link_full_text = f"{link_description}\n\nCONTENT OF LINKED ARTICLE: \n{link.content}"
            main_text += f"\n\n{link_full_text}"
        
        user_content.append(
            {"type": "input_text", "text": main_text}
        )
        
        # Add images with their descriptions interleaved
        for idx, image in enumerate(self.images, 1):
            image_type = "reposted" if image.is_repost else "original"
            
            # Build image description
            desc_parts = [f"Image {idx} ({image_type})"]
            if image.alt_text:
                desc_parts.append(f"Alt Text: {image.alt_text}")
            
            image_description = " | ".join(desc_parts)
            
            # Add description text, then the image
            user_content.append(
                {"type": "input_text", "text": image_description}
            )
            user_content.append(
                {"type": "input_image", "image_url": image.url}
            )
        
        return [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
