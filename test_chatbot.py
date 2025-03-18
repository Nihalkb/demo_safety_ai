"""
Test script for the Safety Chatbot using OpenAI integration
"""

import sys
import logging
from safety_processor import SafetyProcessor
from nlp_engine import NLPEngine

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chat_responses():
    """Test different types of chat responses using the safety processor"""
    # Initialize components
    nlp_engine = NLPEngine()
    safety_processor = SafetyProcessor()
    
    # Test messages
    test_messages = [
        "What are the emergency protocols for chemical spills?",
        "How do I handle a gas leak?",
        "What PPE is needed for corrosive materials?",
        "Were there any incidents involving diesel fuel?",
        "Tell me about risk assessment for flammable liquids"
    ]
    
    logger.info("Starting chatbot response test")
    
    # Process each test message
    for message in test_messages:
        logger.info(f"\nTesting message: '{message}'")
        
        # Extract intent
        intent = nlp_engine.extract_intent(message)
        logger.info(f"Detected intent: {intent}")
        
        # Generate response
        response = safety_processor.generate_chat_response(message, intent)
        logger.info(f"RESPONSE: {response}")
        logger.info("-" * 80)

if __name__ == "__main__":
    test_chat_responses()