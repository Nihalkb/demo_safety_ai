import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from sentence_transformers import SentenceTransformer
import faiss
from models import SafetyProtocol, Incident
from app import db

# Load language model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Download model if not available
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Load sentence transformer model for embeddings
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logging.error(f"Error loading sentence transformer model: {e}")
    model = None

# TF-IDF vectorizer as fallback
tfidf_vectorizer = TfidfVectorizer(stop_words='english')

# Global cache for document vectors
document_embeddings = {
    'protocols': None,
    'incidents': None
}

protocol_ids = []
incident_ids = []

# Initialize FAISS index
def initialize_faiss_index():
    global document_embeddings, protocol_ids, incident_ids
    
    # Get all documents
    protocols = SafetyProtocol.query.all()
    incidents = Incident.query.all()
    
    if not protocols or not incidents:
        logging.warning("No documents found in database to index")
        return
    
    protocol_texts = [f"{p.title} {p.content}" for p in protocols]
    incident_texts = [f"{i.title} {i.description} {i.resolution or ''}" for i in incidents]
    
    # Store IDs for lookup
    protocol_ids = [p.id for p in protocols]
    incident_ids = [i.id for i in incidents]
    
    try:
        # Generate embeddings
        if model:
            protocol_embeddings = model.encode(protocol_texts)
            incident_embeddings = model.encode(incident_texts)
            
            # Store embeddings for later use
            document_embeddings['protocols'] = protocol_embeddings
            document_embeddings['incidents'] = incident_embeddings
            
            logging.info(f"Indexed {len(protocols)} protocols and {len(incidents)} incidents with embeddings")
        else:
            # Fallback to TF-IDF if model not available
            all_texts = protocol_texts + incident_texts
            tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
            document_embeddings['protocols'] = tfidf_matrix[:len(protocol_texts)].toarray()
            document_embeddings['incidents'] = tfidf_matrix[len(protocol_texts):].toarray()
            
            logging.info(f"Indexed {len(protocols)} protocols and {len(incidents)} incidents with TF-IDF")
    except Exception as e:
        logging.error(f"Error initializing search index: {e}")

# Search documents
def search_documents(query, top_n=5):
    """Search for documents using semantic search"""
    if (document_embeddings['protocols'] is None or 
        document_embeddings['incidents'] is None):
        initialize_faiss_index()
    
    results = []
    
    try:
        # Process query
        if model:
            query_embedding = model.encode([query])[0]
        else:
            # Fallback to TF-IDF
            query_vector = tfidf_vectorizer.transform([query]).toarray()[0]
        
        # Search protocols
        if document_embeddings['protocols'] is not None:
            protocol_similarities = cosine_similarity(
                [query_embedding] if model else [query_vector], 
                document_embeddings['protocols']
            )[0]
            
            # Get top protocol matches
            protocol_indices = np.argsort(protocol_similarities)[::-1][:top_n]
            for idx in protocol_indices:
                if protocol_similarities[idx] > 0.3:  # Threshold for relevance
                    protocol = SafetyProtocol.query.get(protocol_ids[idx])
                    results.append({
                        'id': protocol.id,
                        'title': protocol.title,
                        'content': protocol.content[:200] + '...' if len(protocol.content) > 200 else protocol.content,
                        'type': 'protocol',
                        'score': float(protocol_similarities[idx]),
                        'date': protocol.date_added.strftime('%Y-%m-%d')
                    })
        
        # Search incidents
        if document_embeddings['incidents'] is not None:
            incident_similarities = cosine_similarity(
                [query_embedding] if model else [query_vector], 
                document_embeddings['incidents']
            )[0]
            
            # Get top incident matches
            incident_indices = np.argsort(incident_similarities)[::-1][:top_n]
            for idx in incident_indices:
                if incident_similarities[idx] > 0.3:  # Threshold for relevance
                    incident = Incident.query.get(incident_ids[idx])
                    results.append({
                        'id': incident.id,
                        'title': incident.title,
                        'content': incident.description[:200] + '...' if len(incident.description) > 200 else incident.description,
                        'type': 'incident',
                        'score': float(incident_similarities[idx]),
                        'date': incident.date_occurred.strftime('%Y-%m-%d'),
                        'severity': incident.severity
                    })
        
        # Sort results by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
    except Exception as e:
        logging.error(f"Error searching documents: {e}")
        
    return results[:top_n]

# Get document by ID
def get_document_by_id(doc_type, doc_id):
    """Retrieve a document by type and ID"""
    try:
        if doc_type == 'protocol':
            document = SafetyProtocol.query.get(doc_id)
            if document:
                return {
                    'id': document.id,
                    'title': document.title,
                    'content': document.content,
                    'category': document.category,
                    'date': document.date_added.strftime('%Y-%m-%d'),
                    'type': 'protocol'
                }
        elif doc_type == 'incident':
            document = Incident.query.get(doc_id)
            if document:
                return {
                    'id': document.id,
                    'title': document.title,
                    'description': document.description,
                    'severity': document.severity,
                    'date': document.date_occurred.strftime('%Y-%m-%d'),
                    'location': document.location,
                    'response_time': document.response_time_minutes,
                    'resolution': document.resolution,
                    'type': 'incident'
                }
    except Exception as e:
        logging.error(f"Error retrieving document: {e}")
        
    return None

# Find similar incidents
def get_similar_incidents(incident, top_n=5):
    """Find incidents similar to the given incident"""
    if document_embeddings['incidents'] is None:
        initialize_faiss_index()
    
    results = []
    
    try:
        # Get incident text
        incident_text = f"{incident.title} {incident.description} {incident.resolution or ''}"
        
        # Generate embedding for the incident
        if model:
            incident_embedding = model.encode([incident_text])[0]
        else:
            incident_vector = tfidf_vectorizer.transform([incident_text]).toarray()[0]
        
        # Calculate similarities
        similarities = cosine_similarity(
            [incident_embedding] if model else [incident_vector], 
            document_embeddings['incidents']
        )[0]
        
        # Get indices of most similar incidents
        similar_indices = np.argsort(similarities)[::-1][:top_n+1]  # +1 to account for self-similarity
        
        # Get similar incidents (excluding self)
        for idx in similar_indices:
            similar_id = incident_ids[idx]
            if similar_id != incident.id and similarities[idx] > 0.3:
                similar_incident = Incident.query.get(similar_id)
                results.append({
                    'id': similar_incident.id,
                    'title': similar_incident.title,
                    'description': similar_incident.description[:150] + '...',
                    'severity': similar_incident.severity,
                    'date': similar_incident.date_occurred.strftime('%Y-%m-%d'),
                    'response_time': similar_incident.response_time_minutes,
                    'similarity_score': float(similarities[idx])
                })
    
    except Exception as e:
        logging.error(f"Error finding similar incidents: {e}")
    
    return results
