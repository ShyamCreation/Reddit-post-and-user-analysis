from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View

from .services import (
    fetch_subreddit_comments, 
    fetch_user_data, 
    generate_karma_chart, 
    generate_subreddit_activity_chart,
    generate_activity_timeline,
    generate_word_cloud,
    generate_word_frequency,
    analyze_comment_length,
    analyze_post_comments,
    generate_subreddit_pie_chart,
    analyze_post_comments_postanalysis,
)
from .models import RedditComment
from .forms import SubredditForm, UsernameForm, WordCloudForm, PostAnalysisForm

import logging

# Configure logger
logger = logging.getLogger(__name__)


class BaseView(View):
    """Base view with common methods for all views."""
    template_name = None
    form_class = None
    
    def get_context_data(self, **kwargs):
        """Get the base context data."""
        context = kwargs
        if self.form_class and 'form' not in context:
            context['form'] = self.form_class(self.request.GET or None)
        return context
    
    def render_to_response(self, context):
        """Render the template with the given context."""
        return render(self.request, self.template_name, context)


class IndexView(BaseView):
    """Home page view."""
    template_name = 'reddit_app/base.html'
    
    def get(self, request):
        return self.render_to_response({})


class CommentsView(BaseView):
    """View for displaying subreddit comments."""
    template_name = 'reddit_app/comments.html'
    form_class = SubredditForm
    
    def get(self, request):
        form = self.form_class(request.GET or None)
        comments = []
        context = self.get_context_data(form=form)
        
        if form.is_valid():
            subreddit = form.cleaned_data.get('subreddit')
            limit = form.cleaned_data.get('limit', 100)
            
            # Try to get from cache first
            cache_key = f'subreddit_comments_{subreddit}_{limit}'
            comments = cache.get(cache_key)
            
            if comments is None:
                try:
                    comments = fetch_subreddit_comments(subreddit, limit)
                    
                    # Cache for 30 minutes
                    cache.set(cache_key, comments, 60 * 30)
                    
                    # Save to database if needed
                    self._save_comments_to_db(comments)
                    
                except Exception as e:
                    logger.error(f"Error fetching comments for r/{subreddit}: {str(e)}")
                    messages.error(request, f"Error fetching comments: {str(e)}")
            
            context.update({
                'comments': comments,
                'subreddit': subreddit,
                'limit': limit
            })
        
        return self.render_to_response(context)
    
    def _save_comments_to_db(self, comments):
        """Save fetched comments to the database."""
        for comment_data in comments:
            try:
                RedditComment.objects.update_or_create(
                    comment_id=comment_data['comment_id'],
                    defaults=comment_data
                )
            except Exception as e:
                logger.error(f"Error saving comment {comment_data.get('comment_id')}: {str(e)}")


@method_decorator(cache_page(60 * 15), name='get')  # Cache for 15 minutes
class KarmaChartView(BaseView):
    """View for displaying user karma charts."""
    template_name = 'reddit_app/karma_chart.html'
    form_class = UsernameForm
    
    def get(self, request):
        form = self.form_class(request.GET or None)
        context = self.get_context_data(form=form)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            
            try:
                image_base64 = generate_karma_chart(username)
                if not image_base64:
                    context['error_message'] = f"No data available for user: {username}"
                context['image_base64'] = image_base64
                context['username'] = username
            except Exception as e:
                logger.error(f"Error generating karma chart for {username}: {str(e)}")
                context['error_message'] = f"Error generating chart: {str(e)}"
        
        return self.render_to_response(context)


class UserAnalysisView(BaseView):
    """Comprehensive view for user analysis."""
    template_name = 'reddit_app/user_analysis.html'
    form_class = UsernameForm
    
    def get(self, request):
        form = self.form_class(request.GET or None)
        context = self.get_context_data(form=form)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            context['username'] = username
            
            # Try to get from cache first
            cache_key = f'user_analysis_{username}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                context.update(cached_data)
            else:
                try:
                    user_data, error_message = fetch_user_data(username)
                    
                    if user_data:
                        # Generate all charts in parallel 
                        karma_chart = generate_karma_chart(username)
                        subreddit_chart = generate_subreddit_activity_chart(username)
                        activity_timeline = generate_activity_timeline(username)
                        
                        result_data = {
                            'user_data': user_data,
                            'karma_chart': karma_chart,
                            'subreddit_chart': subreddit_chart,
                            'activity_timeline': activity_timeline,
                        }
                        
                        # Cache for 1 hour
                        cache.set(cache_key, result_data, 60 * 60)
                        context.update(result_data)
                    else:
                        context['error_message'] = error_message
                
                except Exception as e:
                    logger.error(f"Error in user analysis for {username}: {str(e)}")
                    context['error_message'] = f"Error analyzing user data: {str(e)}"
        
        return self.render_to_response(context)


class WordCloudView(BaseView):
    """View for generating and displaying word clouds."""
    template_name = 'reddit_app/word_cloud.html'
    form_class = WordCloudForm
    
    def get(self, request):
        form = self.form_class(request.GET or None)
        context = self.get_context_data(form=form)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            subreddit = form.cleaned_data.get('subreddit')
            excluded_words = form.cleaned_data.get('excluded_words')
            
            if not username and not subreddit:
                context['error_message'] = "Please provide either a username or subreddit name."
                return self.render_to_response(context)
            
            # Parse excluded words
            custom_excluded_words = self._parse_excluded_words(excluded_words)
            
            # Generate caching key
            cache_key = self._generate_cache_key(username, subreddit, excluded_words)
            cached_data = cache.get(cache_key)
            
            if cached_data:
                context.update(cached_data)
            else:
                try:
                    if username:
                        word_cloud = generate_word_cloud(username=username, custom_excluded_words=custom_excluded_words)
                        word_frequency = generate_word_frequency(username=username, custom_excluded_words=custom_excluded_words)
                        if not word_cloud:
                            context['error_message'] = f"Not enough text content available for user: {username}."
                    else:  # subreddit
                        word_cloud = generate_word_cloud(subreddit=subreddit, custom_excluded_words=custom_excluded_words)
                        word_frequency = generate_word_frequency(subreddit=subreddit, custom_excluded_words=custom_excluded_words)
                        if not word_cloud:
                            context['error_message'] = f"Not enough text content available for subreddit: r/{subreddit}."
                    
                    result_data = {
                        'word_cloud': word_cloud,
                        'word_frequency': word_frequency,
                        'username': username,
                        'subreddit': subreddit,
                        'excluded_words': excluded_words,
                    }
                    
                    # Cache for 2 hours
                    cache.set(cache_key, result_data, 60 * 120)
                    context.update(result_data)
                
                except Exception as e:
                    logger.error(f"Error generating word cloud: {str(e)}")
                    context['error_message'] = f"Error generating word cloud: {str(e)}"
        
        return self.render_to_response(context)
    
    def _parse_excluded_words(self, excluded_words):
        """Parse the excluded words string into a set."""
        if not excluded_words:
            return None
        return set(word.strip() for word in excluded_words.split(','))
    
    def _generate_cache_key(self, username, subreddit, excluded_words):
        """Generate a unique cache key based on the input parameters."""
        if username:
            return f'word_cloud_user_{username}_{excluded_words}'
        return f'word_cloud_sub_{subreddit}_{excluded_words}'


@method_decorator(cache_page(60 * 60), name='get')  # Cache for 1 hour
class CommentLengthView(View):
    """View for analyzing comment lengths dynamically from user input."""
    template_name = 'reddit_app/comment_length.html'

    def get(self, request):
        form = PostAnalysisForm(request.GET or None)  # Use form to take post URL from user
        context = {"form": form}

        if form.is_valid():
            post_url = form.cleaned_data.get("post_url")
            context["post_url"] = post_url  # Pass URL to template for reference

            # Fetch and analyze post comments
            stats, image_base64, error_message = analyze_post_comments(post_url)

            if error_message:
                context["error_message"] = error_message
            else:
                context.update({
                    "stats": stats,
                    "image_base64": image_base64,
                })

        return render(request, self.template_name, context)


class PostAnalysisView(BaseView):
    """View for analyzing a specific Reddit post."""
    template_name = 'reddit_app/post_analysis.html'
    form_class = PostAnalysisForm

    def get(self, request):
        form = self.form_class(request.GET or None)
        context = self.get_context_data(form=form)

        if form.is_valid():
            post_url = form.cleaned_data.get('post_url')
            context['post_url'] = post_url

            # Try to get from cache first
            cache_key = f'post_analysis_{post_url}'
            cached_data = cache.get(cache_key)

            if cached_data:
                context.update(cached_data)
            else:
                try:
                    stats, image_base64, error_message = analyze_post_comments_postanalysis(post_url)

                    if error_message:
                        context['error_message'] = error_message
                    else:
                        result_data = {
                            'stats': stats,
                            'image_base64': image_base64,
                        }

                        # Cache for 3 hours
                        cache.set(cache_key, result_data, 60 * 180)
                        context.update(result_data)

                except Exception as e:
                    logger.error(f"Error analyzing post {post_url}: {str(e)}")
                    context['error_message'] = f"Error analyzing post: {str(e)}"

        return self.render_to_response(context)



class SubredditActivityView(BaseView):
    """View for displaying subreddit participation pie chart."""
    template_name = 'reddit_app/subreddit_activity.html'
    form_class = UsernameForm
    
    def get(self, request):
        form = self.form_class(request.GET or None)
        context = self.get_context_data(form=form)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            context['username'] = username
            
            # Try to get from cache first
            cache_key = f'subreddit_pie_{username}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                context.update(cached_data)
            else:
                try:
                    image_base64, error_message = generate_subreddit_pie_chart(username)
                    
                    result_data = {
                        'image_base64': image_base64,
                        'error_message': error_message
                    }
                    
                    if image_base64:  # Only cache successful results
                        # Cache for 2 hours
                        cache.set(cache_key, result_data, 60 * 120)
                    
                    context.update(result_data)
                
                except Exception as e:
                    logger.error(f"Error generating subreddit pie chart for {username}: {str(e)}")
                    context['error_message'] = f"Error generating chart: {str(e)}"
        
        return self.render_to_response(context)

from django.shortcuts import render
from django.views import View
from .forms import PostWordCloudSentimentForm
from .services import fetch_reddit_comments, generate_word_cloud_post, analyze_sentiment

class WordCloudSentimentView(View):
    """View to handle Word Cloud & Sentiment Analysis for a Reddit Post"""
    template_name = 'reddit_app/post_wordcloud_sentiment.html'

    def deduplicate_comments(self, comments):
        """Remove duplicate comments based on unique identifier (username + timestamp + text)"""
        unique_comments = []
        seen = set()
        
        for comment in comments:
            # Create a unique identifier for each comment
            identifier = (comment['username'], comment['timestamp'], comment['text'])
            
            if identifier not in seen:
                seen.add(identifier)
                unique_comments.append(comment)
                
        return unique_comments

    def get(self, request):
        form = PostWordCloudSentimentForm(request.GET or None)
        context = {"form": form}

        if form.is_valid():
            post_url = form.cleaned_data.get("post_url")
            comments, error = fetch_reddit_comments(post_url)

            if error:
                context["error_message"] = error
            else:
                wordcloud_img = generate_word_cloud_post(comments)
                analyzed_comments, sentiment_summary = analyze_sentiment(comments)
                
                # Deduplicate comments before sending to template
                analyzed_comments = self.deduplicate_comments(analyzed_comments)

                context.update({
                    "post_url": post_url,
                    "wordcloud_img": wordcloud_img,
                    "sentiment_summary": sentiment_summary,
                    "analyzed_comments": analyzed_comments,
                })

        return render(request, self.template_name, context)


from django.shortcuts import render
from django.views import View
import json
from .forms import PostWordCloudSentimentForm
from .services import fetch_reddit_comment_timestamps, generate_interactive_chart

class InteractiveCommentTrendsView(View):
    """View for displaying interactive comment trends over time"""
    template_name = 'reddit_app/interactive_comment_trends.html'

    def get(self, request):
        form = PostWordCloudSentimentForm(request.GET or None)
        context = {"form": form}

        if form.is_valid():
            post_url = form.cleaned_data.get("post_url")
            comments, error = fetch_reddit_comment_timestamps(post_url)

            if error:
                context["error_message"] = error
            else:
                interactive_chart = generate_interactive_chart(comments, time_unit='hourly')

                context.update({
                    "post_url": post_url,
                    "interactive_chart": interactive_chart
                })

        return render(request, self.template_name, context)
