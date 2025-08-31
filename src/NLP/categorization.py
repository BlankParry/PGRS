import spacy
from collections import Counter
import re

# Load English language model
nlp = spacy.load("en_core_web_sm")

# Define department keywords
DEPARTMENT_KEYWORDS = {
    'Sanitation': [
        'garbage', 'waste', 'trash', 'sewage', 'drainage', 'cleaning',
        'sanitation', 'hygiene', 'dump', 'litter', 'cleanliness',
        'waste management', 'sewerage', 'garbage collection'
    ],
    
    'Water': [
        'water', 'pipeline', 'leakage', 'tap', 'supply', 'drinking water',
        'water pressure', 'contamination', 'water quality', 'pipe burst',
        'water connection', 'water supply', 'water shortage'
    ],
    
    'Infrastructure': [
        'road', 'street', 'footpath', 'building', 'construction', 'repair',
        'maintenance', 'bridge', 'pavement', 'pothole', 'street light',
        'traffic signal', 'infrastructure', 'public property'
    ],
    
    'Public Safety': [
        'safety', 'security', 'crime', 'accident', 'emergency', 'police',
        'traffic', 'violation', 'harassment', 'danger', 'threat',
        'street light', 'public safety', 'law enforcement'
    ],
    
    'General': [
        'general', 'other', 'miscellaneous', 'complaint', 'issue',
        'problem', 'concern', 'query', 'request', 'assistance'
    ]
}

def preprocess_text(text):
    """
    Preprocess the complaint text by converting to lowercase,
    removing special characters and extra whitespace
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep spaces between words
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def extract_keywords(text):
    """
    Extract relevant keywords from the complaint text using spaCy
    """
    # Process the text with spaCy
    doc = nlp(text)
    
    # Extract nouns, verbs, and adjectives
    keywords = []
    for token in doc:
        if token.pos_ in ['NOUN', 'VERB', 'ADJ'] and not token.is_stop:
            keywords.append(token.text.lower())
            
    # Extract noun phrases
    for chunk in doc.noun_chunks:
        keywords.append(chunk.text.lower())
    
    return list(set(keywords))

def categorize_complaint(text):
    """
    Categorize the complaint based on keyword matching and return department
    """
    # Preprocess the complaint text
    processed_text = preprocess_text(text)
    
    # Extract keywords from the complaint
    complaint_keywords = extract_keywords(processed_text)
    
    # Initialize department scores
    department_scores = {dept: 0 for dept in DEPARTMENT_KEYWORDS}
    
    # Calculate score for each department based on keyword matches
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in processed_text:
                department_scores[dept] += 2  # Direct match
            for complaint_keyword in complaint_keywords:
                if keyword in complaint_keyword or complaint_keyword in keyword:
                    department_scores[dept] += 1  # Partial match
    
    # Get department with highest score
    max_score = max(department_scores.values())
    
    # If no clear match found, assign to General department
    if max_score == 0:
        return 'General'
    
    # Get all departments with the highest score
    top_departments = [dept for dept, score in department_scores.items() 
                      if score == max_score]
    
    # If multiple departments have same score, return the first one
    return top_departments[0]

def get_department_id(department_name):
    """
    Convert department name to ID
    """
    department_mapping = {
        'Sanitation': 1,
        'Water': 2,
        'Infrastructure': 3,
        'Public Safety': 4,
        'General': 5
    }
    return department_mapping.get(department_name, 5)  # Default to General (5)

def analyze_complaint(text):
    """
    Main function to analyze complaint and return department ID
    """
    try:
        # Categorize the complaint
        department = categorize_complaint(text)
        
        # Get department ID
        department_id = get_department_id(department)
        
        return department_id
        
    except Exception as e:
        print(f"Error in complaint analysis: {e}")
        return 5  # Default to General department in case of error 