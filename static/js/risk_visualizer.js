document.addEventListener('DOMContentLoaded', function() {
    const riskForm = document.getElementById('risk-assessment-form');
    const incidentTitle = document.getElementById('incident-title');
    const incidentDetails = document.getElementById('incident-details');
    const loadingAssessment = document.getElementById('loading-assessment');
    const resultsContainer = document.getElementById('results-container');
    const severityIndicator = document.getElementById('severity-indicator');
    const severityScore = document.getElementById('severity-score');
    const severityClassification = document.getElementById('severity-classification');
    const severityRationale = document.getElementById('severity-rationale');
    const predictiveInsights = document.getElementById('predictive-insights');
    
    // Initialize severity chart with sample data
    initSeverityChart();
    
    // Set up event listeners
    riskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        performRiskAssessment();
    });
    
    function performRiskAssessment() {
        const title = incidentTitle.value.trim();
        const details = incidentDetails.value.trim();
        
        if (!title || !details) {
            showError('Please provide both a title and details for the incident');
            return;
        }
        
        // Show loading indicator
        loadingAssessment.style.display = 'block';
        resultsContainer.style.display = 'none';
        
        // Make API request
        fetch('/api/risk-assessment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                title: title,
                details: details
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
            loadingAssessment.style.display = 'none';
            
            // Display results
            displayResults(data);
        })
        .catch(error => {
            console.error('Error during risk assessment:', error);
            loadingAssessment.style.display = 'none';
            showError('An error occurred during risk assessment. Please try again.');
        });
    }
    
    function displayResults(data) {
        // Update severity indicator position
        const position = (data.severity / 5) * 100;
        severityIndicator.style.left = `${position}%`;
        
        // Update severity score and classification
        severityScore.textContent = data.severity;
        
        const classifications = {
            1: "Minimal Risk",
            2: "Low Risk",
            3: "Moderate Risk",
            4: "High Risk",
            5: "Critical Risk"
        };
        
        severityClassification.textContent = classifications[data.severity] || "Unknown";
        
        // Update color based on severity
        severityClassification.className = '';
        if (data.severity >= 4) {
            severityClassification.classList.add('text-danger', 'fw-bold');
        } else if (data.severity === 3) {
            severityClassification.classList.add('text-warning', 'fw-bold');
        } else {
            severityClassification.classList.add('text-success');
        }
        
        // Update rationale
        severityRationale.textContent = data.rationale;
        
        // Update predictive insights
        predictiveInsights.textContent = data.insights;
        
        // Show results container
        resultsContainer.style.display = 'block';
        
        // Update chart with new data point
        updateChartWithNewAssessment(data.severity);
    }
    
    function initSeverityChart() {
        const ctx = document.getElementById('severity-chart').getContext('2d');
        
        // Sample historical data
        const sampleData = {
            labels: ['Minimal', 'Low', 'Moderate', 'High', 'Critical'],
            datasets: [{
                label: 'Historical Incidents by Severity',
                data: [5, 12, 18, 8, 3],
                backgroundColor: [
                    '#28a745',  // Minimal - Green
                    '#a3c739',  // Low - Light Green/Yellow
                    '#ffc107',  // Moderate - Yellow
                    '#fd7e14',  // High - Orange
                    '#dc3545'   // Critical - Red
                ],
                borderWidth: 1
            }]
        };
        
        window.severityChart = new Chart(ctx, {
            type: 'bar',
            data: sampleData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Incidents'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Severity Level'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Incidents: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    function updateChartWithNewAssessment(severity) {
        // Add the new assessment to the chart data
        if (window.severityChart) {
            // Severity is 1-5, array is 0-4
            const dataIndex = severity - 1;
            window.severityChart.data.datasets[0].data[dataIndex]++;
            window.severityChart.update();
        }
    }
    
    function showError(message) {
        // Create or update error message
        let errorAlert = document.getElementById('assessment-error');
        
        if (!errorAlert) {
            errorAlert = document.createElement('div');
            errorAlert.id = 'assessment-error';
            errorAlert.className = 'alert alert-danger mt-3';
            riskForm.appendChild(errorAlert);
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
