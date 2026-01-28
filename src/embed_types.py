"""Enum for Bluesky embed types"""
from enum import Enum


class EmbedType(Enum):
    """Bluesky embed type constants"""
    # View types (processed/display format)
    RECORD_VIEW = "app.bsky.embed.record#view"
    RECORD_WITH_MEDIA_VIEW = "app.bsky.embed.recordWithMedia#view"
    IMAGES_VIEW = "app.bsky.embed.images#view"
    EXTERNAL_VIEW = "app.bsky.embed.external#view"
    
    # Raw types (data format)
    RECORD = "app.bsky.embed.record"
    RECORD_WITH_MEDIA = "app.bsky.embed.recordWithMedia"
    IMAGES = "app.bsky.embed.images"
    EXTERNAL = "app.bsky.embed.external"
    
    def is_view_type(self) -> bool:
        """Check if this is a view type (ends with #view)"""
        return self.value.endswith("#view")
    
    def get_raw_type(self) -> "EmbedType":
        """Get the raw type equivalent (without #view)"""
        if self.is_view_type():
            raw_value = self.value.replace("#view", "")
            for embed_type in EmbedType:
                if embed_type.value == raw_value:
                    return embed_type
        return self
    
    def get_view_type(self) -> "EmbedType":
        """Get the view type equivalent (with #view)"""
        if not self.is_view_type():
            view_value = f"{self.value}#view"
            for embed_type in EmbedType:
                if embed_type.value == view_value:
                    return embed_type
        return self
