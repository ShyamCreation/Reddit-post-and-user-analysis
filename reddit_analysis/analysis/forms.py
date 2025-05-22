from django import forms

class UsernameForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Reddit username'})
    )

class SubredditForm(forms.Form):
    subreddit = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subreddit name'})
    )
    limit = forms.IntegerField(
        min_value=1,
        max_value=1000,
        initial=100,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class WordCloudForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Reddit username'})
    )
    subreddit = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subreddit name'})
    )
    excluded_words = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Comma separated words to exclude'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        subreddit = cleaned_data.get('subreddit')
        
        if not username and not subreddit:
            raise forms.ValidationError("Please provide either a username or subreddit name.")
            
        return cleaned_data

class PostAnalysisForm(forms.Form):
    post_url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Reddit post URL'
        })
    )

class PostWordCloudSentimentForm(forms.Form):
    """Form for inputting a Reddit post URL for Word Cloud & Sentiment Analysis."""
    post_url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "Enter Reddit post URL"})
    )