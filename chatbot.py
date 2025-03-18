import logging
import random
import re
import spacy
from search_engine import search_documents

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Common safety-related keywords for intent recognition
SAFETY_KEYWORDS = [
    "emergency", "protocol", "procedure", "safety", "incident", "accident", 
    "hazard", "risk", "danger", "evacuation", "fire", "spill", "injury", 
    "leak", "explosion", "toxic", "chemical", "gas", "material", "ppe",
    "equipment", "precaution", "prevention", "response", "containment"
]

# Intent patterns
INTENT_PATTERNS = {
    'protocol_search': [
        r'(protocol|procedure|guideline)s?\s+(for|about|related\s+to)\s+(.+)',
        r'how\s+(do|should)\s+I\s+(.+)',
        r'what\s+(is|are)\s+the\s+(protocol|procedure|step)s?\s+(for|to)\s+(.+)'
    ],
    'incident_query': [
        r'(incident|accident)s?\s+(related\s+to|about|involving)\s+(.+)',
        r'(previous|past|recent)\s+(incident|accident)s?\s+(with|about|involving)\s+(.+)',
        r'(examples|cases)\s+of\s+(.+)\s+(incident|accident)s?'
    ],
    'risk_assessment': [
        r'(risk|danger)\s+(of|from|associated\s+with)\s+(.+)',
        r'how\s+(dangerous|risky|severe)\s+(is|are)\s+(.+)',
        r'(severity|assessment)\s+of\s+(.+)\s+(risk|hazard|incident)'
    ],
    'emergency_response': [
        r'(what|how)\s+to\s+do\s+in\s+case\s+of\s+(.+)\s+(emergency|incident|accident)',
        r'(response|react)\s+to\s+(.+)\s+(emergency|incident|spill|leak)',
        r'emergency\s+(procedure|protocol|response)\s+for\s+(.+)'
    ],
    'greeting': [
        r'^(hi|hello|hey|greetings)[\s\.,!]*$',
        r'^good\s+(morning|afternoon|evening)[\s\.,!]*$'
    ],
    'goodbye': [
        r'^(bye|goodbye|see\s+you|farewell)[\s\.,!]*$',
        r'^(end|quit|exit)[\s\.,!]*$'
    ],
    'thanks': [
        r'^(thanks|thank\s+you|appreciate\s+it)[\s\.,!]*$'
    ],
    'help': [
        r'^(help|assist|support)[\s\.,!]*$',
        r'what\s+can\s+you\s+(do|help\s+with)[\s\?,]*$',
        r'how\s+(do|can)\s+I\s+use\s+this[\s\?,]*$'
    ]
}

# Response templates
RESPONSE_TEMPLATES = {
    'greeting': [
        "Hello! I'm your Safety Information Assistant. How can I help you today?",
        "Hi there! I can help you with safety protocols, incident information, and risk assessments. What do you need?",
        "Greetings! I'm here to assist with safety information. What would you like to know?"
    ],
    'goodbye': [
        "Goodbye! Feel free to return if you have more safety questions.",
        "Stay safe! Come back anytime you need assistance.",
        "Farewell. Remember to always prioritize safety in your operations."
    ],
    'thanks': [
        "You're welcome! Safety is our priority.",
        "Happy to help! Is there anything else you need?",
        "Anytime! Let me know if you have other questions about safety protocols."
    ],
    'help': [
        "I can help you with: \n- Finding safety protocols\n- Information about past incidents\n- Risk assessments\n- Emergency response procedures\nJust ask me a question about any of these topics!",
        "You can ask me questions about safety protocols, past incidents, risk assessments, or emergency procedures. Try asking something like 'What's the protocol for chemical spills?' or 'Show me incidents related to gas leaks.'",
        "This system helps you find safety information quickly. Ask about specific protocols, incidents, or risks, and I'll retrieve the relevant information for you."
    ],
    'fallback': [
        "I'm not sure I understand. Could you rephrase your question about safety?",
        "I didn't quite catch that. Try asking about safety protocols, incidents, or risk assessments.",
        "I'm having trouble understanding your question. Could you be more specific about the safety information you need?"
    ]
}

def identify_intent(message):
    """Identify the user's intent from their message"""
    message = message.lower().strip()
    
    # Check against regex patterns
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message):
                return intent
    
    # Check for safety keywords if no pattern match
    doc = nlp(message)
    for token in doc:
        if token.text.lower() in SAFETY_KEYWORDS:
            # Default to protocol search if safety keyword found
            return 'protocol_search'
    
    # Fallback
    return 'unknown'

def extract_entities(message):
    """Extract relevant entities from the message"""
    doc = nlp(message)
    entities = {}
    
    # Extract nouns and noun phrases as potential safety topics
    entities['topics'] = []
    for chunk in doc.noun_chunks:
        entities['topics'].append(chunk.text)
    
    # If no noun chunks, try getting nouns
    if not entities['topics']:
        entities['topics'] = [token.text for token in doc if token.pos_ == 'NOUN']
    
    return entities

def generate_response_from_search(query, intent):
    """Generate a response based on search results"""
    search_results = search_documents(query, top_n=3)
    
    if not search_results:
        return f"I couldn't find specific information about {query}. Please try a different query or be more specific."
    
    # Format response based on search results
    response = f"Here's what I found about '{query}':\n\n"
    
    for i, result in enumerate(search_results, 1):
        response += f"{i}. {result['title']}\n"
        if result['type'] == 'protocol':
            response += f"Protocol: {result['content'][:150]}...\n"
        elif result['type'] == 'incident':
            response += f"Incident ({result['severity']}): {result['content'][:150]}...\n"
        response += f"Relevance: {result['score']:.2f}\n\n"
    
    response += "Would you like more details on any of these items?"
    return response

def process_chat_message(message):
    """Process a chat message and generate a response"""
    try:
        # Identify intent
        intent = identify_intent(message)
        
        # Handle conversation intents
        if intent in ['greeting', 'goodbye', 'thanks', 'help']:
            return random.choice(RESPONSE_TEMPLATES[intent])
        
        # Handle search-based intents
        if intent in ['protocol_search', 'incident_query', 'risk_assessment', 'emergency_response']:
            entities = extract_entities(message)
            
            if entities['topics']:
                # Use the first topic as the main search query
                main_topic = entities['topics'][0]
                return generate_response_from_search(message, intent)
            else:
                # No specific topic found
                return "Could you please specify what safety topic you're interested in?"
        
        # Handle unknown intent
        return random.choice(RESPONSE_TEMPLATES['fallback'])
    
    except Exception as e:
        logging.error(f"Error processing chat message: {e}")
        return "I'm experiencing some technical difficulties. Please try again."
