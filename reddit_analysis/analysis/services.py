import praw
import matplotlib.pyplot as plt
import base64
import pandas as pd
import numpy as np
import re
from io import BytesIO
from datetime import datetime
from wordcloud import WordCloud, STOPWORDS
from collections import Counter
from .utils import (
    get_reddit_instance,
    extract_post_id,
    clean_reddit_text,
    get_default_stopwords,
    plot_to_base64,
)


def fetch_subreddit_comments(subreddit_name, limit=100):
    reddit = get_reddit_instance()
    subreddit = reddit.subreddit(subreddit_name)
    
    comments_data = []
    try:
        for comment in subreddit.comments(limit=limit):
            comments_data.append({
                "comment_id": comment.id,
                "body": comment.body,
                "score": comment.score,
                "subreddit": comment.subreddit.display_name,
                "created_utc": comment.created_utc,
                "parent_id": comment.parent_id,
                "link_id": comment.link_id,
                "permalink": f"https://www.reddit.com{comment.permalink}",
                "edited": bool(comment.edited),
                "awards": comment.all_awardings,
            })
    except Exception as e:
        pass
    
    return comments_data

def fetch_user_data(username):
    reddit = get_reddit_instance()
    
    try:
        user = reddit.redditor(username)
        
        # Karma data
        post_karma = user.link_karma
        comment_karma = user.comment_karma
        
        # Recent comments
        recent_comments = []
        all_comments = []  # For timeline analysis
        for comment in user.comments.new(limit=100):  # Increased limit for better timeline
            comment_data = {
                "text": comment.body,
                "score": comment.score,
                "subreddit": comment.subreddit.display_name,
                "created_utc": comment.created_utc,
                "created_date": datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "permalink": f"https://www.reddit.com{comment.permalink}"
            }
            all_comments.append(comment_data)
            if len(recent_comments) < 10:  # Keep only 10 for display
                recent_comments.append({
                    "text": comment.body,
                    "score": comment.score,
                    "subreddit": comment.subreddit.display_name,
                    "created_utc": datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                    "permalink": f"https://www.reddit.com{comment.permalink}"
                })
        
        # Recent posts
        recent_posts = []
        all_posts = []  # For timeline analysis
        for post in user.submissions.new(limit=100):  # Increased limit for better timeline
            post_data = {
                "title": post.title,
                "score": post.score,
                "subreddit": post.subreddit.display_name,
                "created_utc": post.created_utc,
                "created_date": datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "permalink": f"https://www.reddit.com{post.permalink}"
            }
            all_posts.append(post_data)
            if len(recent_posts) < 10:  # Keep only 10 for display
                recent_posts.append({
                    "title": post.title,
                    "score": post.score,
                    "subreddit": post.subreddit.display_name,
                    "created_utc": datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                    "permalink": f"https://www.reddit.com{post.permalink}"
                })
        
        # Most active subreddits
        subreddit_activity = {}
        for comment in all_comments:
            subreddit = comment["subreddit"]
            if subreddit in subreddit_activity:
                subreddit_activity[subreddit] += 1
            else:
                subreddit_activity[subreddit] = 1
        
        top_subreddits = sorted(subreddit_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        
        user_data = {
            'username': username,
            'post_karma': post_karma,
            'comment_karma': comment_karma,
            'recent_comments': recent_comments,
            'recent_posts': recent_posts,
            'all_comments': all_comments,
            'all_posts': all_posts,
            'top_subreddits': top_subreddits,
            'account_created': datetime.fromtimestamp(user.created_utc).strftime('%Y-%m-%d'),
        }
        
        return user_data, None
    except Exception as e:
        return None, str(e)

def generate_karma_chart(username):
    try:
        user_data, error = fetch_user_data(username)
        if error:
            return None
        
        post_karma = user_data['post_karma']
        comment_karma = user_data['comment_karma']
        
        plt.figure(figsize=(6, 4))
        plt.bar(["Post Karma", "Comment Karma"], [post_karma, comment_karma], color=["blue", "red"])
        plt.xlabel("Karma Type")
        plt.ylabel("Karma Score")
        plt.title(f"Post vs. Comment Karma for {username}")
        
        # Save plot to a bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        # Encode the bytes as base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        
        return image_base64
    except Exception as e:
        return None

def generate_subreddit_activity_chart(username):
    try:
        user_data, error = fetch_user_data(username)
        if error:
            return None
            
        subreddits = [s[0] for s in user_data['top_subreddits']]
        activity = [s[1] for s in user_data['top_subreddits']]
        
        plt.figure(figsize=(8, 5))
        plt.bar(subreddits, activity, color="green")
        plt.xlabel("Subreddit")
        plt.ylabel("Number of Comments")
        plt.title(f"Top Subreddits for {username}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        # Encode the bytes as base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        
        return image_base64
    except Exception as e:
        return None
    
def generate_activity_timeline(username):
    try:
        user_data, error = fetch_user_data(username)
        if error:
            return None
        
        # Create DataFrames from user data
        df_posts = pd.DataFrame(user_data['all_posts'])
        df_comments = pd.DataFrame(user_data['all_comments'])
        
        # If we don't have enough data, return None
        if df_posts.empty and df_comments.empty:
            return None
            
        # Convert timestamps to readable dates
        if not df_posts.empty:
            df_posts["date"] = pd.to_datetime(df_posts["created_utc"], unit="s").dt.date
        
        if not df_comments.empty:
            df_comments["date"] = pd.to_datetime(df_comments["created_utc"], unit="s").dt.date
        
        # Group by date
        posts_per_day = df_posts.groupby("date").size() if not df_posts.empty else pd.Series(dtype=int)
        comments_per_day = df_comments.groupby("date").size() if not df_comments.empty else pd.Series(dtype=int)
        
        # Merge unique dates
        all_dates = sorted(set(posts_per_day.index.tolist() + comments_per_day.index.tolist()))
        
        # Create the plot
        plt.figure(figsize=(10, 5))
        
        # Plot posts if available
        if not posts_per_day.empty:
            plt.bar(posts_per_day.index, posts_per_day.values, color="blue", alpha=0.6, label="Posts")
        
        # Plot comments if available
        if not comments_per_day.empty:
            plt.bar(comments_per_day.index, comments_per_day.values, color="red", alpha=0.6, label="Comments")
        
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.title(f"Posts & Comments Over Time for {username}")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        # Encode the bytes as base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        
        return image_base64
    except Exception as e:
        print(f"Error generating activity timeline: {str(e)}")
        return None
    


def generate_word_cloud(username=None, subreddit=None, custom_excluded_words=None):
    """
    Generate a word cloud from a Reddit user's comments/posts or a subreddit's comments.
    
    Parameters:
    username (str, optional): Reddit username to analyze
    subreddit (str, optional): Subreddit name to analyze
    custom_excluded_words (set, optional): Additional words to exclude
    
    Returns:
    str: Base64 encoded image of the word cloud
    """
    try:
        stopwords = get_default_stopwords(custom_excluded_words)
        
        combined_text = ""
        
        # Get text based on username or subreddit
        if username:
            user_data, error = fetch_user_data(username)
            if error or not user_data:
                return None
            
            # Extract text from comments
            comments_text = " ".join([comment.get("text", "") for comment in user_data.get('recent_comments', [])])
            
            # Extract titles from posts
            posts_text = " ".join([post.get("title", "") for post in user_data.get('recent_posts', [])])
            
            combined_text = comments_text + " " + posts_text
            
        elif subreddit:
            comments = fetch_subreddit_comments(subreddit, limit=100)
            if not comments:
                return None
                
            # Extract text from subreddit comments
            combined_text = " ".join([comment.get("body", "") for comment in comments])
        
        else:
            return None
        
        # Remove URLs from the text
        combined_text = re.sub(r'http\S+', '', combined_text)
        # Remove common Reddit formatting
        combined_text = re.sub(r'\[.*?\]\(.*?\)', '', combined_text)  # Remove markdown links
        combined_text = re.sub(r'&amp;', '&', combined_text)  # Replace HTML entities
        combined_text = re.sub(r'&lt;', '<', combined_text)
        combined_text = re.sub(r'&gt;', '>', combined_text)
        
        # Check if we have enough text
        if len(combined_text.split()) < 10:
            return None
        
        # Generate the word cloud
        wordcloud = WordCloud(
            width=800, 
            height=400,
            background_color='white',
            max_words=100,
            stopwords=stopwords,
            collocations=False  # Avoid repeating word pairs
        ).generate(combined_text)
        
        # Create the plot
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        # Save plot to a bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        # Encode the bytes as base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        
        return image_base64
    
    except Exception as e:
        print(f"Error generating word cloud: {str(e)}")
        return None

def generate_word_frequency(username=None, subreddit=None, custom_excluded_words=None, top_n=15):
    """
    Generate word frequency data for a bar chart from Reddit content
    
    Parameters:
    username (str, optional): Reddit username to analyze
    subreddit (str, optional): Subreddit name to analyze
    custom_excluded_words (set, optional): Additional words to exclude
    top_n (int): Number of top words to return
    
    Returns:
    str: Base64 encoded image of the frequency chart
    """
    try:
        #
        stopwords = get_default_stopwords(custom_excluded_words)
        
        combined_text = ""
        
        # Get text based on username or subreddit
        if username:
            user_data, error = fetch_user_data(username)
            if error or not user_data:
                return None
            
            # Extract text from comments
            comments_text = " ".join([comment.get("text", "") for comment in user_data.get('recent_comments', [])])
            
            # Extract titles from posts
            posts_text = " ".join([post.get("title", "") for post in user_data.get('recent_posts', [])])
            
            combined_text = comments_text + " " + posts_text
            
        elif subreddit:
            comments = fetch_subreddit_comments(subreddit, limit=100)
            if not comments:
                return None
                
            # Extract text from subreddit comments
            combined_text = " ".join([comment.get("body", "") for comment in comments])
        
        else:
            return None
        
        # Remove URLs from the text
        combined_text = re.sub(r'http\S+', '', combined_text)
        # Remove common Reddit formatting
        combined_text = re.sub(r'\[.*?\]\(.*?\)', '', combined_text)
        
        # Tokenize and filter words
        words = combined_text.lower().split()
        words = [word.strip('.,!?()[]{}"\'') for word in words]
        words = [word for word in words if len(word) > 2 and word not in stopwords]
        
        # Count word frequency
        word_counts = Counter(words)
        top_words = word_counts.most_common(top_n)
        
        if not top_words:
            return None
            
        # Create frequency chart
        words, counts = zip(*top_words)
        
        plt.figure(figsize=(10, 6))
        plt.barh(range(len(words)), counts, align='center')
        plt.yticks(range(len(words)), words)
        plt.xlabel('Frequency')
        plt.title('Most Common Words')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        # Encode the bytes as base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        
        return image_base64
    
    except Exception as e:
        print(f"Error generating word frequency chart: {str(e)}")
        return None
    


def fetch_post_comments(post_url):
    """Fetch comments from a specific Reddit post URL."""
    post_id = extract_post_id(post_url)  # Get post ID

    if not post_id:
        return None, "Invalid Reddit post URL format."

    reddit = get_reddit_instance()

    try:
        submission = reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)  # Load all top-level comments

        comments_data = []
        for comment in submission.comments.list():
            if isinstance(comment, praw.models.Comment):
                comments_data.append({
                    "body": comment.body,
                    "created_utc": datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                    "score": comment.score
                })

        return comments_data, None
    except Exception as e:
        return None, f"Error fetching post: {str(e)}"

def analyze_post_comments(post_url):
    """Fetch comments, compute statistics, and generate a histogram for a given post."""
    comments, error = fetch_post_comments(post_url)
    if error:
        return None, None, error

    if not comments:
        return None, None, "No comments found for this post."

    # Convert to DataFrame
    df = pd.DataFrame(comments)

    # Remove deleted/empty comments
    df = df[df["body"] != "[deleted]"]

    if df.empty:
        return None, None, "All comments are deleted."

    # Compute word and character count
    df["word_count"] = df["body"].apply(lambda x: len(x.split()))
    df["char_count"] = df["body"].apply(len)

    # Calculate quartiles directly from pandas
    word_quartiles = df["word_count"].quantile([0.25, 0.50, 0.75])
    char_quartiles = df["char_count"].quantile([0.25, 0.50, 0.75])

    # Create class to mimic the structure
    class DotDict:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
                
    # Create nested objects to allow attribute access like "0.25"
    class QuartileDict:
        def __init__(self, q25, q50, q75):
            self.__dict__["0.25"] = int(q25)
            self.__dict__["0.50"] = int(q50)
            self.__dict__["0.75"] = int(q75)

    # Compute statistics
    stats = {
        "total_comments": len(df),
        "avg_word_count": df["word_count"].mean(),
        "median_word_count": int(df["word_count"].median()),
        "quartiles_word_count": QuartileDict(
            word_quartiles[0.25], word_quartiles[0.50], word_quartiles[0.75]
        ),
        "word_count": DotDict(
            min=int(df["word_count"].min()),
            max=int(df["word_count"].max()),
            std=df["word_count"].std(),
        ),
        "avg_char_count": df["char_count"].mean(),
        "median_char_count": int(df["char_count"].median()),
        "quartiles_char_count": QuartileDict(
            char_quartiles[0.25], char_quartiles[0.50], char_quartiles[0.75]
        ),
        "char_count": DotDict(
            min=int(df["char_count"].min()),
            max=int(df["char_count"].max()),
            std=df["char_count"].std(),
        ),
    }

    # Generate histogram
    buffer = BytesIO()
    plt.figure(figsize=(10, 6))
    
    # Create a subplot with 1 row and 2 columns
    plt.subplot(1, 2, 1)
    plt.hist(df["word_count"], bins=30, color="skyblue", edgecolor="black")
    plt.title("Word Count Distribution")
    plt.xlabel("Word Count")
    plt.ylabel("Frequency")
    
    # Add second histogram for character count
    plt.subplot(1, 2, 2)
    plt.hist(df["char_count"], bins=30, color="lightgreen", edgecolor="black")
    plt.title("Character Count Distribution")
    plt.xlabel("Character Count")
    plt.ylabel("Frequency")
    
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()

    return stats, image_base64, None
#-------------------------------new 21 april--

def analyze_post_comments_postanalysis(post_url):
    """Fetch comments, compute statistics, and generate a histogram for a given post."""
    comments, error = fetch_post_comments(post_url)
    if error:
        return None, None, error

    if not comments:
        return None, None, "No comments found for this post."

    # Convert to DataFrame
    df = pd.DataFrame(comments)

    # Remove deleted/empty comments
    df = df[df["body"] != "[deleted]"]

    if df.empty:
        return None, None, "All comments are deleted."

    # Compute word and character count
    df["word_count"] = df["body"].apply(lambda x: len(x.split()))
    df["char_count"] = df["body"].apply(len)

    # Calculate quartiles directly from pandas
    word_quartiles = df["word_count"].quantile([0.25, 0.50, 0.75])
    char_quartiles = df["char_count"].quantile([0.25, 0.50, 0.75])

    # Create regular dictionaries 
    # This ensures they can be properly pickled for cache
    word_quartile_dict = {
        "0.25": int(word_quartiles[0.25]),
        "0.50": int(word_quartiles[0.50]),
        "0.75": int(word_quartiles[0.75])
    }
    
    char_quartile_dict = {
        "0.25": int(char_quartiles[0.25]),
        "0.50": int(char_quartiles[0.50]),
        "0.75": int(char_quartiles[0.75])
    }
    
    word_count_stats = {
        "min": int(df["word_count"].min()),
        "max": int(df["word_count"].max()),
        "std": float(df["word_count"].std())
    }
    
    char_count_stats = {
        "min": int(df["char_count"].min()),
        "max": int(df["char_count"].max()),
        "std": float(df["char_count"].std())
    }

    # Compute statistics using regular dictionaries
    stats = {
        "total_comments": len(df),
        "avg_word_count": float(df["word_count"].mean()),
        "median_word_count": int(df["word_count"].median()),
        "quartiles_word_count": word_quartile_dict,
        "word_count": word_count_stats,
        "avg_char_count": float(df["char_count"].mean()),
        "median_char_count": int(df["char_count"].median()),
        "quartiles_char_count": char_quartile_dict,
        "char_count": char_count_stats,
    }

    # Generate histogram
    buffer = BytesIO()
    plt.figure(figsize=(10, 6))
    
    # Create a subplot with 1 row and 2 columns
    plt.subplot(1, 2, 1)
    plt.hist(df["word_count"], bins=30, color="skyblue", edgecolor="black")
    plt.title("Word Count Distribution")
    plt.xlabel("Word Count")
    plt.ylabel("Frequency")
    
    # Add second histogram for character count
    plt.subplot(1, 2, 2)
    plt.hist(df["char_count"], bins=30, color="lightgreen", edgecolor="black")
    plt.title("Character Count Distribution")
    plt.xlabel("Character Count")
    plt.ylabel("Frequency")
    
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()

    return stats, image_base64, None


from .models import RedditComment  # Import model to fetch comments from DB

def analyze_comment_length():
    """Fetch comments from the database, compute statistics, and generate a histogram."""
    # Fetch all comments from the database
    comments = RedditComment.objects.exclude(body="[deleted]").values_list("body", flat=True)

    if not comments:
        return None, "No comments available for analysis."

    # Convert to DataFrame
    df = pd.DataFrame(comments, columns=["body"])
    
    # Compute word and character count
    df["word_count"] = df["body"].apply(lambda x: len(x.split()))
    df["char_count"] = df["body"].apply(len)

    # Compute statistics
    stats = {
        "total_comments": len(df),
        "avg_word_count": df["word_count"].mean(),
        "median_word_count": df["word_count"].median(),
        "quartiles_word_count": df["word_count"].quantile([0.25, 0.5, 0.75]).to_dict(),
        "avg_char_count": df["char_count"].mean(),
        "median_char_count": df["char_count"].median(),
        "quartiles_char_count": df["char_count"].quantile([0.25, 0.5, 0.75]).to_dict(),
    }

    # Generate histogram
    buffer = BytesIO()
    plt.figure(figsize=(10, 6))
    plt.hist(df["word_count"], bins=30, color="skyblue", edgecolor="black")
    plt.title("Distribution of Comment Lengths (Word Count)")
    plt.xlabel("Word Count")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()

    return stats, image_base64




def fetch_user_posts_comments(username):
    """Fetch posts & comments from a Reddit user."""
    reddit = get_reddit_instance()
    
    try:
        user = reddit.redditor(username)
        
        # Fetch recent posts
        posts = []
        for post in user.submissions.new(limit=100):
            posts.append({"subreddit": post.subreddit.display_name})

        # Fetch recent comments
        comments = []
        for comment in user.comments.new(limit=100):
            comments.append({"subreddit": comment.subreddit.display_name})

        return posts, comments, None

    except Exception as e:
        return None, None, str(e)

def generate_subreddit_pie_chart(username):
    """Generate a pie chart of subreddit activity (posts + comments)."""
    posts, comments, error = fetch_user_posts_comments(username)
    if error:
        return None, error

    if not posts and not comments:
        return None, "No subreddit activity found for this user."

    # Convert to DataFrame
    df_posts = pd.DataFrame(posts)
    df_comments = pd.DataFrame(comments)

    # Count number of posts & comments per subreddit
    subreddit_counts = df_posts["subreddit"].value_counts().add(df_comments["subreddit"].value_counts(), fill_value=0)

    # Filter subreddits with more than 1 post/comment
    subreddit_counts = subreddit_counts[subreddit_counts > 1]

    if subreddit_counts.empty:
        return None, "Not enough subreddit activity to display."

    # Generate Pie Chart
    buffer = BytesIO()
    plt.figure(figsize=(7, 7))
    subreddit_counts.plot(kind="pie", autopct="%1.1f%%", cmap="tab10")
    plt.title(f"Subreddit Participation for {username}")
    plt.ylabel("")  # Hide y-label
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()

    return image_base64, None


# ✅ 3️⃣ Fetch Comments from Reddit Post
def fetch_reddit_comments(post_url):
    """Fetches comments from a Reddit post using authenticated API"""
    post_id = extract_post_id(post_url)
    if not post_id:
        return None, "Invalid Reddit post URL."

    reddit = get_reddit_instance()

    try:
        submission = reddit.submission(id=post_id)
        submission.comments.replace_more(limit=None)  # Expand all comments

        comments = []

        def extract_comments(comment_list):
            for comment in comment_list:
                author = comment.author.name if comment.author else "[Deleted]"
                timestamp = datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')

                comments.append({
                    "username": author,
                    "comment": comment.body,
                    "timestamp": timestamp
                })

                if len(comment.replies) > 0:
                    extract_comments(comment.replies)  # Recursively fetch replies

        extract_comments(submission.comments.list())  # Extract all comments
        return comments, None

    except Exception as e:
        return None, f"Error fetching comments: {str(e)}"

# ✅ 4️⃣ Generate Word Cloud
def generate_word_cloud_post(comments):
    """Generates a Word Cloud from Reddit comments"""
    combined_text = " ".join(comment["comment"] for comment in comments)

    # Remove URLs
    combined_text = re.sub(r'http\S+', '', combined_text)

    # Define stopwords
    stopwords = set(STOPWORDS)
    stopwords.update(["deleted", "removed"])

    # Generate Word Cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords).generate(combined_text)

    # Convert Word Cloud to base64 image
    buffer = BytesIO()
    plt.figure(figsize=(15, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    return image_base64

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import urlparse

# ✅ 5️⃣ Perform Sentiment Analysis
def analyze_sentiment(comments):
    """Analyzes sentiment of Reddit comments and sorts them by time (newest first)."""
    analyzer = SentimentIntensityAnalyzer()
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    
    analyzed_comments = []
    for comment in comments:
        score = analyzer.polarity_scores(comment["comment"])["compound"]
        sentiment = "Positive" if score > 0.05 else "Negative" if score < -0.05 else "Neutral"
        sentiment_counts[sentiment] += 1
        analyzed_comments.append({
            "username": comment["username"],
            "timestamp": comment["timestamp"],
            "text": comment["comment"],
            "sentiment": sentiment,
            "score": round(score, 4)  # Keep score rounded for readability
        })

    # ✅ Sort comments by timestamp (newest first)
    analyzed_comments.sort(key=lambda x: x["timestamp"], reverse=True)

    total = len(comments)
    sentiment_percentages = {
        "Positive": round((sentiment_counts["Positive"] / total) * 100, 2) if total else 0,
        "Negative": round((sentiment_counts["Negative"] / total) * 100, 2) if total else 0,
        "Neutral": round((sentiment_counts["Neutral"] / total) * 100, 2) if total else 0,
    }

    return analyzed_comments, sentiment_percentages




# Fetch Comments from a Reddit Post
def fetch_reddit_comment_timestamps(post_url):
    """Fetch timestamps of all comments from a Reddit post"""
    post_id = extract_post_id(post_url)
    if not post_id:
        return None, "Invalid Reddit post URL."

    reddit = get_reddit_instance()

    try:
        submission = reddit.submission(id=post_id)
        submission.comments.replace_more(limit=None)  # Expand all comments

        timestamps = []

        def extract_comments(comment_list):
            for comment in comment_list:
                timestamp = datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                timestamps.append(timestamp)

                if len(comment.replies) > 0:
                    extract_comments(comment.replies)  # Recursively fetch replies

        extract_comments(submission.comments.list())  # Extract all comments
        return timestamps, None

    except Exception as e:
        return None, f"Error fetching comments: {str(e)}"

# Generate Interactive Plotly Chart
import json
import pandas as pd
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder  # Use this instead of px.utils

# def generate_interactive_chart(comments, time_unit='hourly'):
#     """Generate an interactive Plotly line chart for Reddit comment trends"""
#     if not comments:
#         return None

#     # Convert timestamps to pandas DataFrame
#     df = pd.DataFrame(comments, columns=['timestamp'])
#     df['timestamp'] = pd.to_datetime(df['timestamp'])

#     # Group by time unit
#     if time_unit == 'hourly':
#         df['time_group'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:00')  # Group by hour
#     elif time_unit == 'daily':
#         df['time_group'] = df['timestamp'].dt.strftime('%Y-%m-%d')  # Group by day
#     else:
#         return None  # Invalid time unit

#     # Count comments per time group
#     comment_counts = df.groupby('time_group').size().reset_index(name='count')

#     # Create an interactive Plotly line chart
#     fig = px.line(comment_counts, x='time_group', y='count',
#                   markers=True,
#                   labels={'time_group': 'Time Interval', 'count': 'Number of Comments'},
#                   title=f"Number of Comments Over Time ({time_unit.capitalize()})")

#     fig.update_layout(
#         xaxis=dict(title="Time Interval", tickangle=-45),
#         yaxis=dict(title="Number of Comments"),
#         hovermode="x unified"
#     )

#     return json.dumps(fig, cls=PlotlyJSONEncoder)  # Fixed line

def generate_interactive_chart(comments, time_unit='hourly'):
    """Generate an interactive Plotly line chart for Reddit comment trends"""
    if not comments:
        return None
        
    # Convert timestamps to pandas DataFrame
    df = pd.DataFrame(comments, columns=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Group by time unit
    if time_unit == 'hourly':
        df['time_group'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:00')  # Group by hour
    elif time_unit == 'daily':
        df['time_group'] = df['timestamp'].dt.strftime('%Y-%m-%d')  # Group by day
    else:
        return None  # Invalid time unit
    
    # Count comments per time group
    comment_counts = df.groupby('time_group').size().reset_index(name='count')
    
    # 
    comment_counts = comment_counts.sort_values('time_group')
    
    # Add cumulative column
    comment_counts['cumulative'] = comment_counts['count'].cumsum()
    
    # Create a subplot with two charts
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    
    fig = make_subplots(
        rows=2, 
        cols=1, 
        subplot_titles=[
            f"New Comments Per {time_unit.capitalize()} Interval",
            "Cumulative Comments Over Time"
        ],
        vertical_spacing=0.25  # Increased spacing between subplots
    )
    
    # Add non-cumulative chart (new comments per period)
    fig.add_trace(
        go.Bar(
            x=comment_counts['time_group'],
            y=comment_counts['count'],
            name="New Comments",
            marker_color='rgb(55, 83, 109)'
        ),
        row=1, col=1
    )
    
    # Add cumulative chart
    fig.add_trace(
        go.Scatter(
            x=comment_counts['time_group'],
            y=comment_counts['cumulative'],
            mode='lines+markers',
            name="Cumulative Comments",
            line=dict(color='rgb(26, 118, 255)', width=2)
        ),
        row=2, col=1
    )
    
    # Update layout with increased height
    fig.update_layout(
        height=800,  # Increased overall height
        showlegend=True,
        hovermode="x unified",
        title_text="Reddit Comment Activity Analysis",
        margin=dict(t=100, b=50, l=50, r=50)  # Adjusted margins
    )
    
    # Update x-axis properties
    fig.update_xaxes(
        title_text="Time",
        tickangle=-45,
        row=1, col=1
    )
    fig.update_xaxes(
        title_text="Time",
        tickangle=-45,
        row=2, col=1
    )
    
    # Update y-axis properties
    fig.update_yaxes(
        title_text="Number of New Comments",
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="Total Comments",
        row=2, col=1
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)