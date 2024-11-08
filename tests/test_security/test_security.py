import pytest
from src.security.ai_security_scanner import AISecurityScanner

class TestAISecurityScanner:
    @pytest.fixture
    def security_scanner(self, test_config):
        return AISecurityScanner(test_config['security'])
    
    @pytest.mark.asyncio
    async def test_scan_infrastructure(self, security_scanner):
        """Test infrastructure security scanning."""
        results = await security_scanner.scan_infrastructure()
        assert 'vulnerabilities' in results
        assert 'misconfigurations' in results
        assert 'recommendations' in results
    
    @pytest.mark.asyncio
    async def test_kubernetes_security(self, security_scanner, mock_k8s_client):
        """Test Kubernetes security scanning."""
        results = await security_scanner._scan_kubernetes_security()
        assert isinstance(results, dict)
        assert 'vulnerabilities' in results
        assert 'misconfigurations' in results
