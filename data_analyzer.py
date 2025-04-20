import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
from scipy.stats import linregress
from textblob import TextBlob

# Engagement analysis: Mean and variance of engagement by content type
def analyze_post_engagement(posts_df):
    if posts_df.empty:
        return pd.Series()

    engagement_by_type = posts_df.groupby('type')['engagement'].agg(['mean', 'std']).sort_values('mean', ascending=False)
    return engagement_by_type

# Sentiment analysis of post content (positive, negative, neutral)
def sentiment_analysis(posts_df):
    if posts_df.empty or 'content' not in posts_df.columns:
        return {}

    sentiments = []
    for post in posts_df['content']:
        sentiment = TextBlob(post).sentiment.polarity
        if sentiment > 0:
            sentiments.append('Positive')
        elif sentiment < 0:
            sentiments.append('Negative')
        else:
            sentiments.append('Neutral')

    posts_df['sentiment'] = sentiments
    sentiment_counts = posts_df['sentiment'].value_counts()
    return sentiment_counts

# Posting patterns: Average engagement by posting time and correlation coefficient
def analyze_posting_patterns(posts_df):
    if posts_df.empty or 'time' not in posts_df.columns:
        return pd.Series()

    posts_df['hour'] = posts_df['time'].apply(lambda x: int(x.split(':')[0]))

    engagement_by_hour = posts_df.groupby('hour')['engagement'].mean()
    correlation = np.corrcoef(posts_df['hour'], posts_df['engagement'])[0][1]

    return engagement_by_hour, correlation

# Content length vs engagement: Linear regression between content length and engagement
def analyze_content_length(posts_df):
    if posts_df.empty or 'content_length_type' not in posts_df.columns:
        return pd.Series()

    # Grouping the posts by content length type and calculating average engagement for each
    engagement_by_length_type = posts_df.groupby('content_length_type')['engagement'].mean().sort_values(ascending=False)

    # Perform linear regression on content length type vs engagement
    # For this, we need to map content_length_type to numerical values
    length_type_map = {'short': 1, 'medium': 2, 'long': 3}
    posts_df['length_type_numeric'] = posts_df['content_length_type'].map(length_type_map)

    if posts_df['length_type_numeric'].nunique() > 1:
        slope, intercept, r_value, p_value, std_err = linregress(posts_df['length_type_numeric'], posts_df['engagement'])
        correlation = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value
        }
    else:
        correlation = {
            'slope': None,
            'intercept': None,
            'r_squared': None,
            'p_value': None,
            'message': 'Not enough variation in post lengths for regression'
        }

    return engagement_by_length_type,  correlation 

# Content themes: Analyzing key themes from content
def analyze_content_themes(posts_df):
    if posts_df.empty or 'content' not in posts_df.columns:
        return {}

    content_themes = {
        "Positive": {"keywords": ["good", "great", "love", "excellent", "success"], "count": 0, "observation": ""},
        "Negative": {"keywords": ["bad", "poor", "failure", "disappointing"], "count": 0, "observation": ""},
        "Neutral": {"keywords": ["okay", "fine", "decent", "neutral"], "count": 0, "observation": ""}
    }

    for index, row in posts_df.iterrows():
        content = row['content'].lower()
        for theme, data in content_themes.items():
            if any(keyword in content for keyword in data["keywords"]):
                content_themes[theme]["count"] += 1

    total_posts = len(posts_df)
    for theme, data in content_themes.items():
        data["observation"] = f"{data['count']} out of {total_posts} posts are considered {theme.lower()}."

    return content_themes

# Hashtag analysis: Most common hashtags and their engagement correlation
def analyze_hashtags(posts_df):
    if posts_df.empty or 'hashtags_list' not in posts_df.columns:
        return []

    all_hashtags = []
    for hashtags in posts_df['hashtags_list']:
        if isinstance(hashtags, list):
            all_hashtags.extend(hashtags)
    
    hashtag_counts = Counter(all_hashtags)
    hashtag_engagement = {}

    for hashtag in hashtag_counts:
        avg_engagement = posts_df[posts_df['hashtags_list'].apply(lambda x: hashtag in x)]['engagement'].mean()
        hashtag_engagement[hashtag] = avg_engagement

    return hashtag_counts.most_common(5), hashtag_engagement

# Optimal posting time based on engagement (with a correlation coefficient)
def get_optimal_posting_time(posts_df):
    if posts_df.empty or 'hour' not in posts_df.columns:
        return None

    avg_engagement_by_hour = posts_df.groupby('hour')['engagement'].mean()
    optimal_hour = avg_engagement_by_hour.idxmax()
    return f"{optimal_hour}:00" 