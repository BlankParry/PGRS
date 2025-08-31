import spacy
from textblob import TextBlob
import re

# Load English language model
nlp = spacy.load("en_core_web_sm")

# Define urgency keywords and their weights
URGENCY_KEYWORDS = {
    'HIGH': {
        'immediate': 3,
        'urgent': 3,
        'emergency': 3,
        'dangerous': 3,
        'critical': 3,
        'severe': 3,
        'serious': 3,
        'hazard': 3,
        'life-threatening': 4,
        'accident': 3,
        'disaster': 4,
        'death': 4,
        'dying': 4,
        'collapse': 3,
        'explosion': 4,
        'fire': 4,
        'flood': 3,
        'toxic': 4,
        'poison': 4,
        'unsafe': 3
    },
    'MEDIUM': {
        'important': 2,
        'significant': 2,
        'moderate': 2,
        'needed': 2,
        'required': 2,
        'necessary': 2,
        'concern': 2,
        'issue': 2,
        'problem': 2,
        'repair': 2,
        'fix': 2,
        'broken': 2,
        'damaged': 2,
        'leaking': 2,
        'malfunction': 2
    },
    'LOW': {
        'minor': 1,
        'small': 1,
        'slight': 1,
        'routine': 1,
        'regular': 1,
        'normal': 1,
        'standard': 1,
        'basic': 1,
        'general': 1,
        'common': 1,
        'usual': 1,
        'typical': 1
    }
}

# Time-related keywords that might affect priority
TIME_INDICATORS = {
    'HIGH': ['immediately', 'urgent', 'asap', 'emergency', 'right now', 'right away'],
    'MEDIUM': ['soon', 'this week', 'next few days'],
    'LOW': ['whenever', 'sometime', 'eventually', 'when possible']
}

def calculate_sentiment_score(text):
    """
    Calculate sentiment score of the complaint text using TextBlob
    Returns a value between -1 (very negative) and 1 (very positive)
    """
    blob = TextBlob(text)
    return blob.sentiment.polarity

def calculate_urgency_score(text):
    """
    Calculate urgency score based on keyword matching
    """
    text = text.lower()
    score = 0
    max_weight = 0
    
    # Check for urgency keywords
    for priority, keywords in URGENCY_KEYWORDS.items():
        for keyword, weight in keywords.items():
            if keyword in text:
                score += weight
                max_weight = max(max_weight, weight)
    
    # Check for time indicators
    for priority, indicators in TIME_INDICATORS.items():
        for indicator in indicators:
            if indicator in text:
                if priority == 'HIGH':
                    score += 3
                elif priority == 'MEDIUM':
                    score += 2
                else:
                    score += 1
    
    return score, max_weight

def analyze_entities(text):
    """
    Analyze named entities in the text to identify potential critical elements
    """
    doc = nlp(text)
    critical_entities = ['PERSON', 'ORG', 'GPE', 'LOC']
    entity_count = sum(1 for ent in doc.ents if ent.label_ in critical_entities)
    return min(entity_count, 3)  # Cap the contribution of entities

def determine_priority(text):
    """
    Main function to determine complaint priority
    Returns 'HIGH', 'MEDIUM', or 'LOW'
    """
    try:
        # Calculate various scores
        sentiment_score = calculate_sentiment_score(text)
        urgency_score, max_weight = calculate_urgency_score(text)
        entity_score = analyze_entities(text)
        
        # Calculate final score
        # Negative sentiment increases priority
        sentiment_factor = (1 - sentiment_score) / 2  # Convert to 0-1 scale
        final_score = urgency_score + (entity_score * 2) + (sentiment_factor * 3)
        
        # Determine priority based on final score and presence of high-urgency keywords
        if max_weight >= 4 or final_score >= 12:
            return 'HIGH'
        elif max_weight >= 2 or final_score >= 6:
            return 'MEDIUM'
        else:
            return 'LOW'
            
    except Exception as e:
        print(f"Error in priority analysis: {e}")
        return 'MEDIUM'  # Default to medium priority in case of error

def get_priority_score(priority):
    """
    Convert priority string to numeric score for database
    """
    priority_mapping = {
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1
    }
    return priority_mapping.get(priority, 2)  # Default to medium (2)

def analyze_priority(text):
    """
    Wrapper function to analyze complaint priority and return numeric score
    """
    priority = determine_priority(text)
    return get_priority_score(priority) 