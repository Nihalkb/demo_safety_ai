import logging
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from models import Incident
from sqlalchemy import func

# Risk severity levels and their weights
SEVERITY_LEVELS = {
    'Low': 1,
    'Medium': 2,
    'High': 3,
    'Critical': 4
}

def categorize_risk(incidents):
    """Categorize incidents by risk severity"""
    categorized = {
        'Low': [],
        'Medium': [],
        'High': [],
        'Critical': []
    }
    
    # Group incidents by severity
    for incident in incidents:
        if incident.severity in categorized:
            categorized[incident.severity].append({
                'id': incident.id,
                'title': incident.title,
                'description': incident.description[:100] + '...' if len(incident.description) > 100 else incident.description,
                'date': incident.date_occurred.strftime('%Y-%m-%d'),
                'location': incident.location,
                'response_time': incident.response_time_minutes
            })
    
    # Add counts
    result = {
        'categories': {
            severity: {
                'count': len(incidents),
                'incidents': incidents[:5]  # Limit to 5 incidents per category
            }
            for severity, incidents in categorized.items()
        },
        'total_count': len(incidents),
        'distribution': {
            severity: len(incidents) / max(len(incidents), 1) * 100
            for severity, incidents in categorized.items()
        }
    }
    
    return result

def predict_risk():
    """Generate risk predictions based on historical incidents"""
    try:
        # Get incidents from the past year
        one_year_ago = datetime.now() - timedelta(days=365)
        recent_incidents = Incident.query.filter(Incident.date_occurred >= one_year_ago).all()
        
        if not recent_incidents:
            return {
                'message': 'Not enough historical data for risk prediction',
                'predictions': []
            }
        
        # Analyze incident frequency by location
        locations = [incident.location for incident in recent_incidents if incident.location]
        location_counts = Counter(locations)
        high_risk_locations = [
            {
                'location': location,
                'incident_count': count,
                'risk_level': 'High' if count >= 3 else 'Medium'
            }
            for location, count in location_counts.most_common(5) if count > 1
        ]
        
        # Analyze incident types/keywords
        keywords = []
        for incident in recent_incidents:
            if incident.keywords:
                keywords.extend(incident.keywords.split(','))
        
        keyword_counts = Counter(keywords)
        risk_trends = [
            {
                'keyword': keyword,
                'incident_count': count,
                'risk_level': 'High' if count >= 3 else 'Medium'
            }
            for keyword, count in keyword_counts.most_common(5) if count > 1
        ]
        
        # Calculate average severity over time
        months_data = {}
        for incident in recent_incidents:
            month_key = incident.date_occurred.strftime('%Y-%m')
            if month_key not in months_data:
                months_data[month_key] = {'count': 0, 'severity_sum': 0}
            
            months_data[month_key]['count'] += 1
            months_data[month_key]['severity_sum'] += SEVERITY_LEVELS.get(incident.severity, 1)
        
        severity_trend = [
            {
                'month': month,
                'average_severity': data['severity_sum'] / data['count'],
                'incident_count': data['count']
            }
            for month, data in months_data.items()
        ]
        
        # Sort by month
        severity_trend.sort(key=lambda x: x['month'])
        
        # Calculate trend direction
        if len(severity_trend) >= 2:
            current = severity_trend[-1]['average_severity']
            previous = severity_trend[-2]['average_severity'] if len(severity_trend) > 1 else 0
            trend_direction = 'increasing' if current > previous else 'decreasing' if current < previous else 'stable'
        else:
            trend_direction = 'insufficient data'
        
        return {
            'high_risk_locations': high_risk_locations,
            'risk_trends': risk_trends,
            'severity_trend': severity_trend,
            'trend_direction': trend_direction,
            'prediction_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        logging.error(f"Error in risk prediction: {e}")
        return {
            'message': f'Error generating risk predictions: {str(e)}',
            'predictions': []
        }

def calculate_industry_average_response():
    """Calculate industry average response time"""
    try:
        avg_response = Incident.query.with_entities(func.avg(Incident.response_time_minutes)).scalar()
        if avg_response is None:
            return None
        return round(avg_response, 2)
    except Exception as e:
        logging.error(f"Error calculating average response time: {e}")
        return None
