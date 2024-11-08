import pytest
import yaml
import os
import json
from unittest.mock import Mock, patch
from kubernetes import client, config
import pandas as pd
import numpy as np

@pytest.fixture
def mock_k8s_client():
    """Mock Kubernetes client for testing."""
    with patch('kubernetes.client.CoreV1Api') as mock_core_api:
        with patch('kubernetes.client.AppsV1Api') as mock_apps_api:
            yield {
                'core': mock_core_api(),
                'apps': mock_apps_api()
            }

@pytest.fixture
def test_config():
    """Load test configuration."""
    with open('tests/test_config.yml', 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_metrics():
    """Generate sample metrics data."""
    return {
        'cpu_usage': 45.5,
        'memory_usage': 62.3,
        'disk_usage': 78.1,
        'network_io': 150.4,
        'error_rate': 0.05,
        'response_time': 250
    }

@pytest.fixture
def sample_deployment():
    """Generate sample deployment specification."""
    return {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {
            'name': 'test-deployment',
            'namespace': 'default'
        },
        'spec': {
            'replicas': 3,
            'selector': {
                'matchLabels': {
                    'app': 'test'
                }
            },
            'template': {
                'metadata': {
                    'labels': {
                        'app': 'test'
                    }
                },
                'spec': {
                    'containers': [{
                        'name': 'test-container',
                        'image': 'test-image:latest',
                        'resources': {
                            'requests': {
                                'cpu': '100m',
                                'memory': '128Mi'
                            },
                            'limits': {
                                'cpu': '200m',
                                'memory': '256Mi'
                            }
                        }
                    }]
                }
            }
        }
    }