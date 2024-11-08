from typing import Dict, List, Optional
import psutil
import requests
import docker
from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway
from kubernetes import client, config

class MetricCollector:
    def __init__(self, config: Dict):
        """
        Initialize the Metric Collector.
        
        Args:
            config: Configuration dictionary containing:
                - collection_interval: int (seconds)
                - metrics_to_collect: List[str]
                - prometheus_gateway: str
        """
        self.config = config
        self.registry = CollectorRegistry()
        self.metrics = self._initialize_metrics()
        self.docker_client = docker.from_env()
        
        # Initialize Kubernetes client if available
        try:
            config.load_incluster_config()
            self.k8s_client = client.CoreV1Api()
        except:
            self.k8s_client = None
            
    def _initialize_metrics(self) -> Dict:
        """Initialize Prometheus metrics."""
        metrics = {}
        
        # System metrics
        metrics['cpu_usage'] = Gauge('cpu_usage_percent', 
                                   'CPU Usage Percentage', 
                                   registry=self.registry)
        metrics['memory_usage'] = Gauge('memory_usage_percent', 
                                      'Memory Usage Percentage', 
                                      registry=self.registry)
        metrics['disk_usage'] = Gauge('disk_usage_percent', 
                                    'Disk Usage Percentage', 
                                    registry=self.registry)
        
        # Application metrics
        metrics['request_count'] = Counter('request_total', 
                                         'Total Request Count', 
                                         registry=self.registry)
        metrics['error_count'] = Counter('error_total', 
                                       'Total Error Count', 
                                       registry=self.registry)
        metrics['response_time'] = Gauge('response_time_seconds', 
                                       'Response Time in Seconds', 
                                       registry=self.registry)
        
        return metrics
    
    async def collect_metrics(self) -> Dict[str, float]:
        """Collect all configured metrics."""
        metrics_data = {}
        
        # Collect system metrics
        metrics_data.update(self._collect_system_metrics())
        
        # Collect Docker metrics if configured
        if 'docker' in self.config['metrics_to_collect']:
            metrics_data.update(self._collect_docker_metrics())
            
        # Collect Kubernetes metrics if available
        if self.k8s_client and 'kubernetes' in self.config['metrics_to_collect']:
            metrics_data.update(await self._collect_kubernetes_metrics())
            
        # Collect application metrics
        metrics_data.update(self._collect_application_metrics())
        
        # Update Prometheus metrics
        self._update_prometheus_metrics(metrics_data)
        
        return metrics_data
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics."""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'system_load': psutil.getloadavg()[0],
            'network_io_bytes_sent': psutil.net_io_counters().bytes_sent,
            'network_io_bytes_recv': psutil.net_io_counters().bytes_recv
        }
    
    def _collect_docker_metrics(self) -> Dict[str, float]:
        """Collect Docker-related metrics."""
        metrics = {}
        try:
            for container in self.docker_client.containers.list():
                stats = container.stats(stream=False)
                container_name = container.name
                
                # Calculate CPU usage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                             stats['precpu_stats']['system_cpu_usage']
                cpu_usage = (cpu_delta / system_delta) * 100
                
                metrics[f'container_{container_name}_cpu'] = cpu_usage
                metrics[f'container_{container_name}_memory'] = \
                    stats['memory_stats']['usage'] / stats['memory_stats']['limit'] * 100
                    
        except Exception as e:
            print(f"Error collecting Docker metrics: {str(e)}")
            
        return metrics
    
    async def _collect_kubernetes_metrics(self) -> Dict[str, float]:
        """Collect Kubernetes-related metrics."""
        metrics = {}
        try:
            nodes = self.k8s_client.list_node()
            pods = self.k8s_client.list_pod_for_all_namespaces()
            
            # Node metrics
            for node in nodes.items:
                node_name = node.metadata.name
                conditions = {cond.type: cond.status for cond in node.status.conditions}
                metrics[f'node_{node_name}_ready'] = 1 if conditions.get('Ready') == 'True' else 0
                
            # Pod metrics
            running_pods = 0
            failed_pods = 0
            pending_pods = 0
            
            for pod in pods.items:
                if pod.status.phase == 'Running':
                    running_pods += 1
                elif pod.status.phase == 'Failed':
                    failed_pods += 1
                elif pod.status.phase == 'Pending':
                    pending_pods += 1
                    
            metrics.update({
                'k8s_pods_running': running_pods,
                'k8s_pods_failed': failed_pods,
                'k8s_pods_pending': pending_pods
            })
            
        except Exception as e:
            print(f"Error collecting Kubernetes metrics: {str(e)}")
            
        return metrics
    
    def _collect_application_metrics(self) -> Dict[str, float]:
        """Collect application-specific metrics."""
        metrics = {}
        
        # Example application metrics collection
        try:
            if 'app_endpoint' in self.config:
                response = requests.get(f"{self.config['app_endpoint']}/metrics")
                if response.status_code == 200:
                    metrics.update(response.json())
        except Exception as e:
            print(f"Error collecting application metrics: {str(e)}")
            
        return metrics
    
    def _update_prometheus_metrics(self, metrics_data: Dict[str, float]):
        """Update Prometheus metrics with collected data."""
        for metric_name, value in metrics_data.items():
            if metric_name in self.metrics:
                if isinstance(self.metrics[metric_name], Counter):
                    self.metrics[metric_name].inc(value)
                else:
                    self.metrics[metric_name].set(value)
                    
        # Push to Prometheus gateway if configured
        if 'prometheus_gateway' in self.config:
            try:
                push_to_gateway(
                    self.config['prometheus_gateway'],
                    job='metric_collector',
                    registry=self.registry
                )
            except Exception as e:
                print(f"Error pushing to Prometheus gateway: {str(e)}")