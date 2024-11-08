from aidevops.security import AISecurityScanner
from aidevops.reporting import SecurityReporter

async def run_security_scan():
    config = load_config('config/config.yaml')
    scanner = AISecurityScanner(config)
    reporter = SecurityReporter(config)
    
    # Configure scan
    scan_config = {
        'scope': ['vulnerabilities', 'compliance', 'configuration'],
        'targets': ['production-cluster'],
        'ignore_patterns': ['CVE-2023-*'],
        'compliance_standards': ['PCI-DSS', 'HIPAA']
    }
    
    # Run scan
    results = await scanner.scan(scan_config)
    
    # Generate report
    report = await reporter.generate_report(results)
    
    # Handle critical findings
    if report['critical_findings']:
        await handle_critical_findings(report['critical_findings'])
    
    return report

async def handle_critical_findings(findings):
    alert_manager = AlertManager(config)
    for finding in findings:
        await alert_manager.create_alert({
            'title': f"Critical Security Finding: {finding['title']}",
            'severity': 'critical',
            'description': finding['description'],
            'remediation': finding['remediation']
        })