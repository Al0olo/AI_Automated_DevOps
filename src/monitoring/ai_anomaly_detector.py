import numpy as np
from typing import Dict, List, Optional
from datadog_api_client import ApiClient, Configuration
from sklearn.ensemble import IsolationForest
import pandas as pd
from datetime import datetime, timedelta

class AIAnomalyDetector:
    def __init__(self, config: Dict):
        """
        Initialize the AI Anomaly Detector.
        
        Args:
            config: Configuration dictionary containing:
                - anomaly_threshold: float
                - training_period_days: int
                - minimum_datapoints: int
                - sensitivity: float
        """
        self.config = config
        self.model = self._initialize_model()
        self.baseline = self._load_baseline()
        self.history = {}
        
    def _initialize_model(self):
        """Initialize the anomaly detection model."""
        return IsolationForest(
            contamination=self.config.get('sensitivity', 0.1),
            random_state=42
        )
    
    def detect_anomalies(self, metrics: Dict[str, float]) -> List[Dict]:
        """
        Detect anomalies in the current metrics.
        
        Args:
            metrics: Dictionary of metric name to current value
            
        Returns:
            List of detected anomalies with severity and confidence
        """
        anomalies = []
        current_time = datetime.now()
        
        # Update history
        for metric_name, value in metrics.items():
            if metric_name not in self.history:
                self.history[metric_name] = []
            self.history[metric_name].append({
                'timestamp': current_time,
                'value': value
            })
            
            # Remove old data points
            cutoff_time = current_time - timedelta(days=self.config['training_period_days'])
            self.history[metric_name] = [
                point for point in self.history[metric_name]
                if point['timestamp'] > cutoff_time
            ]
            
            # Check for anomalies if we have enough data
            if len(self.history[metric_name]) >= self.config['minimum_datapoints']:
                anomaly = self._check_metric_anomaly(metric_name, value)
                if anomaly:
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _check_metric_anomaly(self, metric_name: str, current_value: float) -> Optional[Dict]:
        """Check if a specific metric is anomalous."""
        historical_values = [point['value'] for point in self.history[metric_name]]
        
        # Prepare data for isolation forest
        X = np.array(historical_values).reshape(-1, 1)
        self.model.fit(X)
        
        # Get anomaly score
        anomaly_score = self.model.score_samples(np.array([[current_value]]))
        
        if anomaly_score[0] < -self.config['anomaly_threshold']:
            severity = self._calculate_severity(anomaly_score[0])
            confidence = self._calculate_confidence(anomaly_score[0])
            
            return {
                'metric': metric_name,
                'current_value': current_value,
                'severity': severity,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'suggested_actions': self._suggest_actions(metric_name, current_value, severity)
            }
        
        return None
    
    def _calculate_severity(self, anomaly_score: float) -> str:
        """Calculate severity based on anomaly score."""
        score = abs(anomaly_score)
        if score > 0.8:
            return 'critical'
        elif score > 0.6:
            return 'high'
        elif score > 0.4:
            return 'medium'
        return 'low'
    
    def _calculate_confidence(self, anomaly_score: float) -> float:
        """Calculate confidence score for the anomaly detection."""
        return min(abs(anomaly_score) * 100, 99.9)
    
    def _suggest_actions(self, metric_name: str, value: float, severity: str) -> List[str]:
        """Suggest remediation actions based on the anomaly."""
        actions = []
        
        # Common metric-specific suggestions
        if metric_name == 'cpu_usage':
            if value > 90:
                actions.extend([
                    'Scale up the service horizontally',
                    'Check for CPU-intensive processes',
                    'Review recent deployments',
                    'Analyze application profiling data'
                ])
            elif value < 10:
                actions.extend([
                    'Consider scaling down to optimize resources',
                    'Check for service availability',
                    'Verify monitoring setup'
                ])
                
        elif metric_name == 'memory_usage':
            if value > 85:
                actions.extend([
                    'Investigate potential memory leaks',
                    'Consider increasing memory allocation',
                    'Review garbage collection metrics',
                    'Analyze heap dumps'
                ])
                
        elif metric_name == 'error_rate':
            if value > 5:
                actions.extend([
                    'Review error logs',
                    'Check dependent services',
                    'Analyze recent changes',
                    'Consider rolling back recent deployment'
                ])
                
        # Add severity-specific general actions
        if severity == 'critical':
            actions.extend([
                'Escalate to on-call team immediately',
                'Prepare incident response',
                'Consider automated remediation'
            ])
        elif severity == 'high':
            actions.extend([
                'Monitor closely for next hour',
                'Prepare for potential escalation',
                'Review related metrics'
            ])
            
        return actions