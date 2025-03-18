import json
import os
import logging
import time
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self):
        """Initialize the LLM handler with OpenAI"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = None
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)
        self.model = "gpt-4o"  # Using the latest model
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not found in environment variables")
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [k for k, v in self.cache.items() if current_time - v["timestamp"] > self.cache_ttl]
        for key in expired_keys:
            del self.cache[key]
    
    def generate_response(self, prompt, safety_context=None, max_length=250):
        """Generate a response using OpenAI based on a prompt and safety context"""
        if not self.client:
            return self.generate_response_with_fallback(prompt, safety_context)
        
        # Clean cache periodically
        self._clean_cache()
        
        # Create a cache key based on prompt and context
        cache_key = f"{prompt}_{str(safety_context)}"
        if cache_key in self.cache:
            logger.info("Returning cached response")
            return self.cache[cache_key]["response"]
        
        try:
            # Prepare the messages for the API call
            messages = [{"role": "system", "content": "You are a safety information assistant. Provide helpful, accurate, and concise information about safety protocols, incidents, and hazard management."}]
            
            # Add safety context if provided
            if safety_context:
                context_message = "Here is some relevant safety information:\n\n"
                if isinstance(safety_context, list):
                    for item in safety_context:
                        if isinstance(item, dict):
                            context_message += json.dumps(item, indent=2) + "\n\n"
                        else:
                            context_message += str(item) + "\n\n"
                else:
                    context_message += str(safety_context)
                
                messages.append({"role": "system", "content": context_message})
            
            # Add the user's prompt
            messages.append({"role": "user", "content": prompt})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_length,
                temperature=0.5,  # Lower temperature for more focused responses
            )
            
            generated_text = response.choices[0].message.content
            
            # Cache the response
            self.cache[cache_key] = {
                "response": generated_text,
                "timestamp": time.time()
            }
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            return self.generate_response_with_fallback(prompt, safety_context)
    
    def generate_response_with_fallback(self, prompt, safety_documents=None):
        """Generate a response with fallbacks if OpenAI is unavailable"""
        logger.warning("Using fallback response generation")
        
        # Basic template-based responses for common safety queries
        if "chemical spill" in prompt.lower():
            return ("For chemical spills: 1) Evacuate the area, 2) Alert safety personnel, "
                   "3) Identify the chemical if possible, 4) Contain the spill using appropriate "
                   "materials, 5) Clean up according to safety protocols for the specific chemical.")
        
        elif "fire" in prompt.lower() or "evacuation" in prompt.lower():
            return ("In case of fire: 1) Activate the nearest fire alarm, 2) Call emergency services, "
                   "3) Evacuate using designated routes, 4) Assemble at the designated meeting point, "
                   "5) Do not use elevators, 6) If trained and if safe to do so, use fire extinguishers "
                   "for small fires.")
        
        elif "protective equipment" in prompt.lower() or "ppe" in prompt.lower():
            return ("Personal Protective Equipment (PPE) requirements depend on the hazard. "
                   "General guidelines include: 1) Eye protection for chemical or particulate hazards, "
                   "2) Gloves appropriate to the material being handled, 3) Respiratory protection "
                   "for airborne hazards, 4) Protective clothing for chemical, thermal, or radiation hazards.")
        
        # If safety documents are provided, attempt to extract relevant information
        if safety_documents:
            # Simple approach: look for keyword matches in the documents
            keywords = prompt.lower().split()
            relevant_info = []
            
            for doc in safety_documents:
                if isinstance(doc, dict):
                    # For dictionaries, check values for matches
                    for key, value in doc.items():
                        if isinstance(value, str):
                            for keyword in keywords:
                                if keyword in value.lower():
                                    relevant_info.append(f"{key}: {value}")
                elif isinstance(doc, str):
                    # For strings, check for keyword matches
                    for keyword in keywords:
                        if keyword in doc.lower():
                            relevant_info.append(doc)
            
            if relevant_info:
                return "Based on available information:\n\n" + "\n\n".join(relevant_info)
        
        # Default response if no specific template or document matches
        return ("I'm your safety assistant. I can help with safety protocols, incident information, "
               "and risk assessments. Please provide specific details about your safety query for "
               "more tailored information.")

    def analyze_sentiment(self, text):
        """Analyze the sentiment of the given text"""
        if not self.client:
            return {"rating": 3, "confidence": 0.5}  # Default neutral rating
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. "
                        + "Analyze the sentiment of the text and provide a rating "
                        + "from 1 to 5 stars and a confidence score between 0 and 1. "
                        + "Respond with JSON in this format: "
                        + "{'rating': number, 'confidence': number}",
                    },
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "rating": max(1, min(5, round(result["rating"]))),
                "confidence": max(0, min(1, result["confidence"])),
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"rating": 3, "confidence": 0.5}  # Default neutral rating