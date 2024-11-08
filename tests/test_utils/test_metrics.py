def test_metric_calculation():
    """Test utility functions for metric calculations."""
    test_metrics = [
        {'cpu': 50, 'memory': 60},
        {'cpu': 60, 'memory': 70},
        {'cpu': 70, 'memory': 80}
    ]
    
    # Calculate average
    avg_cpu = sum(m['cpu'] for m in test_metrics) / len(test_metrics)
    assert avg_cpu == 60
    
    # Calculate trend
    cpu_trend = test_metrics[-1]['cpu'] - test_metrics[0]['cpu']
    assert cpu_trend == 20

def test_data_transformation():
    """Test data transformation utilities."""
    raw_data = {
        'timestamp': '2024-01-01T00:00:00',
        'metrics': {'cpu': 50, 'memory': 60}
    }
    
    # Transform to time series
    ts_data = pd.DataFrame([raw_data['metrics']], 
                          index=[pd.Timestamp(raw_data['timestamp'])])
    assert not ts_data.empty
    assert 'cpu' in ts_data.columns