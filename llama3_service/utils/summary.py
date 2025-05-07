from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_summary(content: str) -> str:
    # This is a placeholder for the actual LLaMA3 model integration
    # In a real implementation, this would call the LLaMA3 model
    return f"Summary of: {content[:100]}..." 