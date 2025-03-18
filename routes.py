from flask import render_template, request, jsonify, session, redirect, url_for
import uuid
from datetime import datetime
import logging

from app import app, db
from models import SafetyDocument, SearchQuery, IncidentReport, ChatSession, ChatMessage
from nlp_engine import NLPEngine
from safety_processor import SafetyProcessor
from vector_store import VectorStore
from risk_analyzer import RiskAnalyzer

# Initialize components
nlp_engine = NLPEngine()
safety_processor = SafetyProcessor()
vector_store = VectorStore()
risk_analyzer = RiskAnalyzer()

# Logger
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/search')
def search_page():
    """Search interface page"""
    return render_template('search.html')

@app.route('/chat')
def chat_page():
    """Interactive chatbot interface"""
    # Generate a session ID if one doesn't exist
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
        
        # Try to create a new chat session in the database
        try:
            chat_session = ChatSession(
                session_id=session['chat_session_id'],
                user_id=None  # Can be linked to a user if authentication is implemented
            )
            db.session.add(chat_session)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Could not create chat session in database: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    return render_template('chat.html', session_id=session['chat_session_id'])

@app.route('/risk-assessment')
def risk_assessment():
    """Risk assessment and visualization page"""
    return render_template('risk_assessment.html')

@app.route('/api/search', methods=['POST'])
def search():
    """API endpoint for NLP search functionality"""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Try to log the search query, but continue if it fails
        try:
            search_query = SearchQuery(query=query)
            db.session.add(search_query)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Could not save search query to database: {db_error}")
            # Try to rollback in case of transaction error
            try:
                db.session.rollback()
            except:
                pass
        
        # Process the query with NLP to understand intent
        processed_query = nlp_engine.process_query(query)
        
        # Retrieve relevant documents
        results = safety_processor.retrieve_documents(processed_query)
        
        # Prepare contextual answers
        answers = safety_processor.generate_contextual_answer(query, results)
        
        return jsonify({
            'query': query,
            'results': results,
            'answers': answers
        })
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return jsonify({'error': 'An error occurred during search'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chatbot interaction"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Process message with NLP engine first to ensure core functionality works
        intent = nlp_engine.extract_intent(message)
        
        # Generate response based on intent and message content
        response_text = safety_processor.generate_chat_response(message, intent)
        
        # Try to handle the database operations, but continue if they fail
        try:
            # Find chat session
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if chat_session:
                # Update last activity
                chat_session.last_activity = datetime.utcnow()
                
                # Store user message
                user_message = ChatMessage(
                    session_id=chat_session.id,
                    message=message,
                    is_user=True
                )
                db.session.add(user_message)
                
                # Store system response
                system_message = ChatMessage(
                    session_id=chat_session.id,
                    message=response_text,
                    is_user=False
                )
                db.session.add(system_message)
                db.session.commit()
            else:
                logger.warning(f"Chat session not found for ID: {session_id}")
        except Exception as db_error:
            logger.warning(f"Database error in chat endpoint: {db_error}")
            try:
                db.session.rollback()
            except:
                pass
        
        # Return response even if database operations failed
        return jsonify({
            'response': response_text,
            'session_id': session_id
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'An error occurred during chat processing'}), 500

@app.route('/api/similarity-search', methods=['POST'])
def similarity_search():
    """API endpoint for finding similar incidents"""
    try:
        data = request.json
        incident_description = data.get('description', '')
        
        if not incident_description:
            return jsonify({'error': 'Incident description is required'}), 400
        
        # Find similar incidents
        similar_incidents = vector_store.find_similar_incidents(incident_description)
        
        # Analyze and compare response times
        comparison = safety_processor.compare_response_times(similar_incidents)
        
        return jsonify({
            'similar_incidents': similar_incidents,
            'comparison': comparison
        })
    except Exception as e:
        logger.exception("Error in similarity search endpoint")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-assessment', methods=['POST'])
def assess_risk():
    """API endpoint for risk assessment"""
    try:
        data = request.json
        incident_details = data.get('details', '')
        
        if not incident_details:
            return jsonify({'error': 'Incident details are required'}), 400
        
        # Assess risk severity
        severity, rationale = risk_analyzer.assess_severity(incident_details)
        
        # Generate predictive insights
        insights = risk_analyzer.generate_predictive_insights(incident_details, severity)
        
        return jsonify({
            'severity': severity,
            'rationale': rationale,
            'insights': insights
        })
    except Exception as e:
        logger.exception("Error in risk assessment endpoint")
        return jsonify({'error': str(e)}), 500

@app.route('/api/document-summary', methods=['POST'])
def document_summary():
    """API endpoint for multi-document summarization"""
    try:
        data = request.json
        document_ids = data.get('document_ids', [])
        
        if not document_ids:
            return jsonify({'error': 'Document IDs are required'}), 400
        
        # Retrieve documents
        documents = [SafetyDocument.query.get(doc_id) for doc_id in document_ids if SafetyDocument.query.get(doc_id)]
        
        if not documents:
            return jsonify({'error': 'No valid documents found'}), 404
        
        # Generate summary
        summary = safety_processor.summarize_multiple_documents(documents)
        
        return jsonify({
            'summary': summary,
            'document_count': len(documents)
        })
    except Exception as e:
        logger.exception("Error in document summary endpoint")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
