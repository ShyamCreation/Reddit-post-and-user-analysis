# reddit_utils.py - Centralized utilities for Reddit operations

import praw
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime
import pandas as pd
import numpy as np
from collections import Counter
import re
from urllib.parse import urlparse
from wordcloud import WordCloud, STOPWORDS

# Centralized Reddit API client
def get_reddit_instance():
    return praw.Reddit(
        client_id="ZopQv_qPEhjiJrWY3f-IjA",
        client_secret="uuHCzVuETxnIYv0KBFjaf92r__3wIQ",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'"
    )


# URL parsing utilities
def extract_post_id(post_url):
    """Extract the post ID from a Reddit post URL."""
    parsed_url = urlparse(post_url)
    path_parts = parsed_url.path.strip('/').split('/')

    # Ensure the structure matches expected format: /r/{subreddit}/comments/{post_id}/{title}/
    if len(path_parts) >= 4 and path_parts[2] == "comments":
        return path_parts[3]  # Post ID is the 4th element

    return None  # Return None if URL format is incorrect

# Helper function for converting matplotlib plot to base64 image
def plot_to_base64(figure=None, close_figure=True):
    """Convert a matplotlib figure to a base64 encoded string."""
    buffer = BytesIO()
    
    if figure is not None:
        plt.figure(figure)
    
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    
    if close_figure:
        plt.close()
        
    buffer.close()
    
    # Encode the bytes as base64
    return base64.b64encode(image_png).decode('utf-8')

# Text processing utilities
def clean_reddit_text(text):
    """Clean and normalize Reddit text content for analysis."""
    # Remove URLs from the text
    text = re.sub(r'http\S+', '', text)
    # Remove common Reddit formatting
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove markdown links
    text = re.sub(r'&amp;', '&', text)  # Replace HTML entities
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    return text

# Default stopwords for Reddit content analysis
def get_default_stopwords(custom_excluded_words=None):
    """Get default stopwords for Reddit content analysis."""
    stopwords = set(STOPWORDS)
    default_excluded = {"deleted", "removed", "edit", "permalink", "http", "https", "www"}
    
    stopwords.update(default_excluded)
    
    if custom_excluded_words:
        stopwords.update(custom_excluded_words)
    
    return stopwords

# Standardized error handling
def safe_execute(func, *args, **kwargs):
    """Execute a function safely, returning None and error message if exception occurs."""
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        return None, str(e)