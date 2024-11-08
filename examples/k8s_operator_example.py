from kubernetes import client, config, watch
from aidevops.deployment import AIDeploymentManager

class AIDevOpsOperator:
    def __init__(self):
        config.load_incluster_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.deployment_manager = AIDeploymentManager(load_config())
    
    async def watch_deployments(self):
        w = watch.Watch()
        for event in w.stream(self.apps_v1.list_deployment_for_all_namespaces):
            deployment = event['object']
            if self._should_manage(deployment):
                await self._handle_deployment(deployment)
    
    def _should_manage(self, deployment):
        return deployment.metadata.annotations.get(
            'aidevops.com/managed'
        ) == 'true'
    
    async def _handle_deployment(self, deployment):
        try:
            result = await self.deployment_manager.optimize_deployment(deployment)
            if result['changes_recommended']:
                await self._apply_recommendations(deployment, result['recommendations'])
        except Exception as e:
            print(f"Error handling deployment: {str(e)}")

if __name__ == "__main__":
    operator = AIDevOpsOperator()
    asyncio.run(operator.watch_deployments())