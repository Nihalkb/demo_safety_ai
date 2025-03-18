import logging
from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for, session
from app import app, db
from models import SafetyProtocol, Incident, SearchQuery, ChatSession, ChatMessage
from search_engine import search_documents, get_document_by_id, get_similar_incidents
from chatbot import process_chat_message
from risk_analysis import categorize_risk, predict_risk
from data.sample_protocols import load_sample_protocols
from data.sample_incidents import load_sample_incidents

# Initialize sample data if database is empty
@app.before_first_request
def initialize_data():
    if SafetyProtocol.query.count() == 0:
        load_sample_protocols()
        logging.info("Sample safety protocols loaded")
    
    if Incident.query.count() == 0:
        load_sample_incidents()
        logging.info("Sample incidents loaded")

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Search endpoint
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=[], query='')
    
    # Log the search query
    search_record = SearchQuery(query_text=query)
    db.session.add(search_record)
    db.session.commit()
    
    # Process search
    results = search_documents(query)
    return render_template('search.html', results=results, query=query)

# Document view endpoint
@app.route('/document/<doc_type>/<int:doc_id>')
def document_view(doc_type, doc_id):
    document = get_document_by_id(doc_type, doc_id)
    if not document:
        return render_template('document_view.html', error="Document not found"), 404
    
    return render_template('document_view.html', document=document, doc_type=doc_type)

# Incident comparison endpoint
@app.route('/incident/compare/<int:incident_id>')
def incident_comparison(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    similar_incidents = get_similar_incidents(incident)
    
    return render_template('incident_comparison.html', 
                           incident=incident, 
                           similar_incidents=similar_incidents)

# Risk assessment endpoint
@app.route('/risk-assessment')
def risk_assessment():
    incidents = Incident.query.all()
    categorized_incidents = categorize_risk(incidents)
    predicted_risks = predict_risk()
    
    return render_template('risk_assessment.html', 
                           categorized_incidents=categorized_incidents,
                           predicted_risks=predicted_risks)

# Chat API endpoints
@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    # Create a new chat session
    chat_session = ChatSession()
    db.session.add(chat_session)
    db.session.commit()
    
    session['chat_session_id'] = chat_session.id
    return jsonify({'session_id': chat_session.id})

@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    data = request.get_json()
    message = data.get('message', '')
    session_id = session.get('chat_session_id')
    
    if not session_id:
        # Create a new session if one doesn't exist
        chat_session = ChatSession()
        db.session.add(chat_session)
        db.session.commit()
        session_id = chat_session.id
        session['chat_session_id'] = session_id
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        is_user=True,
        message=message
    )
    db.session.add(user_message)
    
    # Process message and get response
    response_text = process_chat_message(message)
    
    # Save system response
    system_message = ChatMessage(
        session_id=session_id,
        is_user=False,
        message=response_text
    )
    db.session.add(system_message)
    db.session.commit()
    
    return jsonify({
        'response': response_text
    })

@app.route('/api/chat/history')
def chat_history():
    session_id = session.get('chat_session_id')
    if not session_id:
        return jsonify({'messages': []})
    
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    messages_list = [
        {
            'id': msg.id,
            'is_user': msg.is_user,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%H:%M:%S')
        }
        for msg in messages
    ]
    
    return jsonify({'messages': messages_list})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Internal server error"), 500
