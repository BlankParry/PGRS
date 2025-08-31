import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download VADER resources
nltk.download('vader_lexicon')

def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(text)
    
    # Check for neutral sentiment with a compound score of 0.0
    if sentiment['compound'] == 0.0:
        priority = "Low"
    elif sentiment['compound'] < -0.5:
        priority = "High"
    elif -0.5 <= sentiment['compound'] <= 0.5:
        priority = "Medium"
    else:
        priority = "Low"
    
    return sentiment, priority


    

''' Example
complaint = "The road is extremely dangerous with huge potholes."
sentiment, priority = analyze_sentiment(complaint)
print("Sentiment:", sentiment)
print("Priority:", priority)'''
