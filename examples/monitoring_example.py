from prometheus_client import start_http_server, Gauge, Counter
from aidevops.monitoring import MetricsCollector

class PrometheusExporter:
    def __init__(self, port=8000):
        self.port = port
        self.metrics = {}
        self.initialize_metrics()
        
    def initialize_metrics(self):
        self.metrics['deployment_duration'] = Gauge(
            'aidevops_deployment_duration_seconds',
            'Time taken for deployments'
        )
        self.metrics['deployment_success'] = Counter(
            'aidevops_deployment_success_total',
            'Number of successful deployments'
        )
        self.metrics['deployment_failure'] = Counter(
            'aidevops_deployment_failure_total',
            'Number of failed deployments'
        )
        
    async def start(self):
        start_http_server(self.port)
        collector = MetricsCollector(load_config())
        
        while True:
            metrics = await collector.collect_metrics()
            self.update_metrics(metrics)
            await asyncio.sleep(15)
            
    def update_metrics(self, metrics):
        for metric_name, value in metrics.items():
            if metric_name in self.metrics:
                if isinstance(self.metrics[metric_name], Gauge):
                    self.metrics[metric_name].set(value)
                elif isinstance(self.metrics[metric_name], Counter):
                    self.metrics[metric_name].inc(value)