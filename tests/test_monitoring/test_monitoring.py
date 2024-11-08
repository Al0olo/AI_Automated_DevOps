import pytest
from src.monitoring.ai_anomaly_detector import AIAnomalyDetector

class TestAIAnomalyDetector:
    @pytest.fixture
    def anomaly_detector(self, test_config):
        return AIAnomalyDetector(test_config['monitoring'])
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, anomaly_detector, sample_metrics):
        """Test anomaly detection with sample metrics."""
        # Test normal metrics
        anomalies = await anomaly_detector.detect_anomalies(sample_metrics)
        assert len(anomalies) == 0
        
        # Test anomalous metrics
        anomalous_metrics = sample_metrics.copy()
        anomalous_metrics['cpu_usage'] = 95.0
        anomalous_metrics['error_rate'] = 5.0
        
        anomalies = await anomaly_detector.detect_anomalies(anomalous_metrics)
        assert len(anomalies) > 0
        assert any(a['metric'] == 'cpu_usage' for a in anomalies)
        assert any(a['metric'] == 'error_rate' for a in anomalies)
    
    def test_calculate_severity(self, anomaly_detector):
        """Test severity calculation."""
        test_cases = [
            (95.0, 'critical'),
            (85.0, 'high'),
            (75.0, 'medium'),
            (50.0, 'low')
        ]
        
        for value, expected_severity in test_cases:
            severity = anomaly_detector._calculate_severity(value)
            assert severity == expected_severity
