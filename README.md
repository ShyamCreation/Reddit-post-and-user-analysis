# Reddit-post-and-user-analysis
 Reddit users can analyze their profile, subreddit activities, and publicly available posts. Analysis includes interactive graphs, detailed sentiment analysis and many insights available.
A Django web application for analyzing and visualizing Reddit data, including user activity, subreddit comments, post analytics, word clouds, and sentiment analysis.

## Features

- **User Analysis:** View Reddit user stats, karma, activity timeline, and most active subreddits.
- **Subreddit Comments:** Fetch and display recent comments from any subreddit.
- **Karma Charts:** Visualize user karma distribution.
- **Word Cloud Generator:** Create word clouds from user or subreddit content, with custom word exclusions.
- **Comment Length Analysis:** Analyze comment length statistics for Reddit posts.
- **Post Analysis:** Detailed statistics and histograms for comments on a specific post.
- **Word Cloud & Sentiment Analysis:** Generate word clouds and sentiment breakdowns for Reddit post comments.
- **Interactive Comment Trends:** Explore comment activity over time with interactive charts.

## Project Structure

```
reddit_analysis/
    manage.py
    analysis/
        models.py
        views.py
        forms.py
        services.py
        templates/
            reddit_app/
                base.html
                user_analysis.html
                comments.html
                karma_chart.html
                word_cloud.html
                comment_length.html
                post_analysis.html
                post_wordcloud_sentiment.html
                interactive_comment_trends.html
                subreddit_activity.html
    reddit_project/
        settings.py
        urls.py
        wsgi.py
        asgi.py
    db.sqlite3
```

## Setup Instructions

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/reddit_analysis.git
    cd reddit_analysis
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3. **Apply migrations:**
    ```sh
    python manage.py migrate
    ```

4. **Run the development server:**
    ```sh
    python manage.py runserver
    ```

5. **Access the app:**
    Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Configuration

- Edit `reddit_project/settings.py` for database, allowed hosts, and other Django settings.
- Place your Reddit API credentials (if required) in environment variables or a `.env` file and load them in `settings.py` or `services.py`.

## Usage

- Use the navigation bar to access different analysis tools.
- Enter Reddit usernames, subreddit names, or post URLs as prompted.
- Visualizations and statistics will be generated dynamically.

## Screenshots
![Screenshot 2025-04-23 094621](https://github.com/user-attachments/assets/d1bdaa6c-cf2f-47e1-9159-a98b6f020756)
![Screenshot 2025-04-08 113831](https://github.com/user-attachments/assets/5217b7e5-2e5d-4f95-864b-aebfc4d0d139)
![Screenshot 2025-04-07 193351](https://github.com/user-attachments/assets/34897906-1dba-4fe0-82b7-3d19d7737d71)
![Screenshot 2025-04-05 101114](https://github.com/user-attachments/assets/33466582-6df3-4a4f-a012-8e1669680758)
![Screenshot 2025-04-21 162135](https://github.com/user-attachments/assets/fa64527c-3aff-4192-92fe-242166dafe47)


---


**Note:** This project is for educational and research purposes. Use responsibly and respect Reddit's API terms of service.
