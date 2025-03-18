import logging
import json
import os
import re
from collections import Counter

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        """Initialize the store for similarity search using keyword-based approach"""
        self.logger = logging.getLogger(__name__)
        self.incident_reports = self._load_incident_reports()
        
        # Pre-process incident reports for faster keyword matching
        self.processed_incidents = []
        for incident in self.incident_reports:
            # Combine title and description
            text = f"{incident.get('title', '')} {incident.get('description', '')}"
            # Create a set of words for faster lookup
            words = set(self._tokenize_text(text))
            
            self.processed_incidents.append({
                'incident': incident,
                'words': words
            })
        
        self.logger.info(f"VectorStore initialized with {len(self.incident_reports)} incidents")
    
    def _tokenize_text(self, text):
        """Split text into tokens, removing punctuation and converting to lowercase"""
        # Convert to lowercase and split by non-alphanumeric characters
        return [word.lower() for word in re.findall(r'\b\w+\b', text.lower())]
    
    def _load_incident_reports(self):
        """Load incident reports from the data file"""
        try:
            with open('static/data/incident_reports.json', 'r') as f:
                data = json.load(f)
                return data.get('incidents', [])
        except FileNotFoundError:
            self.logger.warning("Incident reports file not found")
            return []
    
    def find_similar_incidents(self, description, top_k=5):
        """Find incidents similar to the given description using keyword matching"""
        self.logger.info(f"Finding similar incidents for: {description}")
        
        if not self.incident_reports:
            return []
        
        # Tokenize the query
        query_tokens = self._tokenize_text(description)
        query_token_set = set(query_tokens)
        
        # Calculate TF-IDF-like weights for each token
        token_counts = Counter(query_tokens)
        
        # Calculate a simple similarity score for each incident
        scored_incidents = []
        for processed in self.processed_incidents:
            incident = processed['incident']
            incident_words = processed['words']
            
            # Calculate intersection of words
            common_words = query_token_set.intersection(incident_words)
            
            if common_words:
                # Basic scoring: sum of (word occurrences in query) for each common word
                score = sum(token_counts[word] for word in common_words)
                # Normalize by query length
                similarity_score = score / len(query_tokens)
                
                incident_copy = incident.copy()
                incident_copy['similarity_score'] = similarity_score
                incident_copy['matching_terms'] = list(common_words)
                scored_incidents.append(incident_copy)
        
        # Sort by score and return top_k
        scored_incidents.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_incidents[:top_k]
