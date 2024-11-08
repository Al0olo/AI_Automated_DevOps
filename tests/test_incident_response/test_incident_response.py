import pytest
from src.incident_response.ai_incident_classifier import AIIncidentClassifier

class TestAIIncidentClassifier:
    @pytest.fixture
    def incident_classifier(self, test_config):
        return AIIncidentClassifier(test_config['incident_response'])
    
    @pytest.mark.asyncio
    async def test_classify_incident(self, incident_classifier, sample_metrics):
        """Test incident classification."""
        incident_data = {
            'metrics': sample_metrics,
            'error_logs': ['Connection timeout', 'Memory exceeded'],
            'affected_users': 100
        }
        
        classification = await incident_classifier.classify_incident(incident_data)
        assert 'classification' in classification
        assert 'severity' in classification
        assert 'response_plan' in classification
    
    def test_determine_severity(self, incident_classifier):
        """Test severity determination."""
        test_cases = [
            ({'error_rate': 10, 'affected_users': 1000}, 'critical'),
            ({'error_rate': 5, 'affected_users': 100}, 'high'),
            ({'error_rate': 1, 'affected_users': 10}, 'medium'),
            ({'error_rate': 0.1, 'affected_users': 1}, 'low')
        ]
        
        for incident_data, expected_severity in test_cases:
            severity = incident_classifier._determine_severity(
                {'metrics': incident_data}, {'type': 'error', 'confidence': 0.9}
            )
            assert severity == expected_severity