document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const searchResults = document.getElementById('search-results');
    const aiAnswer = document.getElementById('ai-answer');
    const resultDocuments = document.getElementById('result-documents');
    const exampleQueries = document.querySelectorAll('.example-query');
    
    // Set up event listeners
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Example query handling
    exampleQueries.forEach(example => {
        example.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            searchInput.value = query;
            performSearch();
        });
    });
    
    function performSearch() {
        const query = searchInput.value.trim();
        
        if (!query) {
            // Show error if query is empty
            showError('Please enter a search query');
            return;
        }
        
        // Show loading spinner
        loadingSpinner.style.display = 'block';
        searchResults.style.display = 'none';
        
        // Make API request
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
            
            // Display results
            displayResults(data);
        })
        .catch(error => {
            console.error('Error during search:', error);
            loadingSpinner.style.display = 'none';
            showError('An error occurred while searching. Please try again.');
        });
    }
    
    function displayResults(data) {
        // Clear previous results
        aiAnswer.innerHTML = '';
        resultDocuments.innerHTML = '';
        
        // Format and display AI answer
        const formattedAnswer = formatAnswer(data.answers);
        aiAnswer.innerHTML = formattedAnswer;
        
        // Display source documents
        if (data.results && data.results.length > 0) {
            data.results.forEach(result => {
                const resultCard = createResultCard(result);
                resultDocuments.appendChild(resultCard);
            });
        } else {
            resultDocuments.innerHTML = '<div class="alert alert-info">No source documents found for this query.</div>';
        }
        
        // Show results section
        searchResults.style.display = 'block';
    }
    
    function formatAnswer(answer) {
        // Replace newlines with HTML line breaks
        let formattedAnswer = answer.replace(/\n/g, '<br>');
        
        // Make headings stand out
        formattedAnswer = formattedAnswer.replace(/^(.*?):(?=\n|<br>)/gm, '<strong>$1:</strong>');
        
        // Highlight important terms
        const importantTerms = [
            'Emergency', 'Protocol', 'Hazard', 'Risk', 'Critical', 'Warning',
            'Caution', 'Danger', 'Safety', 'Procedure', 'Guideline'
        ];
        
        importantTerms.forEach(term => {
            const regex = new RegExp(`\\b${term}\\b`, 'gi');
            formattedAnswer = formattedAnswer.replace(regex, '<span class="text-info">$&</span>');
        });
        
        return formattedAnswer;
    }
    
    function createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'card result-card mb-3';
        
        let cardContent = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">${result.title || 'Untitled Document'}</h6>
                <span class="badge bg-secondary source-badge">${result.source}</span>
            </div>
            <div class="card-body">
        `;
        
        // Display different content based on source type
        if (result.source === 'Emergency Guidebook') {
            cardContent += `
                <p>${result.content}</p>
                <h6 class="mt-3">Protocols:</h6>
                <ul class="protocols-list">
                    ${result.protocols.map(protocol => `<li><i class="fas fa-check-circle text-info me-2"></i>${protocol}</li>`).join('')}
                </ul>
                <div class="mt-3">
                    <h6>Emergency Response:</h6>
                    <p class="mb-0">${result.emergency_response}</p>
                </div>
            `;
        } else if (result.source === 'Incident Report') {
            cardContent += `
                <div class="mb-2"><strong>ID:</strong> ${result.id}</div>
                <div class="mb-2"><strong>Description:</strong> ${result.description}</div>
                <div class="mb-2"><strong>Date:</strong> ${result.date}</div>
                <div class="mb-2"><strong>Severity:</strong> ${renderSeverityStars(result.severity)}</div>
                <div class="mt-3">
                    <h6>Resolution:</h6>
                    <p class="mb-0">${result.resolution}</p>
                </div>
            `;
        } else {
            // Generic document display
            cardContent += `<p>${result.content || 'No content available'}</p>`;
        }
        
        cardContent += `
                <div class="text-end mt-3">
                    <small class="text-muted">Relevance: ${Math.round(result.relevance_score * 100)}%</small>
                </div>
            </div>
        `;
        
        card.innerHTML = cardContent;
        return card;
    }
    
    function renderSeverityStars(severity) {
        const maxStars = 5;
        let stars = '';
        
        for (let i = 1; i <= maxStars; i++) {
            if (i <= severity) {
                stars += '<i class="fas fa-star text-warning"></i>';
            } else {
                stars += '<i class="far fa-star text-muted"></i>';
            }
        }
        
        return stars;
    }
    
    function showError(message) {
        // Create or update error message
        let errorAlert = document.getElementById('search-error');
        
        if (!errorAlert) {
            errorAlert = document.createElement('div');
            errorAlert.id = 'search-error';
            errorAlert.className = 'alert alert-danger mt-3';
            searchInput.parentNode.parentNode.appendChild(errorAlert);
        }
        
        errorAlert.textContent = message;
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            if (errorAlert.parentNode) {
                errorAlert.parentNode.removeChild(errorAlert);
            }
        }, 4000);
    }
});
