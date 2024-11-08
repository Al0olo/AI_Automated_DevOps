import kubernetes as k8s
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime
import yaml
import json
from prometheus_api_client import PrometheusConnect
import numpy as np
from sklearn.ensemble import IsolationForest

class AIDeploymentManager:
    def __init__(self, config: Dict):
        """
        Initialize the AI Deployment Manager.
        
        Args:
            config: Configuration dictionary containing:
                - deployment_strategy
                - monitoring_endpoints
                - rollback_threshold
                - canary_config
                - health_check_config
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Kubernetes client
        try:
            k8s.config.load_incluster_config()
        except k8s.config.ConfigException:
            k8s.config.load_kube_config()
            
        self.k8s_apps = k8s.client.AppsV1Api()
        self.k8s_core = k8s.client.CoreV1Api()
        
        # Initialize Prometheus client for metrics
        if 'prometheus_url' in config:
            self.prometheus = PrometheusConnect(url=config['prometheus_url'])
        else:
            self.prometheus = None
            
        # Initialize anomaly detection model
        self.anomaly_detector = IsolationForest(
            contamination=config.get('anomaly_threshold', 0.1)
        )
        
        self.deployment_history = []
        
    async def deploy(self, deployment_spec: Dict) -> Dict:
        """
        Execute an AI-driven deployment.
        
        Args:
            deployment_spec: Kubernetes deployment specification
            
        Returns:
            Dictionary containing deployment results and metrics
        """
        try:
            # Pre-deployment checks
            self.logger.info("Running pre-deployment checks...")
            pre_check_result = await self._run_pre_deployment_checks(deployment_spec)
            if not pre_check_result['success']:
                return {
                    'status': 'failed',
                    'stage': 'pre-deployment',
                    'reason': pre_check_result['reason']
                }
            
            # Determine deployment strategy
            strategy = self._determine_deployment_strategy(deployment_spec)
            self.logger.info(f"Selected deployment strategy: {strategy}")
            
            # Execute deployment based on strategy
            if strategy == 'canary':
                result = await self._execute_canary_deployment(deployment_spec)
            elif strategy == 'blue_green':
                result = await self._execute_blue_green_deployment(deployment_spec)
            else:
                result = await self._execute_rolling_deployment(deployment_spec)
                
            # Post-deployment analysis
            analysis = await self._analyze_deployment(result)
            
            # Record deployment
            self._record_deployment(deployment_spec, strategy, result, analysis)
            
            return {
                'status': 'success' if result['success'] else 'failed',
                'strategy': strategy,
                'metrics': result['metrics'],
                'analysis': analysis
            }
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'rollback_status': await self._handle_rollback(deployment_spec)
            }
    
    async def _run_pre_deployment_checks(self, deployment_spec: Dict) -> Dict:
        """Run AI-driven pre-deployment checks."""
        checks = {
            'resource_availability': await self._check_resource_availability(deployment_spec),
            'system_health': await self._check_system_health(),
            'dependency_health': await self._check_dependencies(deployment_spec),
            'security_compliance': await self._check_security_compliance(deployment_spec)
        }
        
        # Analyze all check results
        all_passed = all(check['success'] for check in checks.values())
        failed_checks = [name for name, check in checks.items() if not check['success']]
        
        return {
            'success': all_passed,
            'checks': checks,
            'failed_checks': failed_checks,
            'reason': '; '.join(check['reason'] for check in checks.values() if not check['success'])
        }
    
    async def _check_resource_availability(self, deployment_spec: Dict) -> Dict:
        """Check if required resources are available."""
        try:
            # Get node resources
            nodes = self.k8s_core.list_node()
            available_resources = {
                'cpu': 0,
                'memory': 0
            }
            
            for node in nodes.items:
                allocatable = node.status.allocatable
                available_resources['cpu'] += float(allocatable['cpu'])
                available_resources['memory'] += int(allocatable['memory'].rstrip('Ki')) / 1024
                
            # Calculate required resources
            required_resources = {
                'cpu': 0,
                'memory': 0
            }
            
            for container in deployment_spec['spec']['template']['spec']['containers']:
                if 'resources' in container:
                    resources = container['resources'].get('requests', {})
                    if 'cpu' in resources:
                        required_resources['cpu'] += float(resources['cpu'])
                    if 'memory' in resources:
                        required_resources['memory'] += int(resources['memory'].rstrip('Mi'))
                        
            # Check if resources are available
            cpu_available = available_resources['cpu'] >= required_resources['cpu']
            memory_available = available_resources['memory'] >= required_resources['memory']
            
            return {
                'success': cpu_available and memory_available,
                'reason': '' if (cpu_available and memory_available) else 
                         'Insufficient resources available'
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Failed to check resource availability: {str(e)}"
            }
    
    async def _check_system_health(self) -> Dict:
        """Check overall system health."""
        try:
            if self.prometheus:
                # Get key metrics
                metrics = {
                    'cpu_usage': self.prometheus.custom_query('avg(container_cpu_usage_seconds_total)'),
                    'memory_usage': self.prometheus.custom_query('avg(container_memory_usage_bytes)'),
                    'error_rate': self.prometheus.custom_query('sum(rate(http_requests_total{code=~"5.."}[5m]))')
                }
                
                # Check if metrics are within acceptable ranges
                health_checks = {
                    'cpu_usage': float(metrics['cpu_usage'][0]['value'][1]) < 80,
                    'memory_usage': float(metrics['memory_usage'][0]['value'][1]) < 80,
                    'error_rate': float(metrics['error_rate'][0]['value'][1]) < 5
                }
                
                all_healthy = all(health_checks.values())
                return {
                    'success': all_healthy,
                    'reason': '' if all_healthy else 'System health checks failed'
                }
            else:
                return {'success': True, 'reason': 'No health metrics configured'}
                
        except Exception as e:
            return {
                'success': False,
                'reason': f"Failed to check system health: {str(e)}"
            }
    
    def _determine_deployment_strategy(self, deployment_spec: Dict) -> str:
        """Use AI to determine the best deployment strategy."""
        # Get historical deployment data
        recent_deployments = self.deployment_history[-10:]
        
        # Calculate success rates for different strategies
        strategy_success_rates = {}
        for strategy in ['canary', 'blue_green', 'rolling']:
            strategy_deployments = [d for d in recent_deployments if d['strategy'] == strategy]
            if strategy_deployments:
                success_rate = len([d for d in strategy_deployments if d['success']]) / len(strategy_deployments)
                strategy_success_rates[strategy] = success_rate
                
        # Consider deployment characteristics
        characteristics = {
            'size': self._calculate_deployment_size(deployment_spec),
            'complexity': self._calculate_deployment_complexity(deployment_spec),
            'risk_level': self._calculate_risk_level(deployment_spec)
        }
        
        # Make decision based on characteristics and history
        if characteristics['risk_level'] == 'high':
            return 'canary'
        elif characteristics['size'] == 'large':
            return 'blue_green'
        elif strategy_success_rates.get('rolling', 0) > 0.8:
            return 'rolling'
            
        return 'canary'  # Default to safest option

    def _calculate_deployment_size(self, deployment_spec: Dict) -> str:
        """Calculate the size category of a deployment."""
        try:
            replicas = deployment_spec['spec'].get('replicas', 1)
            containers = len(deployment_spec['spec']['template']['spec']['containers'])
            
            size_score = replicas * containers
            
            if size_score > 20:
                return 'large'
            elif size_score > 5:
                return 'medium'
            else:
                return 'small'
                
        except Exception:
            return 'medium'  # Default to medium if calculation fails