from django.db import models

class RedditComment(models.Model):
    comment_id = models.CharField(max_length=100, primary_key=True)
    body = models.TextField()
    score = models.IntegerField()
    subreddit = models.CharField(max_length=100)
    created_utc = models.FloatField()
    parent_id = models.CharField(max_length=100)
    link_id = models.CharField(max_length=100)
    permalink = models.URLField()
    edited = models.BooleanField(default=False)
    awards = models.JSONField(default=list)
    
    def __str__(self):
        return f"Comment {self.comment_id} in r/{self.subreddit}"