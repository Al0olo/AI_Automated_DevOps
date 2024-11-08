from typing import Dict, List
import requests
import json
from datetime import datetime
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging

class AlertManager:
    def __init__(self, config: Dict):
        """
        Initialize the Alert Manager.
        
        Args:
            config: Configuration dictionary containing:
                - alert_channels: Dict of alert channels and their configs
                - alert_rules: Dict of alert rules
                - notification_templates: Dict of notification templates
        """
        self.config = config
        self.alert_history = []
        self.logger = logging.getLogger(__name__)
        
    async def process_anomalies(self, anomalies: List[Dict]):
        """Process detected anomalies and trigger appropriate alerts."""
        for anomaly in anomalies:
            if self._should_alert(anomaly):
                alert = self._create_alert(anomaly)
                await self._send_alerts(alert)
                self.alert_history.append(alert)
                
    def _should_alert(self, anomaly: Dict) -> bool:
        """Determine if an alert should be sent for this anomaly."""
        # Check for alert fatigue
        recent_alerts = [
            alert for alert in self.alert_history
            if alert['metric'] == anomaly['metric'] and
            (datetime.now() - datetime.fromisoformat(alert['timestamp'])).total_seconds() < 
            self.config['alert_cooldown']
        ]
        
        if recent_alerts:
            return False
            
        # Check severity threshold
        severity_levels = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        return severity_levels[anomaly['severity']] >= \
               severity_levels[self.config['minimum_severity']]
    
    def _create_alert(self, anomaly: Dict) -> Dict:
        """Create an alert object from an anomaly."""
        return {
            'id': f"alert-{datetime.now().timestamp()}",
            'metric': anomaly['metric'],
            'value': anomaly['current_value'],
            'severity': anomaly['severity'],
            'confidence': anomaly['confidence'],
            'timestamp': datetime.now().isoformat(),
            'description': self._generate_alert_description(anomaly),
            'actions': anomaly['suggested_actions']
        }
        
    def _generate_alert_description(self, anomaly: Dict) -> str:
        """Generate a detailed alert description."""
        template = self.config['notification_templates'].get(
            anomaly['severity'],
            self.config['notification_templates']['default']
        )
        
        return template
    async def _send_alerts(self, alert: Dict):
        """Send alerts through all configured channels."""
        tasks = []
        
        for channel, config in self.config['alert_channels'].items():
            if self._is_channel_appropriate(channel, alert['severity']):
                tasks.append(self._send_to_channel(channel, config, alert))
                
        await asyncio.gather(*tasks)
    
    def _is_channel_appropriate(self, channel: str, severity: str) -> bool:
        """Determine if the channel is appropriate for the alert severity."""
        channel_config = self.config['alert_channels'][channel]
        return severity in channel_config['severity_levels']
    
    async def _send_to_channel(self, channel: str, config: Dict, alert: Dict):
        """Send alert to specific channel."""
        try:
            if channel == 'email':
                await self._send_email_alert(config, alert)
            elif channel == 'slack':
                await self._send_slack_alert(config, alert)
            elif channel == 'pagerduty':
                await self._send_pagerduty_alert(config, alert)
            elif channel == 'teams':
                await self._send_teams_alert(config, alert)
            elif channel == 'webhook':
                await self._send_webhook_alert(config, alert)
                
            self.logger.info(f"Alert sent successfully via {channel}")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert via {channel}: {str(e)}")
    
    async def _send_email_alert(self, config: Dict, alert: Dict):
        """Send alert via email."""
        msg = MIMEMultipart()
        msg['From'] = config['sender']
        msg['To'] = ', '.join(config['recipients'])
        msg['Subject'] = f"[{alert['severity'].upper()}] Alert: {alert['metric']}"
        
        body = self._generate_email_body(alert)
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            if config.get('use_tls', True):
                server.starttls()
            if 'username' in config:
                server.login(config['username'], config['password'])
            server.send_message(msg)
    
    def _generate_email_body(self, alert: Dict) -> str:
        """Generate HTML email body for alert."""
        return f"""
        <html>
            <body>
                <h2>Alert Details</h2>
                <p><strong>Metric:</strong> {alert['metric']}</p>
                <p><strong>Value:</strong> {alert['value']}</p>
                <p><strong>Severity:</strong> {alert['severity']}</p>
                <p><strong>Confidence:</strong> {alert['confidence']}%</p>
                <p><strong>Time:</strong> {alert['timestamp']}</p>
                
                <h3>Description</h3>
                <p>{alert['description']}</p>
                
                <h3>Suggested Actions</h3>
                <ul>
                    {''.join(f'<li>{action}</li>' for action in alert['actions'])}
                </ul>
            </body>
        </html>
        """
    
    async def _send_slack_alert(self, config: Dict, alert: Dict):
        """Send alert via Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {alert['severity'].upper()} Alert: {alert['metric']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Metric:*\n{alert['metric']}"},
                    {"type": "mrkdwn", "text": f"*Value:*\n{alert['value']}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{alert['severity']}"},
                    {"type": "mrkdwn", "text": f"*Confidence:*\n{alert['confidence']}%"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{alert['description']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Suggested Actions:*\n" + "\n".join(f"• {action}" for action in alert['actions'])
                }
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            await session.post(config['webhook_url'], json={"blocks": blocks})
    
    async def _send_pagerduty_alert(self, config: Dict, alert: Dict):
        """Send alert via PagerDuty."""
        payload = {
            "routing_key": config['routing_key'],
            "event_action": "trigger",
            "payload": {
                "summary": f"{alert['severity'].upper()} Alert: {alert['metric']}",
                "severity": alert['severity'],
                "source": "AI Monitoring System",
                "custom_details": {
                    "metric": alert['metric'],
                    "value": alert['value'],
                    "confidence": alert['confidence'],
                    "description": alert['description'],
                    "suggested_actions": alert['actions']
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post("https://events.pagerduty.com/v2/enqueue", 
                             json=payload,
                             headers={"Content-Type": "application/json"})
    
    def _update_alert_status(self, alert_id: str, status: str):
        """Update the status of an existing alert."""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['status'] = status
                alert['updated_at'] = datetime.now().isoformat()
                break
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts."""
        return [
            alert for alert in self.alert_history
            if alert.get('status') != 'resolved'
        ]
    
    def resolve_alert(self, alert_id: str, resolution_note: str = None):
        """Mark an alert as resolved."""
        self._update_alert_status(alert_id, 'resolved')
        
        if resolution_note:
            for alert in self.alert_history:
                if alert['id'] == alert_id:
                    alert['resolution_note'] = resolution_note
                    alert['resolved_at'] = datetime.now().isoformat()
                    break