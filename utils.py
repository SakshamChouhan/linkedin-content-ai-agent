import re
import pandas as pd
import os
from datetime import datetime
import urllib.parse

def parse_url(url):
    """
    Extracts the username from a LinkedIn profile URL.
    
    Args:
        url (str): LinkedIn profile URL
        
    Returns:
        str: LinkedIn username
    """
    # Extract username from different LinkedIn URL formats
    patterns = [
        r'linkedin\.com/in/([^/\?]+)',  # Standard profile URL
        r'linkedin\.com/company/([^/\?]+)'  # Company page URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no match, return the domain part
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc
    except:
        return url.replace('https://', '').replace('http://', '').split('/')[0]

def clean_text(text):
    """
    Cleans and normalizes text.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters that might cause issues in analysis
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\[\]\{\}\'\"\#\@]', '', text)
    
    return text

def load_profile_data():
    """
    Loads profile data from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing profile data
    """
    from database import get_profiles
    return get_profiles()

def extract_engagement_metrics(text):
    """
    Extracts engagement metrics from a text.
    
    Args:
        text (str): Text containing engagement metrics
        
    Returns:
        dict: Dictionary of engagement metrics
    """
    metrics = {
        'likes': 0,
        'comments': 0,
        'shares': 0
    }
    
    # Pattern to match numbers followed by metric name
    patterns = {
        'likes': r'(\d+)(?:\s+|\s*\+\s*)(?:like|likes)',
        'comments': r'(\d+)(?:\s+|\s*\+\s*)(?:comment|comments)',
        'shares': r'(\d+)(?:\s+|\s*\+\s*)(?:share|shares|repost|reposts)'
    }
    
    for metric, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metrics[metric] = int(match.group(1))
    
    return metrics

def calculate_engagement_score(likes, comments, shares):
    """
    Calculates an engagement score based on likes, comments, and shares.
    
    Args:
        likes (int): Number of likes
        comments (int): Number of comments
        shares (int): Number of shares
        
    Returns:
        float: Engagement score
    """
    # Weighted formula: likes + (comments * 3) + (shares * 5)
    # This weights engagement actions by their relative value
    return likes + (comments * 3) + (shares * 5)

def format_date_time(date_str, time_str=None):
    """
    Formats date and time strings consistently.
    
    Args:
        date_str (str): Date string
        time_str (str, optional): Time string
        
    Returns:
        tuple: Formatted date and time
    """
    try:
        # Parse date
        if isinstance(date_str, str):
            if 'ago' in date_str.lower():
                # Handle relative dates
                if 'hour' in date_str.lower() or 'hr' in date_str.lower():
                    hours_ago = int(re.search(r'(\d+)', date_str).group(1))
                    date_obj = datetime.now()
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                elif 'day' in date_str.lower() or 'd' in date_str.lower():
                    days_ago = int(re.search(r'(\d+)', date_str).group(1))
                    date_obj = datetime.now()
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                else:
                    formatted_date = datetime.now().strftime('%Y-%m-%d')
            else:
                # Try to parse absolute date
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_str
                except:
                    try:
                        date_obj = datetime.strptime(date_str, '%b %d, %Y')
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        formatted_date = date_str
        else:
            formatted_date = str(date_str)
        
        # Parse time
        if time_str:
            try:
                time_obj = datetime.strptime(time_str, '%H:%M')
                formatted_time = time_obj.strftime('%H:%M')
            except:
                formatted_time = time_str
        else:
            formatted_time = None
        
        return formatted_date, formatted_time
    
    except Exception as e:
        print(f"Error formatting date/time: {str(e)}")
        return str(date_str), time_str
