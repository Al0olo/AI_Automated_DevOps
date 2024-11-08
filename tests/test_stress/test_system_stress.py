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

class TestSystemStress:
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_concurrent_deployments(self, deployment_manager):
        """Test system under concurrent deployment load."""
        num_concurrent = 20
        deployment_results = []
        
        async def deploy_and_monitor():
            deployment = {
                'metadata': {'name': f'stress-test-{np.random.randint(1000, 9999)}'},
                'spec': {
                    'replicas': 1,
                    'template': {
                        'spec': {
                            'containers': [{
                                'name': 'stress-test',
                                'image': 'nginx:latest'
                            }]
                        }
                    }
                }
            }
            
            try:
                result = await deployment_manager.deploy(deployment)
                return {'success': True, 'result': result}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Execute concurrent deployments
        tasks = [deploy_and_monitor() for _ in range(num_concurrent)]
        deployment_results = await asyncio.gather(*tasks)
        
        # Analyze results
        success_rate = len([r for r in deployment_results if r['success']]) / num_concurrent
        assert success_rate >= 0.95  # 95% success rate required
        
        return {
            'total_deployments': num_concurrent,
            'success_rate': success_rate,
            'results': deployment_results
        }

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_memory_stress(self, anomaly_detector):
        """Test system under memory stress conditions."""
        initial_memory = psutil.Process().memory_info().rss
        max_memory_usage = 0
        
        try:
            # Generate large metric sets
            large_metrics = [
                {f'metric_{i}': np.random.random() 
                 for i in range(1000)}
                for _ in range(10000)
            ]
            
            # Process metrics while monitoring memory
            for metrics in large_metrics:
                await anomaly_detector.detect_anomalies(metrics)
                current_memory = psutil.Process().memory_info().rss
                max_memory_usage = max(max_memory_usage, current_memory - initial_memory)
                
                # Check memory usage
                memory_mb = max_memory_usage / (1024 * 1024)
                assert memory_mb < 1024  # Max 1GB memory usage
                
        except Exception as e:
            pytest.fail(f"Memory stress test failed: {str(e)}")
            
        return {
            'initial_memory_mb': initial_memory / (1024 * 1024),
            'max_memory_usage_mb': max_memory_usage / (1024 * 1024),
            'memory_increase_mb': (max_memory_usage - initial_memory) / (1024 * 1024)
        }

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_cpu_stress(self, security_scanner):
        """Test system under CPU stress conditions."""
        cpu_usage_samples = []
        
        async def cpu_intensive_scan():
            # Perform intensive security scan
            return await security_scanner.scan_infrastructure()
        
        # Run multiple scans concurrently
        num_scans = psutil.cpu_count() * 2  # 2x number of CPU cores
        
        start_time = time.time()
        tasks = [cpu_intensive_scan() for _ in range(num_scans)]
        
        # Monitor CPU usage during scans
        async def monitor_cpu():
            while time.time() - start_time < 60:  # Monitor for 60 seconds
                cpu_usage_samples.append(psutil.cpu_percent(interval=1))
                await asyncio.sleep(1)
        
        # Run scans and monitoring
        monitor_task = asyncio.create_task(monitor_cpu())
        scan_results = await asyncio.gather(*tasks)
        await monitor_task
        
        # Analyze CPU usage
        avg_cpu_usage = statistics.mean(cpu_usage_samples)
        max_cpu_usage = max(cpu_usage_samples)
        
        return {
            'average_cpu_usage': avg_cpu_usage,
            'max_cpu_usage': max_cpu_usage,
            'num_scans_completed': len(scan_results),
            'scan_success_rate': len([r for r in scan_results if r]) / num_scans
        }