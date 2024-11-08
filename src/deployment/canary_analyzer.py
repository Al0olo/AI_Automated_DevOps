from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
import pandas as pd
from datetime import datetime, timedelta
import logging
import asyncio
from prometheus_client import CollectorRegistry, Counter, Gauge

class CanaryAnalyzer:
    def __init__(self, config: Dict):
        """
        Initialize the Canary Analyzer.
        
        Args:
            config: Configuration dictionary containing:
                - analysis_thresholds
                - monitoring_interval
                - metrics_config
                - alert_thresholds
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics_registry = CollectorRegistry()
        self.anomaly_detector = self._initialize_anomaly_detector()
        self.baseline_metrics = {}
        self.canary_metrics = {}
        
    async def analyze_canary(self, canary_data: Dict) -> Dict:
        """
        Perform comprehensive canary analysis.
        
        Args:
            canary_data: Dictionary containing canary deployment data
            
        Returns:
            Analysis results and recommendations
        """
        try:
            # Collect metrics
            baseline_metrics = await self._collect_baseline_metrics(canary_data)
            canary_metrics = await self._collect_canary_metrics(canary_data)
            
            # Perform analysis
            analysis_results = {
                'performance_analysis': self._analyze_performance(
                    baseline_metrics,
                    canary_metrics
                ),
                'error_analysis': self._analyze_errors(
                    baseline_metrics,
                    canary_metrics
                ),
                'resource_analysis': self._analyze_resources(
                    baseline_metrics,
                    canary_metrics
                ),
                'user_impact_analysis': self._analyze_user_impact(
                    baseline_metrics,
                    canary_metrics
                )
            }
            
            # Generate decision
            decision = self._make_promotion_decision(analysis_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                analysis_results,
                decision
            )
            
            return {
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis_results,
                'decision': decision,
                'recommendations': recommendations,
                'confidence_score': self._calculate_confidence(analysis_results)
            }
            
        except Exception as e:
            self.logger.error(f"Canary analysis failed: {str(e)}")
            return self._generate_error_response(str(e))
    
    def _initialize_anomaly_detector(self) -> IsolationForest:
        """Initialize the anomaly detection model."""
        return IsolationForest(
            contamination=self.config.get('anomaly_threshold', 0.1),
            random_state=42
        )
    
    async def _collect_baseline_metrics(self, canary_data: Dict) -> Dict:
        """Collect metrics from baseline deployment."""
        metrics = {}
        try:
            # Performance metrics
            metrics['performance'] = {
                'latency': await self._get_latency_metrics(
                    canary_data['baseline']['service']
                ),
                'throughput': await self._get_throughput_metrics(
                    canary_data['baseline']['service']
                ),
                'success_rate': await self._get_success_rate_metrics(
                    canary_data['baseline']['service']
                )
            }
            
            # Resource metrics
            metrics['resources'] = {
                'cpu_usage': await self._get_cpu_metrics(
                    canary_data['baseline']['service']
                ),
                'memory_usage': await self._get_memory_metrics(
                    canary_data['baseline']['service']
                ),
                'network_io': await self._get_network_metrics(
                    canary_data['baseline']['service']
                )
            }
            
            # Error metrics
            metrics['errors'] = {
                'error_rate': await self._get_error_rate_metrics(
                    canary_data['baseline']['service']
                ),
                'error_types': await self._get_error_types_metrics(
                    canary_data['baseline']['service']
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect baseline metrics: {str(e)}")
            
        return metrics
    
    async def _collect_canary_metrics(self, canary_data: Dict) -> Dict:
        """Collect metrics from canary deployment."""
        return await self._collect_baseline_metrics(
            {'baseline': {'service': canary_data['canary']['service']}}
        )
    
    def _analyze_performance(
        self,
        baseline_metrics: Dict,
        canary_metrics: Dict
    ) -> Dict:
        """Analyze performance metrics comparison."""
        analysis = {}
        
        # Latency analysis
        latency_diff = self._calculate_metric_difference(
            baseline_metrics['performance']['latency'],
            canary_metrics['performance']['latency']
        )
        
        analysis['latency'] = {
            'difference_percentage': latency_diff,
            'significant': abs(latency_diff) > self.config['thresholds']['latency'],
            'impact': self._determine_impact_level(latency_diff)
        }
        
        # Throughput analysis
        throughput_diff = self._calculate_metric_difference(
            baseline_metrics['performance']['throughput'],
            canary_metrics['performance']['throughput']
        )
        
        analysis['throughput'] = {
            'difference_percentage': throughput_diff,
            'significant': abs(throughput_diff) > self.config['thresholds']['throughput'],
            'impact': self._determine_impact_level(throughput_diff)
        }
        
        # Success rate analysis
        success_rate_diff = self._calculate_metric_difference(
            baseline_metrics['performance']['success_rate'],
            canary_metrics['performance']['success_rate']
        )
        
        analysis['success_rate'] = {
            'difference_percentage': success_rate_diff,
            'significant': abs(success_rate_diff) > self.config['thresholds']['success_rate'],
            'impact': self._determine_impact_level(success_rate_diff)
        }
        
        return analysis
    
    def _analyze_errors(
        self,
        baseline_metrics: Dict,
        canary_metrics: Dict
    ) -> Dict:
        """Analyze error metrics comparison."""
        analysis = {}
        
        # Error rate analysis
        error_rate_diff = self._calculate_metric_difference(
            baseline_metrics['errors']['error_rate'],
            canary_metrics['errors']['error_rate']
        )
        
        analysis['error_rate'] = {
            'difference_percentage': error_rate_diff,
            'significant': abs(error_rate_diff) > self.config['thresholds']['error_rate'],
            'impact': self._determine_impact_level(error_rate_diff)
        }
        
        # Error types analysis
        error_types_analysis = self._analyze_error_types(
            baseline_metrics['errors']['error_types'],
            canary_metrics['errors']['error_types']
        )
        
        analysis['error_types'] = {
            'new_errors': error_types_analysis['new_errors'],
            'resolved_errors': error_types_analysis['resolved_errors'],
            'impact': error_types_analysis['impact']
        }
        
        return analysis
    
    def _analyze_resources(
        self,
        baseline_metrics: Dict,
        canary_metrics: Dict
    ) -> Dict:
        """Analyze resource utilization comparison."""
        analysis = {}
        
        # CPU analysis
        cpu_diff = self._calculate_metric_difference(
            baseline_metrics['resources']['cpu_usage'],
            canary_metrics['resources']['cpu_usage']
        )
        
        analysis['cpu'] = {
            'difference_percentage': cpu_diff,
            'significant': abs(cpu_diff) > self.config['thresholds']['cpu'],
            'impact': self._determine_impact_level(cpu_diff)
        }
        
        # Memory analysis
        memory_diff = self._calculate_metric_difference(
            baseline_metrics['resources']['memory_usage'],
            canary_metrics['resources']['memory_usage']
        )
        
        analysis['memory'] = {
            'difference_percentage': memory_diff,
            'significant': abs(memory_diff) > self.config['thresholds']['memory'],
            'impact': self._determine_impact_level(memory_diff)
        }
        
        return analysis
    
    def _make_promotion_decision(self, analysis_results: Dict) -> Dict:
        """Make decision about canary promotion."""
        # Initialize decision metrics
        decision_metrics = {
            'performance_score': self._calculate_performance_score(
                analysis_results['performance_analysis']
            ),
            'error_score': self._calculate_error_score(
                analysis_results['error_analysis']
            ),
            'resource_score': self._calculate_resource_score(
                analysis_results['resource_analysis']
            ),
            'user_impact_score': self._calculate_user_impact_score(
                analysis_results['user_impact_analysis']
            )
        }
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(decision_metrics)
        
        # Make decision
        should_promote = overall_score >= self.config['promotion_threshold']
        
        return {
            'promote': should_promote,
            'overall_score': overall_score,
            'metrics_scores': decision_metrics,
            'confidence': self._calculate_decision_confidence(decision_metrics),
            'reasons': self._generate_decision_reasons(
                should_promote,
                decision_metrics,
                analysis_results
            )
        }
    
    def _generate_recommendations(
        self,
        analysis_results: Dict,
        decision: Dict
    ) -> List[Dict]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Performance recommendations
        if analysis_results['performance_analysis']['latency']['significant']:
            recommendations.append({
                'type': 'performance',
                'severity': analysis_results['performance_analysis']['latency']['impact'],
                'description': 'Significant latency difference detected',
                'action': self._generate_latency_recommendation(
                    analysis_results['performance_analysis']['latency']
                )
            })
            
        # Error recommendations
        if analysis_results['error_analysis']['error_rate']['significant']:
            recommendations.append({
                'type': 'error',
                'severity': analysis_results['error_analysis']['error_rate']['impact'],
                'description': 'Significant error rate difference detected',
                'action': self._generate_error_recommendation(
                    analysis_results['error_analysis']
                )
            })
            
        # Resource recommendations
        if analysis_results['resource_analysis']['cpu']['significant']:
            recommendations.append({
                'type': 'resource',
                'severity': analysis_results['resource_analysis']['cpu']['impact'],
                'description': 'Significant CPU usage difference detected',
                'action': self._generate_resource_recommendation(
                    analysis_results['resource_analysis']
                )
            })
            
        return recommendations
    
    def _calculate_decision_confidence(self, decision_metrics: Dict) -> float:
        """Calculate confidence level in the decision."""
        weights = self.config.get('confidence_weights', {
            'performance_score': 0.4,
            'error_score': 0.3,
            'resource_score': 0.2,
            'user_impact_score': 0.1
        })
        
        confidence = sum(
            score * weights[metric]
            for metric, score in decision_metrics.items()
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _determine_impact_level(self, difference: float) -> str:
        """Determine impact level based on metric difference."""
        thresholds = self.config.get('impact_thresholds', {
            'high': 20,
            'medium': 10,
            'low': 5
        })
        
        abs_diff = abs(difference)
        
        if abs_diff > thresholds['high']:
            return 'high'
        elif abs_diff > thresholds['medium']:
            return 'medium'
        elif abs_diff > thresholds['low']:
            return 'low'
        else:
            return 'insignificant'