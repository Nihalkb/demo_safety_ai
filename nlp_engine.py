import re
import logging
import nltk

# Initialize NLTK components - download essential resources
try:
    # Initialize required NLTK components
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    
    # Set up components
    NLTK_AVAILABLE = True
except Exception as e:
    NLTK_AVAILABLE = False
    logging.error(f"Error initializing NLTK: {e}")
    # Fallback implementations if NLTK unavailable
    def word_tokenize(text):
        return re.findall(r'\b\w+\b', text.lower())
    
    STOPWORDS = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
                'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during',
                'to', 'from', 'in', 'on', 'by', 'with', 'at'}
    
    # Simple lemmatizer class as fallback
    class SimpleWordNetLemmatizer:
        def lemmatize(self, word, pos=None):
            # Very basic lemmatization: handle plurals and -ing, -ed endings
            if word.endswith('s') and len(word) > 3:
                return word[:-1]
            if word.endswith('ing') and len(word) > 5:
                return word[:-3]
            if word.endswith('ed') and len(word) > 4:
                return word[:-2]
            return word

logger = logging.getLogger(__name__)

class NLPEngine:
    def __init__(self):
        """Initialize the NLP engine with necessary components"""
        self.logger = logging.getLogger(__name__)
        
        # Use NLTK if available, otherwise use fallbacks
        if NLTK_AVAILABLE:
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            self.logger.info("Using NLTK for NLP processing")
        else:
            self.stop_words = STOPWORDS
            self.lemmatizer = SimpleWordNetLemmatizer()
            self.logger.info("Using fallback NLP processing (NLTK not available)")
        
        # Keywords related to safety and emergencies
        self.safety_keywords = {
            'chemical': ['chemical', 'acid', 'base', 'solvent', 'reagent', 'corrosive', 'toxic'],
            'fire': ['fire', 'flame', 'burn', 'combustion', 'ignite', 'extinguish', 'smoke'],
            'gas': ['gas', 'leak', 'vapor', 'fume', 'inhalation', 'breathe', 'oxygen'],
            'spill': ['spill', 'leak', 'release', 'contain', 'absorb', 'cleanup', 'contamination'],
            'injury': ['injury', 'wound', 'cut', 'burn', 'exposure', 'contact', 'pain'],
            'ppe': ['ppe', 'protection', 'glove', 'goggle', 'respirator', 'mask', 'shield'],
            'evacuation': ['evacuation', 'evacuate', 'emergency', 'exit', 'alarm', 'procedure', 'drill']
        }
        
        # Intent patterns for chat
        self.intent_patterns = {
            'emergency_protocol': [
                r'what (should|do) .* (do|if|when) .* emergency',
                r'how .* (handle|respond|deal with) .* (emergency|accident|incident)',
                r'protocol .* (for|in case of|during) .* (emergency|accident|incident)',
                r'safety (procedure|protocol|guideline)',
                r'emergency (procedure|protocol|guideline)',
                r'what (is|are) the protocol',
            ],
            'incident_inquiry': [
                r'(previous|past|similar) .* (incident|accident|event)',
                r'has .* (happened|occurred) .* before',
                r'incident .* (history|record|report)',
                r'similar .* (case|situation|scenario)',
                r'how .* (handled|resolved) .* (incident|accident)',
            ],
            'risk_assessment': [
                r'(how|what) .* (dangerous|hazardous|risky)',
                r'risk .* (level|assessment|evaluation)',
                r'severity .* (of|for) .* (incident|situation|hazard)',
                r'(evaluate|assess) .* risk',
                r'what .* risk',
                r'how .* severe',
            ],
            'general_inquiry': [
                r'(what|how|who|when|where) .*',
                r'information .* (about|regarding)',
                r'tell me .*',
                r'I need .*',
                r'looking for .*',
            ]
        }
        
        self.logger.info("NLP Engine initialized")
    
    def process_query(self, query):
        """Process a natural language query and extract structured information"""
        self.logger.debug(f"Processing query: {query}")
        
        # Lowercase the query
        query = query.lower()
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(query)
        filtered_tokens = [token for token in tokens if token.isalnum() and token not in self.stop_words]
        
        # Lemmatize tokens
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in filtered_tokens]
        
        # Extract keywords
        keywords = self._extract_keywords(lemmatized_tokens)
        
        # Determine query intent
        intent = self._determine_intent(query)
        
        # Identify entities
        entities = self._identify_entities(query)
        
        return {
            'original_query': query,
            'processed_tokens': lemmatized_tokens,
            'keywords': keywords,
            'intent': intent,
            'entities': entities
        }
    
    def _extract_keywords(self, tokens):
        """Extract relevant keywords from processed tokens"""
        keywords = []
        
        # Add any tokens that are part of our safety vocabulary
        all_safety_terms = [term for sublist in self.safety_keywords.values() for term in sublist]
        keywords = [token for token in tokens if token in all_safety_terms]
        
        # If we didn't find any specific safety keywords, use the most significant tokens
        if not keywords and tokens:
            # Use at most 3 tokens, prioritizing longer words which tend to be more content-bearing
            sorted_tokens = sorted(tokens, key=len, reverse=True)
            keywords = sorted_tokens[:min(3, len(sorted_tokens))]
        
        return keywords
    
    def _determine_intent(self, query):
        """Determine the intent of the query"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        
        # Default to general inquiry if no specific intent is determined
        return 'general_inquiry'
    
    def _identify_entities(self, query):
        """Identify named entities in the query"""
        entities = {}
        
        # Simple rule-based entity extraction
        # In a production system, this would use a proper NER model
        
        # Look for chemical names
        chemical_pattern = r'(?i)(acid|base|solvent|chemical|substance|material|compound|gas|liquid)\s+([a-z]+)'
        chemical_matches = re.findall(chemical_pattern, query)
        if chemical_matches:
            entities['chemical'] = [match[1] for match in chemical_matches]
        
        # Look for locations
        location_pattern = r'(?i)(?:at|in|near)\s+(?:the\s+)?([a-z\s]+(?:building|room|area|facility|site|location|place))'
        location_matches = re.findall(location_pattern, query)
        if location_matches:
            entities['location'] = location_matches
        
        # Look for emergency types
        emergency_pattern = r'(?i)(fire|explosion|leak|spill|release|injury|accident|incident|emergency)'
        emergency_matches = re.findall(emergency_pattern, query)
        if emergency_matches:
            entities['emergency_type'] = emergency_matches
        
        return entities
    
    def extract_intent(self, message):
        """Extract the intent from a chat message"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return intent
        
        # Default to general inquiry if no specific intent is determined
        return 'general_inquiry'
