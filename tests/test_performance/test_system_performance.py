import pytest
import time
import asyncio
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil
import statistics
from locust import HttpUser, task, between
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import resource

class TestSystemPerformance:
    @pytest.fixture
    def performance_metrics(self):
        """Initialize performance metrics collection."""
        registry = CollectorRegistry()
        metrics = {
            'response_time': Gauge('response_time_seconds', 
                                 'Response time in seconds', 
                                 registry=registry),
            'memory_usage': Gauge('memory_usage_bytes', 
                                'Memory usage in bytes', 
                                registry=registry),
            'cpu_usage': Gauge('cpu_usage_percent', 
                             'CPU usage percentage', 
                             registry=registry)
        }
        return metrics, registry

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_deployment_performance(self, deployment_manager, sample_deployment):
        """Test deployment performance under normal conditions."""
        metrics = []
        memory_usage = []
        cpu_usage = []
        
        # Perform multiple deployments and measure performance
        for _ in range(10):
            start_memory = psutil.Process().memory_info().rss
            start_cpu = psutil.cpu_percent()
            start_time = time.time()
            
            # Execute deployment
            result = await deployment_manager.deploy(sample_deployment)
            
            # Collect metrics
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            end_cpu = psutil.cpu_percent()
            
            metrics.append(end_time - start_time)
            memory_usage.append(end_memory - start_memory)
            cpu_usage.append(end_cpu - start_cpu)
            
            # Allow system to stabilize
            await asyncio.sleep(1)
        
        # Calculate performance statistics
        performance_stats = {
            'avg_deployment_time': statistics.mean(metrics),
            'max_deployment_time': max(metrics),
            'min_deployment_time': min(metrics),
            'std_deployment_time': statistics.stdev(metrics),
            'avg_memory_usage': statistics.mean(memory_usage),
            'avg_cpu_usage': statistics.mean(cpu_usage)
        }
        
        # Assert performance requirements
        assert performance_stats['avg_deployment_time'] < 5.0  # Max 5 seconds
        assert performance_stats['max_deployment_time'] < 10.0  # Max 10 seconds
        assert performance_stats['avg_memory_usage'] < 500 * 1024 * 1024  # Max 500MB
        
        return performance_stats

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_monitoring_performance(self, anomaly_detector, sample_metrics):
        """Test monitoring system performance with large metric sets."""
        async def generate_metric_batch(size):
            return [
                {k: v + np.random.normal(0, 1) for k, v in sample_metrics.items()}
                for _ in range(size)
            ]
        
        batch_sizes = [100, 1000, 10000]
        performance_results = {}
        
        for size in batch_sizes:
            metrics_batch = await generate_metric_batch(size)
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            # Process metrics batch
            anomalies = []
            for metrics in metrics_batch:
                batch_anomalies = await anomaly_detector.detect_anomalies(metrics)
                anomalies.extend(batch_anomalies)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            performance_results[size] = {
                'processing_time': end_time - start_time,
                'memory_usage': end_memory - start_memory,
                'anomalies_detected': len(anomalies)
            }
            
            # Assert performance requirements
            assert performance_results[size]['processing_time'] / size < 0.01  # Max 10ms per metric
            
        return performance_results