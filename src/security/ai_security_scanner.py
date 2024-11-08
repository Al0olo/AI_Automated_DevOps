from typing import Dict, List, Optional
import tensorflow as tf
import numpy as np
from datetime import datetime
import logging
import yaml
import json
import aiohttp
import asyncio
from sklearn.ensemble import IsolationForest
from cryptography.fernet import Fernet
import re

class AISecurityScanner:
    def __init__(self, config: Dict):
        """
        Initialize the AI Security Scanner.
        
        Args:
            config: Configuration dictionary containing:
                - scan_rules: Security scanning rules
                - vulnerability_db: Path to vulnerability database
                - api_endpoints: Security API endpoints
                - ml_model_config: ML model configurations
                - alert_thresholds: Alert threshold configurations
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.anomaly_detector = IsolationForest(
            contamination=config.get('anomaly_threshold', 0.1)
        )
        self.scan_history = []
        self._load_vulnerability_database()
        self._initialize_ml_models()
        
    async def scan_infrastructure(self) -> Dict:
        """
        Perform comprehensive security scan of infrastructure.
        
        Returns:
            Dictionary containing scan results and recommendations
        """
        try:
            scan_results = {
                'timestamp': datetime.now().isoformat(),
                'vulnerabilities': [],
                'misconfigurations': [],
                'threats': [],
                'compliance_issues': [],
                'recommendations': [],
                'risk_score': 0.0
            }
            
            # Parallel security scans
            scan_tasks = [
                self._scan_kubernetes_security(),
                self._scan_network_security(),
                self._scan_application_security(),
                self._scan_data_security(),
                self._check_compliance()
            ]
            
            results = await asyncio.gather(*scan_tasks)
            
            # Combine results
            for result in results:
                scan_results['vulnerabilities'].extend(result.get('vulnerabilities', []))
                scan_results['misconfigurations'].extend(result.get('misconfigurations', []))
                scan_results['threats'].extend(result.get('threats', []))
                scan_results['compliance_issues'].extend(result.get('compliance_issues', []))
            
            # AI-driven analysis
            analysis = await self._analyze_scan_results(scan_results)
            scan_results['risk_score'] = analysis['risk_score']
            scan_results['recommendations'] = analysis['recommendations']
            
            # Update scan history
            self._update_scan_history(scan_results)
            
            return scan_results
            
        except Exception as e:
            self.logger.error(f"Security scan failed: {str(e)}")
            return self._generate_error_report(str(e))
    
    async def _scan_kubernetes_security(self) -> Dict:
        """Scan Kubernetes cluster for security issues."""
        k8s_results = {
            'vulnerabilities': [],
            'misconfigurations': [],
            'threats': []
        }
        
        try:
            # Scan Pod Security Policies
            psp_issues = await self._check_pod_security_policies()
            k8s_results['misconfigurations'].extend(psp_issues)
            
            # Scan RBAC configurations
            rbac_issues = await self._check_rbac_configurations()
            k8s_results['misconfigurations'].extend(rbac_issues)
            
            # Scan Network Policies
            network_issues = await self._check_network_policies()
            k8s_results['vulnerabilities'].extend(network_issues)
            
            # Scan Secrets
            secret_issues = await self._check_secrets_security()
            k8s_results['vulnerabilities'].extend(secret_issues)
            
            # Scan Container Security
            container_issues = await self._check_container_security()
            k8s_results['vulnerabilities'].extend(container_issues)
            
            return k8s_results
            
        except Exception as e:
            self.logger.error(f"Kubernetes security scan failed: {str(e)}")
            return k8s_results
    
    async def _check_pod_security_policies(self) -> List[Dict]:
        """Check Pod Security Policies for misconfigurations."""
        issues = []
        
        try:
            # Get all PSPs
            api = kubernetes.client.PolicyV1beta1Api()
            psps = api.list_pod_security_policy()
            
            for psp in psps.items:
                # Check privileged containers
                if psp.spec.privileged:
                    issues.append({
                        'type': 'psp_misconfiguration',
                        'severity': 'high',
                        'resource': psp.metadata.name,
                        'detail': 'PSP allows privileged containers',
                        'remediation': 'Disable privileged containers in PSP'
                    })
                
                # Check host namespace sharing
                if psp.spec.host_network or psp.spec.host_pid or psp.spec.host_ipc:
                    issues.append({
                        'type': 'psp_misconfiguration',
                        'severity': 'medium',
                        'resource': psp.metadata.name,
                        'detail': 'PSP allows host namespace sharing',
                        'remediation': 'Disable host namespace sharing unless required'
                    })
                
                # Check volume types
                if 'hostPath' in psp.spec.volumes:
                    issues.append({
                        'type': 'psp_misconfiguration',
                        'severity': 'high',
                        'resource': psp.metadata.name,
                        'detail': 'PSP allows hostPath volumes',
                        'remediation': 'Remove hostPath from allowed volume types'
                    })
                    
        except Exception as e:
            self.logger.error(f"PSP check failed: {str(e)}")
            
        return issues
    
    async def _check_container_security(self) -> List[Dict]:
        """Check container security configurations."""
        issues = []
        
        try:
            api = kubernetes.client.CoreV1Api()
            pods = api.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                for container in pod.spec.containers:
                    # Check security context
                    if not container.security_context:
                        issues.append({
                            'type': 'container_security',
                            'severity': 'medium',
                            'resource': f"{pod.metadata.namespace}/{pod.metadata.name}/{container.name}",
                            'detail': 'No security context defined',
                            'remediation': 'Define security context with appropriate settings'
                        })
                    else:
                        # Check privileged mode
                        if container.security_context.privileged:
                            issues.append({
                                'type': 'container_security',
                                'severity': 'high',
                                'resource': f"{pod.metadata.namespace}/{pod.metadata.name}/{container.name}",
                                'detail': 'Container running in privileged mode',
                                'remediation': 'Disable privileged mode unless absolutely necessary'
                            })
                        
                        # Check root user
                        if not container.security_context.run_as_non_root:
                            issues.append({
                                'type': 'container_security',
                                'severity': 'medium',
                                'resource': f"{pod.metadata.namespace}/{pod.metadata.name}/{container.name}",
                                'detail': 'Container may run as root user',
                                'remediation': 'Enable runAsNonRoot'
                            })
                            
                    # Check resource limits
                    if not container.resources or not container.resources.limits:
                        issues.append({
                            'type': 'container_security',
                            'severity': 'low',
                            'resource': f"{pod.metadata.namespace}/{pod.metadata.name}/{container.name}",
                            'detail': 'No resource limits defined',
                            'remediation': 'Define resource limits to prevent DoS'
                        })
                        
        except Exception as e:
            self.logger.error(f"Container security check failed: {str(e)}")
            
        return issues
    
    async def _scan_network_security(self) -> Dict:
        """Scan network security configurations."""
        network_results = {
            'vulnerabilities': [],
            'misconfigurations': [],
            'threats': []
        }
        
        try:
            # Scan Network Policies
            policies = await self._check_network_policies()
            network_results['misconfigurations'].extend(policies)
            
            # Scan Service Configurations
            services = await self._check_service_security()
            network_results['vulnerabilities'].extend(services)
            
            # Scan Ingress Configurations
            ingress = await self._check_ingress_security()
            network_results['vulnerabilities'].extend(ingress)
            
            # Detect Network Anomalies
            anomalies = await self._detect_network_anomalies()
            network_results['threats'].extend(anomalies)
            
            return network_results
            
        except Exception as e:
            self.logger.error(f"Network security scan failed: {str(e)}")
            return network_results
    
    async def _scan_application_security(self) -> Dict:
        """Scan application-level security."""
        app_results = {
            'vulnerabilities': [],
            'misconfigurations': [],
            'threats': []
        }
        
        try:
            # Dependency scanning
            dep_results = await self._scan_dependencies()
            app_results['vulnerabilities'].extend(dep_results)
            
            # API security scanning
            api_results = await self._scan_api_security()
            app_results['vulnerabilities'].extend(api_results)
            
            # Code security scanning
            code_results = await self._scan_code_security()
            app_results['vulnerabilities'].extend(code_results)
            
            # Authentication/Authorization check
            auth_results = await self._check_auth_security()
            app_results['misconfigurations'].extend(auth_results)
            
            return app_results
            
        except Exception as e:
            self.logger.error(f"Application security scan failed: {str(e)}")
            return app_results
    
    async def _scan_dependencies(self) -> List[Dict]:
        """Scan project dependencies for vulnerabilities."""
        vulnerabilities = []
        
        try:
            # Parse dependency files
            dependency_files = [
                'requirements.txt',
                'package.json',
                'pom.xml',
                'build.gradle'
            ]
            
            for dep_file in dependency_files:
                if os.path.exists(dep_file):
                    deps = self._parse_dependency_file(dep_file)
                    for dep in deps:
                        # Check against vulnerability database
                        vulns = self.vulnerability_db.get(dep['name'], [])
                        for vuln in vulns:
                            if self._is_version_vulnerable(dep['version'], vuln['affected_versions']):
                                vulnerabilities.append({
                                    'type': 'dependency_vulnerability',
                                    'severity': vuln['severity'],
                                    'package': dep['name'],
                                    'version': dep['version'],
                                    'vulnerability_id': vuln['id'],
                                    'description': vuln['description'],
                                    'remediation': f"Upgrade to version {vuln['fixed_versions']}"
                                })
                                
        except Exception as e:
            self.logger.error(f"Dependency scanning failed: {str(e)}")
            
        return vulnerabilities
    
    async def _scan_data_security(self) -> Dict:
        """Scan data security configurations and practices."""
        data_results = {
            'vulnerabilities': [],
            'misconfigurations': [],
            'compliance_issues': []
        }
        
        try:
            # Check data encryption
            encryption_issues = await self._check_data_encryption()
            data_results['vulnerabilities'].extend(encryption_issues)
            
            # Check data access controls
            access_issues = await self._check_data_access()
            data_results['misconfigurations'].extend(access_issues)
            
            # Check data retention policies
            retention_issues = await self._check_data_retention()
            data_results['compliance_issues'].extend(retention_issues)
            
            # Check for sensitive data exposure
            exposure_issues = await self._check_sensitive_data_exposure()
            data_results['vulnerabilities'].extend(exposure_issues)
            
            return data_results
            
        except Exception as e:
            self.logger.error(f"Data security scan failed: {str(e)}")
            return data_results
    
    async def _check_compliance(self) -> Dict:
        """Check compliance with security standards."""
        compliance_results = {
            'compliance_issues': [],
            'recommendations': []
        }
        
        standards = {
            'PCI-DSS': self._check_pci_compliance,
            'HIPAA': self._check_hipaa_compliance,
            'GDPR': self._check_gdpr_compliance,
            'SOC2': self._check_soc2_compliance
        }
        
        for standard, check_func in standards.items():
            if standard in self.config.get('compliance_standards', []):
                issues = await check_func()
                compliance_results['compliance_issues'].extend(issues)
                
        return compliance_results

    def calculate_risk_score(self, scan_results: Dict) -> float:
        """Calculate overall risk score based on scan results."""
        # Base weights for different types of issues
        weights = {
            'critical': 10.0,
            'high': 5.0,
            'medium': 2.0,
            'low': 1.0
        }
        
        total_score = 0
        max_possible_score = 0
        
        # Calculate score for vulnerabilities
        for vuln in scan_results['vulnerabilities']:
            total_score += weights[vuln['severity']]
            max_possible_score += weights['critical']
        
        # Calculate score for misconfigurations
        for misconfig in scan_results['misconfigurations']:
            total_score += weights[misconfig['severity']] * 0.8  # Slightly lower weight
            max_possible_score += weights['critical']
        
        # Calculate score for compliance issues
        for issue in scan_results['compliance_issues']:
            total_score += weights[issue['severity']] * 1.2  # Higher weight for compliance
            max_possible_score += weights['critical']
        
        # Normalize score to 0-100 range
        if max_possible_score == 0:
            return 0
            
        normalized_score = (1 - (total_score / max_possible_score)) * 100
        return round(max(0, min(100, normalized_score)), 2)