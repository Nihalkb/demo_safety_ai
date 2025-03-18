document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const sessionId = document.getElementById('session-id').value;
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    
    // Set up event listeners
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Set up suggestion chips
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            chatInput.value = query;
            sendMessage();
        });
    });
    
    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add message to chat
    function addMessage(content, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${isUser ? 'user-message' : 'system-message'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = content;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = formatTime(new Date());
        
        messageElement.appendChild(messageContent);
        messageElement.appendChild(messageTime);
        
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }
    
    // Format time
    function formatTime(date) {
        const hours = date.getHours();
        const minutes = date.getMinutes();
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    }
    
    // Send message to server
    function sendMessage() {
        const message = chatInput.value.trim();
        
        if (!message) {
            return;
        }
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input
        chatInput.value = '';
        
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        scrollToBottom();
        
        // Send message to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Add system response to chat
            addMessage(data.response);
            
            // Generate new suggestions based on the conversation context
            // This would be more sophisticated in a real application
            generateContextualSuggestions(message, data.response);
        })
        .catch(error => {
            console.error('Error during chat:', error);
            loadingIndicator.style.display = 'none';
            
            // Add error message to chat
            addMessage('Sorry, there was an error processing your request. Please try again.');
        });
    }
    
    // Generate contextual suggestions based on conversation
    function generateContextualSuggestions(userMessage, systemResponse) {
        // This is a simplified implementation
        // In a real application, this would analyze the conversation and generate relevant suggestions
        
        // Check if user asked about chemical spills
        if (userMessage.toLowerCase().includes('chemical') || 
            userMessage.toLowerCase().includes('spill') ||
            systemResponse.toLowerCase().includes('chemical')) {
            
            updateSuggestionChips([
                { text: "How to clean up chemical spills?", query: "How do I properly clean up a chemical spill?" },
                { text: "Required PPE for chemicals", query: "What PPE is required when handling chemicals?" },
                { text: "Chemical exposure treatment", query: "How to treat chemical exposure to skin?" }
            ]);
            
        // Check if user asked about fire safety
        } else if (userMessage.toLowerCase().includes('fire') || 
                  systemResponse.toLowerCase().includes('fire') ||
                  userMessage.toLowerCase().includes('burn')) {
            
            updateSuggestionChips([
                { text: "Fire extinguisher types", query: "What type of fire extinguisher should I use?" },
                { text: "Evacuation procedures", query: "What are the evacuation procedures for a fire?" },
                { text: "Fire prevention", query: "How can we prevent fires in the workplace?" }
            ]);
            
        // Check if user asked about gas leaks
        } else if (userMessage.toLowerCase().includes('gas') || 
                  userMessage.toLowerCase().includes('leak') ||
                  systemResponse.toLowerCase().includes('gas leak')) {
            
            updateSuggestionChips([
                { text: "Gas leak detection", query: "How can I detect a gas leak?" },
                { text: "Ventilation procedures", query: "What ventilation procedures should I follow for a gas leak?" },
                { text: "Similar gas incidents", query: "Have there been similar gas leak incidents in the past?" }
            ]);
            
        // Default suggestions if no specific context is detected
        } else {
            // Keep the default suggestions
        }
    }
    
    // Update suggestion chips
    function updateSuggestionChips(suggestions) {
        // Only update if we have suggestions and chips to update
        if (!suggestions || !suggestionChips || suggestionChips.length === 0) {
            return;
        }
        
        // Update only if we have enough suggestions
        if (suggestions.length >= suggestionChips.length) {
            for (let i = 0; i < suggestionChips.length; i++) {
                suggestionChips[i].textContent = suggestions[i].text;
                suggestionChips[i].setAttribute('data-query', suggestions[i].query);
            }
        }
    }
    
    // Initial scroll to bottom
    scrollToBottom();
});
