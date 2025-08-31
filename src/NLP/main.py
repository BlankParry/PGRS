from categorization import analyze_complaint
from priority import analyze_priority
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_complaint_text(complaint_text):
    """
    Main function to analyze complaint text and return department and priority
    
    Args:
        complaint_text (str): The text of the complaint
        
    Returns:
        dict: Dictionary containing department_id and priority_score
    """
    try:
        # Log the incoming complaint
        logger.info("Analyzing new complaint")
        logger.debug(f"Complaint text: {complaint_text[:100]}...")  # Log first 100 chars
        
        # Get department ID
        department_id = analyze_complaint(complaint_text)
        logger.info(f"Department ID assigned: {department_id}")
        
        # Get priority score
        priority_score = analyze_priority(complaint_text)
        logger.info(f"Priority score assigned: {priority_score}")
        
        # Return results
        result = {
            'department_id': department_id,
            'priority_score': priority_score
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing complaint: {str(e)}")
        # Return default values in case of error
        return {
            'department_id': 5,  # Default to General department
            'priority_score': 2  # Default to Medium priority
        }

def batch_analyze_complaints(complaints):
    """
    Analyze multiple complaints in batch
    
    Args:
        complaints (list): List of complaint texts
        
    Returns:
        list: List of analysis results
    """
    try:
        logger.info(f"Starting batch analysis of {len(complaints)} complaints")
        
        results = []
        for complaint in complaints:
            result = analyze_complaint_text(complaint)
            results.append(result)
            
        logger.info("Batch analysis completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return None

def validate_complaint_text(text):
    """
    Validate complaint text before analysis
    
    Args:
        text (str): Complaint text to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not text:
        logger.warning("Empty complaint text received")
        return False
        
    if len(text) < 10:
        logger.warning("Complaint text too short")
        return False
        
    if len(text) > 5000:
        logger.warning("Complaint text exceeds maximum length")
        return False
        
    return True

def process_complaint(complaint_data):
    """
    Process complaint data and return analysis results
    
    Args:
        complaint_data (dict): Dictionary containing complaint information
        
    Returns:
        dict: Analysis results with department and priority
    """
    try:
        # Extract complaint text
        complaint_text = complaint_data.get('description', '')
        
        # Validate complaint text
        if not validate_complaint_text(complaint_text):
            raise ValueError("Invalid complaint text")
            
        # Analyze complaint
        result = analyze_complaint_text(complaint_text)
        
        # Add additional metadata
        result['status'] = 'success'
        result['message'] = 'Complaint analyzed successfully'
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing complaint: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'department_id': 5,
            'priority_score': 2
        }

if __name__ == "__main__":
    # Example usage
    test_complaint = {
        'description': 'There is a dangerous water leak in the main pipeline on Park Street. Water is flooding the area and causing traffic problems. This needs immediate attention!'
    }
    
    result = process_complaint(test_complaint)
    print(json.dumps(result, indent=2)) 