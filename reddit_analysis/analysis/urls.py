from django.urls import path
from . import views

# app_name = 'reddit_app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('comments/', views.CommentsView.as_view(), name='comments'),
    path('karma/', views.KarmaChartView.as_view(), name='karma_chart'),
    path('user-analysis/', views.UserAnalysisView.as_view(), name='user_analysis'),
    path('word-cloud/', views.WordCloudView.as_view(), name='word_cloud'),
    path('comment-length/', views.CommentLengthView.as_view(), name='comment_length'),
    path('post-analysis/', views.PostAnalysisView.as_view(), name='post_analysis'),
    path('subreddit-activity/', views.SubredditActivityView.as_view(), name='subreddit_activity'),
    path('post-wordcloud-sentiment/', views.WordCloudSentimentView.as_view(), name='post_wordcloud_sentiment'),
    path('interactive-comment-trends/', views.InteractiveCommentTrendsView.as_view(), name='interactive_comment_trends'),
]