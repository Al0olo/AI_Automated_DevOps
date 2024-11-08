import plotly.graph_objects as go
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta

class DashboardGenerator:
    def __init__(self, config: Dict):
        """Initialize the Dashboard Generator."""
        self.config = config
        self.metrics_history = {}
        
    def update_metrics(self, metrics: Dict[str, float]):
        """Update metrics history with new data."""
        current_time = datetime.now()
        
        for metric_name, value in metrics.items():
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []
                
            self.metrics_history[metric_name].append({
                'timestamp': current_time,
                'value': value
            })
            
            # Keep only last 24 hours of data
            cutoff_time = current_time - timedelta(hours=24)
            self.metrics_history[metric_name] = [
                point for point in self.metrics_history[metric_name]
                if point['timestamp'] > cutoff_time
            ]
    
    def generate_dashboard(self) -> Dict:
        """Generate dashboard with various visualizations."""
        return {
            'system_health': self._generate_system_health_card(),
            'metrics_trends': self._generate_metrics_trends(),
            'alerts_summary': self._generate_alerts_summary(),
            'resource_usage': self._generate_resource_usage_graphs()
        }
    
    def _generate_system_health_card(self) -> Dict:
        """Generate system health status card."""
        current_metrics = {
            metric: history[-1]['value'] 
            for metric, history in self.metrics_history.items()
            if history
        }
        
        health_score = self._calculate_health_score(current_metrics)
        
        return {
            'score': health_score,
            'status': self._get_health_status(health_score),
            'metrics': current_metrics
        }
    
    def _calculate_health_score(self, current_metrics: Dict[str, float]) -> float:
        """Calculate overall system health score."""
        weights = self.config.get('metric_weights', {
            'cpu_usage': 0.3,
            'memory_usage': 0.3,
            'error_rate': 0.2,
            'response_time': 0.2
        })
        
        score = 100  # Start with perfect score
        
        for metric, value in current_metrics.items():
            if metric not in weights:
                continue
                
            weight = weights[metric]
            
            # Calculate penalty based on metric type
            if metric in ['cpu_usage', 'memory_usage']:
                if value > 90:
                    penalty = weight * 100
                elif value > 80:
                    penalty = weight * 50
                elif value > 70:
                    penalty = weight * 25
                else:
                    penalty = 0
            elif metric == 'error_rate':
                if value > 5:
                    penalty = weight * 100
                elif value > 1:
                    penalty = weight * 50
                elif value > 0.1:
                    penalty = weight * 25
                else:
                    penalty = 0
            elif metric == 'response_time':
                if value > 2000:  # ms
                    penalty = weight * 100
                elif value > 1000:
                    penalty = weight * 50
                elif value > 500:
                    penalty = weight * 25
                else:
                    penalty = 0
                    
            score -= penalty
            
        return max(0, min(100, score))
    
    def _get_health_status(self, health_score: float) -> str:
        """Convert health score to status string."""
        if health_score >= 90:
            return 'Excellent'
        elif health_score >= 75:
            return 'Good'
        elif health_score >= 60:
            return 'Fair'
        elif health_score >= 40:
            return 'Poor'
        else:
            return 'Critical'
    
    def _generate_metrics_trends(self) -> Dict:
        """Generate trend graphs for key metrics."""
        trends = {}
        
        for metric_name, history in self.metrics_history.items():
            if not history:
                continue
                
            # Convert to pandas DataFrame for easier manipulation
            df = pd.DataFrame(history)
            
            # Calculate basic statistics
            stats = {
                'current': history[-1]['value'],
                'mean': df['value'].mean(),
                'min': df['value'].min(),
                'max': df['value'].max(),
                'std': df['value'].std()
            }
            
            # Calculate trend
            if len(history) >= 2:
                current = history[-1]['value']
                previous = history[-2]['value']
                stats['trend'] = {
                    'direction': 'up' if current > previous else 'down',
                    'change_pct': ((current - previous) / previous) * 100
                }
            
            # Generate trend line
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[point['timestamp'] for point in history],
                y=[point['value'] for point in history],
                mode='lines+markers',
                name=metric_name,
                line=dict(width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title=f'{metric_name} Trend',
                xaxis_title='Time',
                yaxis_title='Value',
                template='plotly_white'
            )
            
            trends[metric_name] = {
                'stats': stats,
                'graph': fig.to_json()
            }
            
        return trends
    
    def _generate_alerts_summary(self) -> Dict:
        """Generate summary of recent alerts."""
        alerts = self.metrics_history.get('alerts', [])
        if not alerts:
            return {'count': 0, 'by_severity': {}, 'recent': []}
            
        recent_alerts = alerts[-10:]  # Last 10 alerts
        
        severity_counts = {}
        for alert in alerts:
            severity = alert.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        return {
            'count': len(alerts),
            'by_severity': severity_counts,
            'recent': recent_alerts
        }
    
    def _generate_resource_usage_graphs(self) -> Dict:
        """Generate detailed resource usage visualizations."""
        resources = {}
        
        # CPU Usage Over Time
        if 'cpu_usage' in self.metrics_history:
            cpu_data = self.metrics_history['cpu_usage']
            fig_cpu = go.Figure()
            
            fig_cpu.add_trace(go.Scatter(
                x=[point['timestamp'] for point in cpu_data],
                y=[point['value'] for point in cpu_data],
                fill='tozeroy',
                name='CPU Usage'
            ))
            
            fig_cpu.add_shape(
                type="line",
                x0=cpu_data[0]['timestamp'],
                y0=80,
                x1=cpu_data[-1]['timestamp'],
                y1=80,
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            fig_cpu.update_layout(
                title='CPU Usage Trend',
                yaxis_title='Usage %',
                showlegend=False,
                template='plotly_white'
            )
            
            resources['cpu'] = fig_cpu.to_json()
        
        # Memory Usage Distribution
        if 'memory_usage' in self.metrics_history:
            memory_data = self.metrics_history['memory_usage']
            fig_memory = go.Figure()
            
            fig_memory.add_trace(go.Histogram(
                x=[point['value'] for point in memory_data],
                nbinsx=20,
                name='Memory Distribution'
            ))
            
            fig_memory.update_layout(
                title='Memory Usage Distribution',
                xaxis_title='Usage %',
                yaxis_title='Frequency',
                showlegend=False,
                template='plotly_white'
            )
            
            resources['memory'] = fig_memory.to_json()
        
        # Disk I/O
        if all(metric in self.metrics_history for metric in ['disk_read', 'disk_write']):
            fig_disk = go.Figure()
            
            fig_disk.add_trace(go.Scatter(
                x=[point['timestamp'] for point in self.metrics_history['disk_read']],
                y=[point['value'] for point in self.metrics_history['disk_read']],
                name='Read'
            ))
            
            fig_disk.add_trace(go.Scatter(
                x=[point['timestamp'] for point in self.metrics_history['disk_write']],
                y=[point['value'] for point in self.metrics_history['disk_write']],
                name='Write'
            ))
            
            fig_disk.update_layout(
                title='Disk I/O Activity',
                yaxis_title='Bytes/sec',
                template='plotly_white'
            )
            
            resources['disk_io'] = fig_disk.to_json()
        
        return resources
    
    def generate_pdf_report(self, output_path: str):
        """Generate a PDF report of the dashboard."""
        dashboard_data = self.generate_dashboard()
        
        # Create PDF using reportlab
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        story.append(Paragraph("System Monitoring Report", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Add system health summary
        health_data = dashboard_data['system_health']
        story.append(Paragraph(f"System Health: {health_data['status']}", styles['Heading1']))
        story.append(Paragraph(f"Health Score: {health_data['score']:.1f}%", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add metric trends
        story.append(Paragraph("Metric Trends", styles['Heading1']))
        for metric, trend in dashboard_data['metrics_trends'].items():
            story.append(Paragraph(metric, styles['Heading2']))
            stats = trend['stats']
            data = [
                ['Metric', 'Value'],
                ['Current', f"{stats['current']:.2f}"],
                ['Average', f"{stats['mean']:.2f}"],
                ['Min', f"{stats['min']:.2f}"],
                ['Max', f"{stats['max']:.2f}"]
            ]
            story.append(Table(data))
            story.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(story)