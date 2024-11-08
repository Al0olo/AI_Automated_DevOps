import pytest
from src.deployment.ai_deployment_manager import AIDeploymentManager
from src.monitoring.ai_anomaly_detector import AIAnomalyDetector
from src.security.ai_security_scanner import AISecurityScanner
from src.incident_response.ai_incident_classifier import AIIncidentClassifier

class TestFullPipeline:
    @pytest.fixture
    def pipeline_components(self, test_config, mock_k8s_client):
        return {
            'deployment': AIDeploymentManager(test_config['deployment']),
            'monitoring': AIAnomalyDetector(test_config['monitoring']),
            'security': AISecurityScanner(test_config['security']),
            'incident': AIIncidentClassifier(test_config['incident_response'])
        }
    
    @pytest.mark.asyncio
    async def test_deployment_to_monitoring(self, pipeline_components, sample_deployment):
        """Test deployment followed by monitoring."""
        # Deploy
        deploy_result = await pipeline_components['deployment'].deploy(sample_deployment)
        assert deploy_result['status'] == 'success'
        
        # Monitor
        metrics = {
            'cpu_usage': 65.0,
            'memory_usage': 70.0,
            'error_rate': 0.1
        }
        
        anomalies = await pipeline_components['monitoring'].detect_anomalies(metrics)
        assert isinstance(anomalies, list)
    
    @pytest.mark.asyncio
    async def test_security_incident_response(self, pipeline_components):
        """Test security scan triggering incident response."""
        # Security scan
        scan_results = await pipeline_components['security'].scan_infrastructure()
        assert isinstance(scan_results, dict)
        
        # If vulnerabilities found, classify incident
        if scan_results['vulnerabilities']:
            incident_data = {
                'type': 'security',
                'details': scan_results,
                'metrics': {
                    'severity': 'high',
                    'affected_components': len(scan_results['vulnerabilities'])
                }
            }
            
            classification = await pipeline_components['incident'].classify_incident(
                incident_data
            )
            assert classification['severity'] in ['high', 'critical']