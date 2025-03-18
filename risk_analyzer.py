import re
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    def __init__(self):
        """Initialize the risk analyzer"""
        self.logger = logging.getLogger(__name__)
        
        # Risk severity criteria
        self.severity_criteria = {
            'keywords': {
                'severe': ['severe', 'major', 'critical', 'extreme', 'fatal', 'death', 'explosion'],
                'high': ['high', 'significant', 'serious', 'fire', 'injury', 'hospital', 'toxic'],
                'medium': ['medium', 'moderate', 'significant', 'spill', 'leak', 'exposure'],
                'low': ['low', 'minor', 'small', 'minimal', 'limited', 'contained']
            },
            'hazard_severity': {
                'toxic_gases': 5,
                'flammable_gases': 4,
                'corrosive_materials': 4,
                'flammable_liquids': 3,
                'oxidizers': 3,
                'common_chemicals': 2,
                'non_hazardous': 1
            }
        }
        
        # Risk severity levels
        self.severity_levels = {
            1: "Minimal Risk",
            2: "Low Risk",
            3: "Moderate Risk",
            4: "High Risk",
            5: "Critical Risk"
        }
        
        self.logger.info("RiskAnalyzer initialized")
    
    def assess_severity(self, incident_details):
        """Assess the severity of an incident based on its description"""
        self.logger.debug(f"Assessing severity for: {incident_details}")
        
        # Default severity and confidence
        severity = 3  # Start with moderate risk
        evidence = []
        
        # Check for severity keywords
        for level, keywords in self.severity_criteria['keywords'].items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', incident_details, re.IGNORECASE):
                    evidence.append(f"Contains '{keyword}' which indicates {level} severity")
                    if level == 'severe':
                        severity += 2
                    elif level == 'high':
                        severity += 1
                    elif level == 'medium':
                        pass  # Keep at 3
                    elif level == 'low':
                        severity -= 1
        
        # Check for hazard types
        for hazard, hazard_severity in self.severity_criteria['hazard_severity'].items():
            # Convert underscores to spaces for matching
            hazard_term = hazard.replace('_', ' ')
            if re.search(r'\b' + re.escape(hazard_term) + r'\b', incident_details, re.IGNORECASE):
                evidence.append(f"Involves '{hazard_term}' with base severity {hazard_severity}")
                severity = max(severity, hazard_severity)
        
        # Check for scale or quantity indicators
        quantity_pattern = r'\b(\d+)\s*(gallon|liter|kg|pound|ton|people|worker|patient|victim)\w*\b'
        quantity_matches = re.findall(quantity_pattern, incident_details, re.IGNORECASE)
        
        for match in quantity_matches:
            amount = int(match[0])
            unit = match[1].lower()
            
            if unit in ['gallon', 'liter'] and amount > 50:
                evidence.append(f"Large quantity: {amount} {unit}s")
                severity += 1
            elif unit in ['kg', 'pound'] and amount > 100:
                evidence.append(f"Large quantity: {amount} {unit}s")
                severity += 1
            elif unit in ['ton'] and amount > 1:
                evidence.append(f"Large quantity: {amount} {unit}s")
                severity += 2
            elif unit in ['people', 'worker', 'patient', 'victim'] and amount > 1:
                evidence.append(f"Multiple affected: {amount} {unit}s")
                severity += 1
        
        # Ensure severity is within bounds
        severity = max(1, min(5, severity))
        
        # Generate rationale
        rationale = "Risk assessment rationale:\n"
        if evidence:
            rationale += "\n".join(f"- {item}" for item in evidence)
        else:
            rationale += "- No specific risk factors identified, using default moderate risk assessment"
        
        rationale += f"\n\nFinal severity rating: {severity}/5 - {self.severity_levels[severity]}"
        
        return severity, rationale
    
    def generate_predictive_insights(self, incident_details, severity):
        """Generate predictive insights based on incident details and severity"""
        self.logger.debug(f"Generating insights for incident with severity {severity}")
        
        insights = []
        
        # Add general insight based on severity
        if severity >= 4:
            insights.append("This type of high-severity incident has a significant chance of recurrence if systematic safety measures are not implemented.")
        elif severity == 3:
            insights.append("Moderate-risk incidents like this frequently indicate underlying process or procedural weaknesses that should be addressed.")
        else:
            insights.append("While this is a lower-risk event, similar incidents can accumulate to create systemic risks if patterns are not identified and addressed.")
        
        # Add time-based insights
        current_date = datetime.now()
        month = current_date.month
        
        if 5 <= month <= 9:  # Summer months
            if "chemical" in incident_details.lower() or "spill" in incident_details.lower():
                insights.append("Chemical incidents tend to increase by 15-20% during summer months due to higher temperatures affecting storage stability and increasing vapor pressure.")
        
        if 11 <= month or month <= 2:  # Winter months
            if "fire" in incident_details.lower() or "heating" in incident_details.lower():
                insights.append("Fire and heating-related incidents show a 25% increase during winter months due to increased use of heating equipment and systems.")
        
        # Add specific hazard insights
        if "corrosive" in incident_details.lower() or "acid" in incident_details.lower() or "base" in incident_details.lower():
            insights.append("Corrosive material incidents historically show a 60% likelihood of equipment failure as a root cause, with 30% related to procedural non-compliance.")
        
        if "gas" in incident_details.lower() or "leak" in incident_details.lower():
            insights.append("Gas leak incidents have a 40% correlation with maintenance delays and a 35% correlation with equipment reaching end-of-service life.")
        
        if "fire" in incident_details.lower() or "explosion" in incident_details.lower():
            insights.append("Fire/explosion events show a 70% correlation with failure to implement proper hot work procedures and isolation protocols.")
        
        # Add preventative recommendation
        if severity >= 4:
            insights.append("Recommendation: Implement comprehensive process safety management review including hazard analysis (HAZOP) and establish more frequent inspection protocols.")
        elif severity == 3:
            insights.append("Recommendation: Review and update standard operating procedures and ensure proper training and competency verification for all personnel involved.")
        else:
            insights.append("Recommendation: Document the incident in detail and incorporate into safety briefings to maintain awareness of potential hazards.")
        
        # Format and return the insights
        formatted_insights = "Predictive Insights:\n\n" + "\n\n".join(f"• {insight}" for insight in insights)
        
        return formatted_insights
