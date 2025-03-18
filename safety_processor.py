import os
import json
import logging
from datetime import datetime
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
from llm_handler import LLMHandler

# Initialize NLTK components
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)

class SafetyProcessor:
    def __init__(self):
        """Initialize the safety information processor"""
        self.emergency_guidebook = self._load_emergency_guidebook()
        self.incident_reports = self._load_incident_reports()
        self.logger = logging.getLogger(__name__)
        self.llm_handler = LLMHandler()
        self.logger.info("SafetyProcessor initialized")
    
    def _load_emergency_guidebook(self):
        """Load PHMSA Emergency Guidebook data"""
        try:
            with open('static/data/emergency_guidebook.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create initial emergency guidebook with basic data if file doesn't exist
            guidebook_data = {
                "hazardous_materials": [
                    {
                        "id": "flammable_liquids",
                        "name": "Flammable Liquids",
                        "description": "Liquids that can burn or ignite, such as gasoline, diesel fuel, and many organic chemicals.",
                        "protocols": [
                            "Keep away from heat, hot surfaces, sparks, open flames and other ignition sources.",
                            "Ground and bond container and receiving equipment.",
                            "Use explosion-proof electrical, ventilating, and lighting equipment.",
                            "Wear protective gloves, eye protection, and face protection."
                        ],
                        "emergency_response": "Evacuate area. Eliminate all ignition sources if safe to do so. Use dry chemical, CO2, water spray or alcohol-resistant foam to extinguish fires. Do not use water jet as this can spread fire."
                    },
                    {
                        "id": "corrosive_materials",
                        "name": "Corrosive Materials",
                        "description": "Substances that can attack and chemically destroy exposed body tissues.",
                        "protocols": [
                            "Do not breathe dust, fume, gas, mist, vapors, or spray.",
                            "Wash thoroughly after handling.",
                            "Wear protective gloves, eye protection, and face protection.",
                            "Store locked up in a well-ventilated place. Keep container tightly closed."
                        ],
                        "emergency_response": "Do not get in eyes, on skin, or on clothing. Avoid breathing vapors or dust. Keep container tightly closed. In case of contact, immediately flush with water for at least 15 minutes."
                    },
                    {
                        "id": "toxic_gases",
                        "name": "Toxic Gases",
                        "description": "Gases that can cause death or serious health effects when inhaled or absorbed through the skin.",
                        "protocols": [
                            "Use only outdoors or in a well-ventilated area.",
                            "Wear respiratory protection.",
                            "Keep/Store away from clothing and other combustible materials.",
                            "Protect from sunlight. Store in a well-ventilated place."
                        ],
                        "emergency_response": "Evacuate area immediately. Call emergency services. Move victim to fresh air and keep at rest in a position comfortable for breathing. Administer oxygen if breathing is difficult."
                    }
                ]
            }
            os.makedirs('static/data', exist_ok=True)
            with open('static/data/emergency_guidebook.json', 'w') as f:
                json.dump(guidebook_data, f, indent=2)
            return guidebook_data
    
    def _load_incident_reports(self):
        """Load historical incident reports"""
        try:
            with open('static/data/incident_reports.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create initial incident reports data if file doesn't exist
            incident_data = {
                "incidents": [
                    {
                        "id": "INC-2023-001",
                        "title": "Chemical Spill at Processing Plant",
                        "description": "A container of hydrochloric acid was damaged during transport, resulting in a 20-gallon spill in the storage area.",
                        "date": "2023-03-15",
                        "location": "Building 3, Chemical Processing Plant",
                        "severity": 3,
                        "response_time_minutes": 12,
                        "hazard_type": "corrosive_materials",
                        "resolution": "Spill contained with neutralizing agent. Area cordoned off, spill team deployed with appropriate PPE. Neutralized with sodium bicarbonate solution and disposed of according to regulations."
                    },
                    {
                        "id": "INC-2023-002",
                        "title": "Natural Gas Leak",
                        "description": "A gas line was damaged during excavation work, causing a significant natural gas leak.",
                        "date": "2023-04-22",
                        "location": "North Campus Construction Site",
                        "severity": 4,
                        "response_time_minutes": 8,
                        "hazard_type": "flammable_gases",
                        "resolution": "Area evacuated within 200 meters. Gas supply shut off. Leak repaired by utility company. No ignition occurred."
                    },
                    {
                        "id": "INC-2023-003",
                        "title": "Diesel Fuel Spill",
                        "description": "During refueling of backup generator, approximately 5 gallons of diesel fuel spilled onto concrete pad.",
                        "date": "2023-02-10",
                        "location": "Building 7, Power Supply Area",
                        "severity": 2,
                        "response_time_minutes": 15,
                        "hazard_type": "flammable_liquids",
                        "resolution": "Spill contained with absorbent materials. No fuel reached soil or drainage. Contaminated materials properly disposed of."
                    }
                ],
                "industry_standards": {
                    "average_response_times": {
                        "flammable_liquids": 10,
                        "corrosive_materials": 12,
                        "toxic_gases": 7,
                        "flammable_gases": 8,
                        "oxidizers": 10
                    }
                }
            }
            os.makedirs('static/data', exist_ok=True)
            with open('static/data/incident_reports.json', 'w') as f:
                json.dump(incident_data, f, indent=2)
            return incident_data
    
    def retrieve_documents(self, query_info):
        """Retrieve relevant safety documents based on NLP-processed query"""
        self.logger.debug(f"Retrieving documents for query: {query_info}")
        
        results = []
        
        # Check emergency guidebook for relevant information
        for material in self.emergency_guidebook["hazardous_materials"]:
            if any(keyword in material["name"].lower() or keyword in material["description"].lower() 
                  for keyword in query_info["keywords"]):
                results.append({
                    "source": "Emergency Guidebook",
                    "title": material["name"],
                    "content": material["description"],
                    "protocols": material["protocols"],
                    "emergency_response": material["emergency_response"],
                    "relevance_score": 0.85  # Placeholder score, would be calculated with more advanced NLP
                })
                
        # Check incident reports for relevant information
        for incident in self.incident_reports["incidents"]:
            if any(keyword in incident["title"].lower() or keyword in incident["description"].lower() 
                  for keyword in query_info["keywords"]):
                results.append({
                    "source": "Incident Report",
                    "id": incident["id"],
                    "title": incident["title"],
                    "description": incident["description"],
                    "date": incident["date"],
                    "hazard_type": incident["hazard_type"],
                    "severity": incident["severity"],
                    "resolution": incident["resolution"],
                    "relevance_score": 0.75  # Placeholder score
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results
    
    def generate_contextual_answer(self, query, results):
        """Generate contextual answers based on retrieved documents"""
        if not results:
            return "I couldn't find any relevant safety information for your query. Please try rephrasing or provide more details."
        
        # Combine information from the most relevant results
        top_results = results[:3]  # Use top 3 most relevant results
        
        # Try using the LLM handler for generating a response
        try:
            # Prepare context from the search results
            context = []
            for result in top_results:
                context.append(result)
            
            # Create a prompt for the LLM
            prompt = f"User query: {query}\n\nPlease provide a helpful and informative response to this safety question. Include specific protocols, emergency procedures, and relevant incident information if applicable."
            
            # Generate response using the LLM
            llm_response = self.llm_handler.generate_response(prompt, context)
            
            if llm_response and len(llm_response.strip()) > 10:
                return llm_response
                
        except Exception as e:
            self.logger.error(f"Error using LLM for contextual answer: {e}")
        
        # Fallback to template-based answers if LLM fails
        self.logger.warning("Falling back to template-based contextual answers")
        
        answer_components = []
        
        for result in top_results:
            if result["source"] == "Emergency Guidebook":
                protocols = "\n- " + "\n- ".join(result["protocols"]) if "protocols" in result else ""
                component = f"According to the Emergency Guidebook on {result['title']}:\n{result['content']}\n\nRecommended protocols:{protocols}\n\nIn an emergency: {result['emergency_response']}"
                answer_components.append(component)
            
            elif result["source"] == "Incident Report":
                component = f"Based on a similar incident ({result['id']}): {result['title']}\n{result['description']}\n\nResolution: {result['resolution']}"
                answer_components.append(component)
        
        # Create a combined answer
        final_answer = "Here's what I found:\n\n" + "\n\n---\n\n".join(answer_components)
        
        return final_answer
    
    def generate_chat_response(self, message, intent):
        """Generate response for chatbot based on user message and intent"""
        self.logger.debug(f"Generating chat response for message with intent: {intent}")
        
        # First gather relevant context based on intent and message
        context_data = []
        
        if intent == "emergency_protocol":
            # Look for emergency protocols
            for material in self.emergency_guidebook["hazardous_materials"]:
                if any(keyword in material["name"].lower() or keyword in material["description"].lower() 
                      for keyword in message.lower().split()):
                    context_data.append(material)
        
        elif intent == "incident_inquiry":
            # Look for similar past incidents
            for incident in self.incident_reports["incidents"]:
                if any(keyword in incident["title"].lower() or keyword in incident["description"].lower() 
                      for keyword in message.lower().split()):
                    context_data.append(incident)
        
        elif intent == "risk_assessment":
            # Find relevant hazardous materials information
            keywords = message.lower().split()
            for material in self.emergency_guidebook["hazardous_materials"]:
                if any(keyword in material["name"].lower() or keyword in material["description"].lower() 
                      for keyword in keywords):
                    context_data.append(material)
        
        # Construct a prompt based on intent and gathered context
        prompt = f"User query: {message}\n\nIntent: {intent}\n\n"
        
        if intent == "emergency_protocol":
            prompt += "Please provide detailed emergency protocols and safety procedures for this situation. List steps clearly."
        elif intent == "incident_inquiry":
            prompt += "Describe similar incidents and their resolutions. Include key details and lessons learned."
        elif intent == "risk_assessment":
            prompt += "Assess the potential risks and hazards in this situation. Include severity, likelihood, and recommended precautions."
        else:
            prompt += "Provide helpful safety information related to this query."
        
        # Use the LLM handler to generate a response with the gathered context
        llm_response = self.llm_handler.generate_response(prompt, context_data)
        
        # If the LLM handler fails or returns an empty response, fall back to the original method
        if not llm_response or llm_response.strip() == "":
            self.logger.warning("LLM response was empty, using fallback response generation")
            # Original keyword-based response generation as fallback
            if intent == "emergency_protocol":
                for material in self.emergency_guidebook["hazardous_materials"]:
                    if any(keyword in material["name"].lower() or keyword in material["description"].lower() 
                          for keyword in message.lower().split()):
                        protocols = "\n- " + "\n- ".join(material["protocols"])
                        return f"Emergency protocols for {material['name']}:{protocols}\n\nEmergency response: {material['emergency_response']}"
                
                return "I couldn't find specific emergency protocols for that situation. Please provide more details about the hazardous material or incident type."
            
            elif intent == "incident_inquiry":
                similar_incidents = []
                
                for incident in self.incident_reports["incidents"]:
                    if any(keyword in incident["title"].lower() or keyword in incident["description"].lower() 
                          for keyword in message.lower().split()):
                        similar_incidents.append(incident)
                
                if similar_incidents:
                    incident = similar_incidents[0]  # Take the first match for simplicity
                    return f"I found a similar incident: {incident['title']} (ID: {incident['id']})\n\nDescription: {incident['description']}\n\nResolution: {incident['resolution']}"
                
                return "I couldn't find any similar past incidents in our records. This may be a new scenario."
            
            elif intent == "risk_assessment":
                keywords = message.lower().split()
                
                for material in self.emergency_guidebook["hazardous_materials"]:
                    if any(keyword in material["name"].lower() for keyword in keywords):
                        return f"Risk assessment for {material['name']}:\n\n{material['description']}\n\nThis is a significant hazard that requires proper safety protocols."
                
                return "I need more specific information about the hazardous materials or situation to provide a risk assessment."
            
            else:
                # General response
                return "I'm your safety assistant. I can help with emergency protocols, incident information, or risk assessments. Please provide more details about what you need."
        
        return llm_response
    
    def compare_response_times(self, incidents):
        """Compare response times with industry standards"""
        if not incidents:
            return {
                "comparison": "No incidents to compare",
                "industry_average": None,
                "incident_average": None
            }
        
        # Extract hazard types and response times
        hazard_types = [incident.get("hazard_type") for incident in incidents if "hazard_type" in incident]
        response_times = [incident.get("response_time_minutes") for incident in incidents if "response_time_minutes" in incident]
        
        if not hazard_types or not response_times:
            return {
                "comparison": "Insufficient data for comparison",
                "industry_average": None,
                "incident_average": None
            }
        
        # Get the most common hazard type for comparison
        hazard_counts = {}
        for hazard in hazard_types:
            if hazard in hazard_counts:
                hazard_counts[hazard] += 1
            else:
                hazard_counts[hazard] = 1
        
        most_common_hazard = max(hazard_counts.items(), key=lambda x: x[1])[0]
        
        # Get industry standard for this hazard type
        industry_avg = self.incident_reports["industry_standards"]["average_response_times"].get(most_common_hazard)
        
        if not industry_avg:
            return {
                "comparison": f"No industry standard available for {most_common_hazard}",
                "industry_average": None,
                "incident_average": sum(response_times) / len(response_times)
            }
        
        # Calculate average response time for these incidents
        incident_avg = sum(response_times) / len(response_times)
        
        # Compare with industry standard
        if incident_avg <= industry_avg:
            comparison = f"Response time is better than or equal to industry standard ({incident_avg:.1f} min vs {industry_avg} min standard)"
        else:
            comparison = f"Response time is slower than industry standard ({incident_avg:.1f} min vs {industry_avg} min standard)"
        
        return {
            "comparison": comparison,
            "industry_average": industry_avg,
            "incident_average": incident_avg
        }
    
    def summarize_multiple_documents(self, documents):
        """Summarize information from multiple documents"""
        if not documents:
            return "No documents provided for summarization."
        
        # Extract content from documents
        contents = []
        for doc in documents:
            if hasattr(doc, 'content'):
                contents.append(doc.content)
            elif isinstance(doc, dict) and 'content' in doc:
                contents.append(doc['content'])
            elif isinstance(doc, str):
                contents.append(doc)
        
        if not contents:
            return "Unable to extract content from provided documents."
        
        # Try using the LLM handler for summarization
        try:
            combined_content = "\n\n---\n\n".join(contents)
            prompt = "Please summarize the following safety documents, focusing on key safety information, protocols, and critical details:\n\n" + combined_content
            
            llm_summary = self.llm_handler.generate_response(prompt, max_length=300)
            
            if llm_summary and len(llm_summary.strip()) > 10:
                return llm_summary
        except Exception as e:
            self.logger.error(f"Error using LLM for summarization: {e}")
        
        # Fallback to basic extractive summarization
        self.logger.warning("Falling back to basic extractive summarization")
        
        # For a simple extractive summary, we'll select key sentences
        all_sentences = []
        for content in contents:
            try:
                sentences = sent_tokenize(content)
                all_sentences.extend(sentences)
            except Exception as e:
                self.logger.error(f"Error tokenizing content: {e}")
                # If tokenization fails, add the content as a single item
                all_sentences.append(content[:200] + "...")  # Truncate long content
        
        if not all_sentences:
            return "Could not process documents for summarization."
        
        # For simplicity, return first sentence of each document plus a random sampling of others
        try:
            summary_sentences = []
            for content in contents:
                sentences = sent_tokenize(content)
                if sentences:
                    summary_sentences.append(sentences[0])
            
            # Add a few more sentences if there are a lot
            if len(all_sentences) > 10:
                # Select a few random sentences from the middle of documents
                import random
                middle_sentences = all_sentences[3:-3] if len(all_sentences) > 6 else all_sentences
                additional_sentences = random.sample(middle_sentences, min(5, len(middle_sentences)))
                summary_sentences.extend(additional_sentences)
            
            # Combine into a summary
            summary = " ".join(summary_sentences)
            
            return summary
        except Exception as e:
            self.logger.error(f"Error creating extractive summary: {e}")
            # Last resort fallback
            return "Document summarization failed. Please try with different documents or check formatting."
