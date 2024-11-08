from aidevops.incident import AIIncidentManager
from aidevops.remediation import RemediationEngine

async def handle_incident(incident_data):
    config = load_config('config/config.yaml')
    incident_manager = AIIncidentManager(config)
    remediation_engine = RemediationEngine(config)
    
    # Classify incident
    classification = await incident_manager.classify_incident(incident_data)
    
    # Generate response plan
    response_plan = await incident_manager.generate_response_plan(classification)
    
    # Execute automated remediation
    if response_plan['auto_remediation_possible']:
        try:
            result = await remediation_engine.execute_plan(response_plan)
            if result['success']:
                await incident_manager.resolve_incident(
                    incident_data['id'],
                    resolution=result['resolution']
                )
            else:
                await incident_manager.escalate_incident(
                    incident_data['id'],
                    reason=result['failure_reason']
                )
        except Exception as e:
            await incident_manager.escalate_incident(
                incident_data['id'],
                reason=str(e)
            )
    else:
        await incident_manager.assign_to_team(
            incident_data['id'],
            team=response_plan['recommended_team']
        )