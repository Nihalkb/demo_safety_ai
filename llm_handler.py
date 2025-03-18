import logging
import time
import os
import json
from huggingface_hub import InferenceClient
from threading import Lock

logger = logging.getLogger(__name__)

# API token (optional)
HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN")

# Use a lock to prevent multiple simultaneous requests
api_lock = Lock()

# Initialize cache for responses to reduce API calls
response_cache = {}
CACHE_SIZE_LIMIT = 100
CACHE_EXPIRE_SECONDS = 3600  # 1 hour

class LLMHandler:
    def __init__(self):
        """Initialize the LLM handler with a Hugging Face model"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing LLM Handler")
        
        # Set up the Hugging Face client - use a smaller open source model
        try:
            # If token is available, use it
            if HUGGINGFACE_API_TOKEN:
                self.client = InferenceClient(token=HUGGINGFACE_API_TOKEN)
                self.logger.info("Using authenticated Hugging Face client")
            else:
                self.client = InferenceClient()
                self.logger.info("Using anonymous Hugging Face client")
            
            # Default to a lightweight model that's good for chat and instruction following
            self.model = "google/flan-t5-small"  # Smaller model that should work with limited resources
            self.logger.info(f"Using model: {self.model}")
            
            self.initialized = True
        except Exception as e:
            self.logger.error(f"Error initializing LLM Handler: {e}")
            self.initialized = False
    
    def _clean_cache(self):
        """Remove expired or excess cache entries"""
        current_time = time.time()
        # Remove expired entries
        expired_keys = [k for k, v in response_cache.items() 
                       if current_time - v['timestamp'] > CACHE_EXPIRE_SECONDS]
        for k in expired_keys:
            del response_cache[k]
        
        # If still too many entries, remove oldest
        if len(response_cache) > CACHE_SIZE_LIMIT:
            sorted_keys = sorted(response_cache.keys(), 
                               key=lambda k: response_cache[k]['timestamp'])
            for k in sorted_keys[:len(response_cache) - CACHE_SIZE_LIMIT]:
                del response_cache[k]
    
    def generate_response(self, prompt, safety_context=None, max_length=150):
        """Generate a response using the LLM based on a prompt and safety context"""
        if not self.initialized:
            return "I'm currently experiencing technical difficulties. Please try again later."
        
        # Create a cache key from the prompt and context
        cache_key = f"{prompt}_{str(safety_context)}"
        
        # Check cache first
        if cache_key in response_cache:
            self.logger.info("Using cached response")
            return response_cache[cache_key]['response']
        
        # Build full context with safety information
        if safety_context:
            full_prompt = f"""
You are a helpful safety assistant. Use the following safety information to answer the question.
Safety Context: {safety_context}

User Question: {prompt}

Response:
"""
        else:
            full_prompt = f"""
You are a helpful safety assistant specializing in workplace and chemical safety.
Answer the following question concisely using your knowledge of safety protocols.

User Question: {prompt}

Response:
"""
        
        try:
            with api_lock:  # Ensure only one API call at a time
                self.logger.info(f"Sending prompt to model: {self.model}")
                
                # Call the Hugging Face API
                response = self.client.text_generation(
                    full_prompt,
                    model=self.model,
                    max_new_tokens=max_length,
                    temperature=0.7,
                    repetition_penalty=1.2,
                    do_sample=True
                )
                
                # Cache the response
                response_cache[cache_key] = {
                    'response': response,
                    'timestamp': time.time()
                }
                
                # Clean cache occasionally
                if len(response_cache) % 10 == 0:
                    self._clean_cache()
                
                return response
                
        except Exception as e:
            self.logger.error(f"Error generating LLM response: {e}")
            # Provide a fallback response
            return ("I'm sorry, I couldn't generate a response at this time. "
                   "Please try again with a different question.")

    def generate_response_with_fallback(self, prompt, safety_documents=None):
        """Generate a response with fallbacks if LLM is unavailable"""
        if not self.initialized:
            self.logger.warning("LLM not initialized, using fallback response")
            # If we have safety documents, use those for a fallback response
            if safety_documents and len(safety_documents) > 0:
                # Create a simple text response based on the most relevant document
                doc = safety_documents[0]
                return f"Based on our safety information: {doc.get('content', '')[:200]}..."
            else:
                return ("I'm a safety assistant here to help with workplace safety questions. "
                       "Ask me about chemical handling, emergency procedures, or safety protocols.")
        
        # If we have safety documents, use them as context
        safety_context = None
        if safety_documents and len(safety_documents) > 0:
            safety_context = "\n".join([doc.get('content', '') for doc in safety_documents[:2]])
        
        # Generate the LLM response
        return self.generate_response(prompt, safety_context)