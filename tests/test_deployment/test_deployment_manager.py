import pytest
from src.deployment.ai_deployment_manager import AIDeploymentManager

class TestAIDeploymentManager:
    @pytest.fixture
    def deployment_manager(self, test_config, mock_k8s_client):
        manager = AIDeploymentManager(test_config['deployment'])
        manager.k8s_client = mock_k8s_client
        return manager
    
    @pytest.mark.asyncio
    async def test_deploy(self, deployment_manager, sample_deployment):
        """Test deployment process."""
        result = await deployment_manager.deploy(sample_deployment)
        assert result['status'] == 'success'
        assert 'metrics' in result
        assert 'analysis' in result
    
    @pytest.mark.asyncio
    async def test_rollback(self, deployment_manager, sample_deployment):
        """Test rollback functionality."""
        # Simulate failed deployment
        with patch.object(deployment_manager, '_execute_deployment', 
                         side_effect=Exception('Deployment failed')):
            result = await deployment_manager.deploy(sample_deployment)
            assert result['status'] == 'failed'
            assert 'rollback_status' in result
    
    def test_determine_strategy(self, deployment_manager, sample_deployment):
        """Test deployment strategy determination."""
        strategy = deployment_manager._determine_deployment_strategy(sample_deployment)
        assert strategy in ['canary', 'blue_green', 'rolling']