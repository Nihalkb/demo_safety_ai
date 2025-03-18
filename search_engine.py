import logging
import json
import re
from collections import Counter
from models import SafetyDocument, IncidentReport
from app import db

logger = logging.getLogger(__name__)

# Global variables to store document information
safety_documents = []
incident_reports = []

def _tokenize_text(text):
    """Split text into tokens, removing punctuation and converting to lowercase"""
    if not text:
        return []
    # Convert to lowercase and split by non-alphanumeric characters
    return [word.lower() for word in re.findall(r'\b\w+\b', text.lower())]

def _load_static_data():
    """Load data from static JSON files"""
    try:
        # Load emergency guidebook
        with open('static/data/emergency_guidebook.json', 'r') as f:
            guidebook = json.load(f)
            
        # Load incident reports
        with open('static/data/incident_reports.json', 'r') as f:
            incidents = json.load(f)
            
        return guidebook, incidents
    except Exception as e:
        logger.error(f"Error loading static data: {e}")
        return None, None

# Initialize document search
def initialize_search_index():
    """Load documents from the database or static files and prepare for search"""
    global safety_documents, incident_reports
    
    try:
        # First try to load from database
        db_safety_docs = SafetyDocument.query.all()
        db_incidents = IncidentReport.query.all()
        
        if db_safety_docs and db_incidents:
            safety_documents = [{
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'document_type': doc.document_type,
                'tokens': set(_tokenize_text(f"{doc.title} {doc.content}")),
                'source': 'database'
            } for doc in db_safety_docs]
            
            incident_reports = [{
                'id': incident.id,
                'title': incident.title,
                'description': incident.description,
                'resolution': incident.resolution,
                'severity': incident.severity,
                'hazard_type': incident.hazard_type,
                'tokens': set(_tokenize_text(f"{incident.title} {incident.description} {incident.resolution or ''}")),
                'source': 'database'
            } for incident in db_incidents]
            
            logger.info(f"Loaded {len(safety_documents)} safety documents and {len(incident_reports)} incident reports from database")
        else:
            # Fallback to static files
            guidebook, incidents_data = _load_static_data()
            
            if guidebook and 'hazardous_materials' in guidebook:
                for i, material in enumerate(guidebook['hazardous_materials']):
                    doc = {
                        'id': f"static-{i+1}",
                        'title': material['name'],
                        'content': f"{material['description']} Protocols: {' '.join(material['protocols'])}",
                        'document_type': 'protocol',
                        'emergency_response': material['emergency_response'],
                        'tokens': set(_tokenize_text(f"{material['name']} {material['description']} {' '.join(material['protocols'])}")),
                        'source': 'static'
                    }
                    safety_documents.append(doc)
                
            if incidents_data and 'incidents' in incidents_data:
                for incident in incidents_data['incidents']:
                    inc = {
                        'id': incident['id'],
                        'title': incident['title'],
                        'description': incident['description'],
                        'resolution': incident.get('resolution', ''),
                        'severity': incident.get('severity', 0),
                        'hazard_type': incident.get('hazard_type', ''),
                        'tokens': set(_tokenize_text(f"{incident['title']} {incident['description']} {incident.get('resolution', '')}")),
                        'source': 'static'
                    }
                    incident_reports.append(inc)
            
            logger.info(f"Loaded {len(safety_documents)} safety documents and {len(incident_reports)} incident reports from static files")
    
    except Exception as e:
        logger.error(f"Error initializing search index: {e}")

# Search documents
def search_documents(query, top_n=5):
    """Search for documents using keyword-based search"""
    global safety_documents, incident_reports
    
    # Initialize if needed
    if not safety_documents and not incident_reports:
        initialize_search_index()
    
    results = []
    
    try:
        # Tokenize query
        query_tokens = _tokenize_text(query)
        query_token_set = set(query_tokens)
        token_counts = Counter(query_tokens)
        
        # Search safety documents
        for doc in safety_documents:
            common_words = query_token_set.intersection(doc['tokens'])
            
            if common_words:
                # Calculate score based on word frequency
                score = sum(token_counts[word] for word in common_words) / len(query_tokens)
                
                if score > 0.1:  # Minimum relevance threshold
                    results.append({
                        'id': doc['id'],
                        'title': doc['title'],
                        'content': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                        'type': doc['document_type'],
                        'score': score,
                        'matching_terms': list(common_words)
                    })
        
        # Search incident reports
        for incident in incident_reports:
            common_words = query_token_set.intersection(incident['tokens'])
            
            if common_words:
                # Calculate score based on word frequency
                score = sum(token_counts[word] for word in common_words) / len(query_tokens)
                
                if score > 0.1:  # Minimum relevance threshold
                    results.append({
                        'id': incident['id'],
                        'title': incident['title'],
                        'content': incident['description'][:200] + '...' if len(incident['description']) > 200 else incident['description'],
                        'type': 'incident',
                        'score': score,
                        'severity': incident['severity'],
                        'matching_terms': list(common_words)
                    })
        
        # Sort results by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        
    return results[:top_n]

# Get document by ID
def get_document_by_id(doc_type, doc_id):
    """Retrieve a document by type and ID"""
    global safety_documents, incident_reports
    
    # Initialize if needed
    if not safety_documents and not incident_reports:
        initialize_search_index()
    
    try:
        if doc_type == 'protocol':
            for doc in safety_documents:
                if str(doc['id']) == str(doc_id):
                    return doc
        elif doc_type == 'incident':
            for incident in incident_reports:
                if str(incident['id']) == str(doc_id):
                    return incident
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        
    return None

# Find similar incidents
def get_similar_incidents(incident_description, top_n=5):
    """Find incidents similar to the given incident description"""
    global incident_reports
    
    # Initialize if needed
    if not incident_reports:
        initialize_search_index()
    
    results = []
    
    try:
        # Tokenize the incident description
        query_tokens = _tokenize_text(incident_description)
        query_token_set = set(query_tokens)
        token_counts = Counter(query_tokens)
        
        # Find similar incidents
        for incident in incident_reports:
            common_words = query_token_set.intersection(incident['tokens'])
            
            if common_words:
                # Calculate score
                score = sum(token_counts[word] for word in common_words) / len(query_tokens)
                
                if score > 0.1:  # Minimum relevance threshold
                    result = {
                        'id': incident['id'],
                        'title': incident['title'],
                        'description': incident['description'][:150] + '...' if len(incident['description']) > 150 else incident['description'],
                        'severity': incident['severity'],
                        'hazard_type': incident.get('hazard_type', 'unknown'),
                        'resolution': incident.get('resolution', ''),
                        'similarity_score': score,
                        'matching_terms': list(common_words)
                    }
                    results.append(result)
        
        # Sort by similarity score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error finding similar incidents: {e}")
    
    return results[:top_n]
