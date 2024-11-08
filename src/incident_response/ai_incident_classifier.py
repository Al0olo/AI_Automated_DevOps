import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
import json

class AIIncidentClassifier:
    def __init__(self, config: Dict):
        """
        Initialize the AI Incident Classifier.
        
        Args:
            config: Configuration dictionary containing:
                - model_config: ML model parameters
                - severity_thresholds: Thresholds for severity classification
                - classification_rules: Custom classification rules
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = RandomForestClassifier(**config.get('model_config', {}))
        self.incident_history = []
        
    async def classify_incident(self, incident_data: Dict) -> Dict:
        """
        Classify an incident using AI.
        
        Args:
            incident_data: Dictionary containing incident information
            
        Returns:
            Dictionary containing classification results
        """
        try:
            # Extract features
            features = self._extract_features(incident_data)
            
            # Perform classification
            classification = self._classify(features)
            
            # Determine severity
            severity = self._determine_severity(incident_data, classification)
            
            # Generate response plan
            response_plan = self._generate_response_plan(classification, severity)
            
            # Update incident history
            self._update_history(incident_data, classification, severity)
            
            return {
                'classification': classification,
                'severity': severity,
                'confidence': classification['confidence'],
                'response_plan': response_plan,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Classification failed: {str(e)}")
            return self._generate_fallback_classification(incident_data, str(e))
    
    def _extract_features(self, incident_data: Dict) -> Dict:
        """Extract relevant features from incident data."""
        features = {}
        
        # System metrics
        if 'metrics' in incident_data:
            features.update({
                'cpu_usage': incident_data['metrics'].get('cpu_usage', 0),
                'memory_usage': incident_data['metrics'].get('memory_usage', 0),
                'error_rate': incident_data['metrics'].get('error_rate', 0),
                'latency': incident_data['metrics'].get('latency', 0)
            })
            
        # Error patterns
        if 'error_logs' in incident_data:
            features['error_text'] = self.vectorizer.fit_transform(
                incident_data['error_logs']
            ).toarray()
            
        # Time-based features
        current_time = datetime.now()
        features.update({
            'hour_of_day': current_time.hour,
            'day_of_week': current_time.weekday(),
            'is_weekend': 1 if current_time.weekday() >= 5 else 0
        })
        
        # System state
        if 'system_state' in incident_data:
            features.update({
                'deployment_age': incident_data['system_state'].get('deployment_age', 0),
                'recent_changes': len(incident_data['system_state'].get('recent_changes', [])),
                'active_users': incident_data['system_state'].get('active_users', 0)
            })
            
        return features
    
    def _classify(self, features: Dict) -> Dict:
        """Classify incident based on extracted features."""
        try:
            # Prepare feature vector
            feature_vector = np.array([list(features.values())])
            
            # Get prediction and confidence
            prediction = self.classifier.predict(feature_vector)[0]
            confidence = np.max(self.classifier.predict_proba(feature_vector)[0])
            
            # Apply classification rules
            final_classification = self._apply_classification_rules(
                prediction, confidence, features
            )
            
            return {
                'type': final_classification,
                'confidence': float(confidence),
                'features_used': list(features.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Classification calculation failed: {str(e)}")
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _determine_severity(self, incident_data: Dict, classification: Dict) -> str:
        """Determine incident severity based on classification and metrics."""
        severity_score = 0
        thresholds = self.config['severity_thresholds']
        
        # Impact-based scoring
        if 'metrics' in incident_data:
            metrics = incident_data['metrics']
            
            # CPU Impact
            if metrics.get('cpu_usage', 0) > thresholds.get('cpu_critical', 90):
                severity_score += 3
            elif metrics.get('cpu_usage', 0) > thresholds.get('cpu_warning', 75):
                severity_score += 1
                
            # Memory Impact
            if metrics.get('memory_usage', 0) > thresholds.get('memory_critical', 90):
                severity_score += 3
            elif metrics.get('memory_usage', 0) > thresholds.get('memory_warning', 75):
                severity_score += 1
                
            # Error Rate Impact
            if metrics.get('error_rate', 0) > thresholds.get('error_critical', 5):
                severity_score += 4
            elif metrics.get('error_rate', 0) > thresholds.get('error_warning', 1):
                severity_score += 2
                
        # User Impact
        if incident_data.get('affected_users', 0) > thresholds.get('users_critical', 1000):
            severity_score += 5
        elif incident_data.get('affected_users', 0) > thresholds.get('users_warning', 100):
            severity_score += 2
            
        # Business Impact
        if incident_data.get('business_impact', 'low') == 'high':
            severity_score += 5
        elif incident_data.get('business_impact', 'low') == 'medium':
            severity_score += 3
            
        # Map score to severity level
        if severity_score >= 10:
            return 'critical'
        elif severity_score >= 7:
            return 'high'
        elif severity_score >= 4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_response_plan(self, classification: Dict, severity: str) -> Dict:
        """Generate an AI-driven incident response plan."""
        response_plan = {
            'immediate_actions': [],
            'investigation_steps': [],
            'remediation_steps': [],
            'prevention_steps': []
        }
        
        # Get base response plan from classification type
        base_plan = self.config['response_templates'].get(
            classification['type'],
            self.config['response_templates']['default']
        )
        
        # Customize plan based on severity
        if severity == 'critical':
            response_plan['immediate_actions'].extend([
                "Initiate incident bridge",
                "Notify senior management",
                "Prepare customer communication",
                "Consider service degradation"
            ])
        elif severity == 'high':
            response_plan['immediate_actions'].extend([
                "Alert on-call team",
                "Start incident documentation",
                "Monitor user impact"
            ])
            
        # Add classification-specific steps
        response_plan['investigation_steps'].extend(base_plan.get('investigation_steps', []))
        response_plan['remediation_steps'].extend(base_plan.get('remediation_steps', []))
        
        # Add prevention steps based on historical data
        similar_incidents = self._find_similar_incidents(classification)
        if similar_incidents:
            prevention_steps = self._analyze_prevention_patterns(similar_incidents)
            response_plan['prevention_steps'].extend(prevention_steps)
            
        return response_plan
    
    def _update_history(self, incident_data: Dict, classification: Dict, severity: str):
        """Update incident history with new incident."""
        self.incident_history.append({
            'timestamp': datetime.now().isoformat(),
            'incident_data': incident_data,
            'classification': classification,
            'severity': severity
        })
        
        # Maintain history size
        max_history = self.config.get('max_history_size', 1000)
        if len(self.incident_history) > max_history:
            self.incident_history = self.incident_history[-max_history:]
            
    def _find_similar_incidents(self, classification: Dict) -> List[Dict]:
        """Find similar incidents in history."""
        similar_incidents = []
        
        for incident in self.incident_history:
            if incident['classification']['type'] == classification['type']:
                similar_incidents.append(incident)
                
        return similar_incidents[-5:]  # Return 5 most recent similar incidents
    
    def _analyze_prevention_patterns(self, incidents: List[Dict]) -> List[str]:
        """Analyze patterns in similar incidents to suggest prevention steps."""
        prevention_steps = set()
        
        for incident in incidents:
            if 'resolution' in incident['incident_data']:
                prevention_steps.update(
                    incident['incident_data']['resolution'].get('prevention_steps', [])
                )
                
        return list(prevention_steps)
    
    def _generate_fallback_classification(self, incident_data: Dict, error: str) -> Dict:
        """Generate fallback classification when AI classification fails."""
        return {
            'classification': {
                'type': 'unknown',
                'confidence': 0.0,
                'error': error
            },
            'severity': 'medium',  # Conservative default
            'response_plan': {
                'immediate_actions': [
                    "Manually review incident",
                    "Engage on-call engineer",
                    "Monitor system metrics"
                ],
                'investigation_steps': [
                    "Review error logs",
                    "Check recent changes",
                    "Monitor key metrics"
                ],
                'remediation_steps': [
                    "Follow standard operating procedures",
                    "Document findings"
                ],
                'prevention_steps': [
                    "Update incident response playbook",
                    "Review classification system"
                ]
            },
            'timestamp': datetime.now().isoformat()
        }