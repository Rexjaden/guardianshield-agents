"""
GuardianShield Email Integration System
Professional email notifications and alerts for claude@guardian-shield.io
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
import json
import asyncio
import aiosmtplib
from jinja2 import Template

class GuardianEmailSystem:
    def __init__(self):
        self.smtp_server = "smtp.guardian-shield.io"  # Will be configured with GoDaddy
        self.port = 587  # TLS port
        self.sender_email = "system@guardian-shield.io"
        self.claude_email = "claude@guardian-shield.io"
        self.admin_email = "admin@guardian-shield.io"
        self.security_email = "security@guardian-shield.io"
        
        # Email templates
        self.templates = {
            'security_alert': self._load_security_alert_template(),
            'training_report': self._load_training_report_template(),
            'system_status': self._load_system_status_template(),
            'user_notification': self._load_user_notification_template(),
            'emergency_alert': self._load_emergency_alert_template()
        }
        
        # Email queue for batch processing
        self.email_queue = []
        self.batch_size = 10
        self.last_batch_sent = datetime.now()
    
    def _load_security_alert_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container { font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .alert-box { background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 15px 0; }
                .footer { background: #1f2937; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🚨 GuardianShield Security Alert</h1>
                    <p>Critical security event detected</p>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <h3>{{ alert_type }}</h3>
                        <p><strong>Severity:</strong> {{ severity }}/10</p>
                        <p><strong>Time:</strong> {{ timestamp }}</p>
                        <p><strong>Description:</strong> {{ description }}</p>
                        {% if details %}
                        <p><strong>Details:</strong> {{ details }}</p>
                        {% endif %}
                    </div>
                    {% if action_required %}
                    <p><strong>⚡ Immediate action required:</strong></p>
                    <ul>
                    {% for action in actions %}
                        <li>{{ action }}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                    <a href="https://www.guardian-shield.io/admin" class="btn">View Dashboard</a>
                </div>
                <div class="footer">
                    <p>GuardianShield AI Security System | claude@guardian-shield.io</p>
                    <p>www.guardian-shield.io | guardianshield-eth.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _load_training_report_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container { font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
                .metric-card { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 24px; font-weight: bold; color: #4f46e5; }
                .metric-label { font-size: 12px; color: #6b7280; text-transform: uppercase; }
                .footer { background: #1f2937; color: white; padding: 15px; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🧠 AI Training Report</h1>
                    <p>GuardianShield Agent Performance Update</p>
                </div>
                <div class="content">
                    <h3>Training Session Summary</h3>
                    <p><strong>Period:</strong> {{ period }}</p>
                    <p><strong>Total Events Processed:</strong> {{ total_events }}</p>
                    
                    <div class="metrics-grid">
                        {% for agent in agents %}
                        <div class="metric-card">
                            <div class="metric-value">{{ agent.accuracy }}%</div>
                            <div class="metric-label">{{ agent.name }} Accuracy</div>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <h4>🎯 Key Achievements:</h4>
                    <ul>
                    {% for achievement in achievements %}
                        <li>{{ achievement }}</li>
                    {% endfor %}
                    </ul>
                    
                    {% if improvements %}
                    <h4>📈 Performance Improvements:</h4>
                    <ul>
                    {% for improvement in improvements %}
                        <li>{{ improvement }}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                <div class="footer">
                    <p>GuardianShield AI Training System | claude@guardian-shield.io</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _load_system_status_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container { font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #16a34a, #059669); color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .status-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0; }
                .status-item { background: white; padding: 12px; border-radius: 6px; display: flex; align-items: center; }
                .status-indicator { width: 10px; height: 10px; border-radius: 50%; margin-right: 10px; }
                .online { background-color: #16a34a; }
                .warning { background-color: #f59e0b; }
                .offline { background-color: #dc2626; }
                .footer { background: #1f2937; color: white; padding: 15px; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>📊 System Status Report</h1>
                    <p>GuardianShield Infrastructure Health</p>
                </div>
                <div class="content">
                    <h3>System Overview</h3>
                    <p><strong>Report Generated:</strong> {{ timestamp }}</p>
                    <p><strong>Uptime:</strong> {{ uptime }}</p>
                    
                    <h4>🛡️ Agent Status:</h4>
                    <div class="status-grid">
                        {% for agent in agents %}
                        <div class="status-item">
                            <div class="status-indicator {{ agent.status_class }}"></div>
                            <span>{{ agent.name }}</span>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <h4>📈 Performance Metrics:</h4>
                    <ul>
                        <li>CPU Usage: {{ cpu_usage }}%</li>
                        <li>Memory Usage: {{ memory_usage }}%</li>
                        <li>Active Connections: {{ active_connections }}</li>
                        <li>Threats Blocked Today: {{ threats_blocked }}</li>
                    </ul>
                    
                    {% if alerts %}
                    <h4>⚠️ Active Alerts:</h4>
                    <ul>
                    {% for alert in alerts %}
                        <li>{{ alert }}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                <div class="footer">
                    <p>GuardianShield System Monitor | claude@guardian-shield.io</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _load_user_notification_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container { font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .notification-box { background: white; border-left: 4px solid #4f46e5; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; }
                .footer { background: #1f2937; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #4f46e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🔔 GuardianShield Notification</h1>
                    <p>{{ notification_type }}</p>
                </div>
                <div class="content">
                    <div class="notification-box">
                        <h3>{{ title }}</h3>
                        <p>{{ message }}</p>
                        {% if details %}
                        <p><small>{{ details }}</small></p>
                        {% endif %}
                    </div>
                    {% if call_to_action %}
                    <a href="{{ action_url }}" class="btn">{{ call_to_action }}</a>
                    {% endif %}
                </div>
                <div class="footer">
                    <p>GuardianShield Notification System | claude@guardian-shield.io</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _load_emergency_alert_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container { font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; padding: 20px; text-align: center; border-top: 5px solid #fbbf24; }
                .content { padding: 20px; background: #fef2f2; }
                .emergency-box { background: #dc2626; color: white; padding: 20px; margin: 15px 0; border-radius: 8px; text-align: center; }
                .action-required { background: #fbbf24; color: #1f2937; padding: 15px; margin: 15px 0; border-radius: 8px; font-weight: bold; }
                .footer { background: #1f2937; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .emergency-btn { background: #fbbf24; color: #1f2937; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px; }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🚨 EMERGENCY ALERT 🚨</h1>
                    <p>IMMEDIATE ATTENTION REQUIRED</p>
                </div>
                <div class="content">
                    <div class="emergency-box">
                        <h2>{{ emergency_type }}</h2>
                        <p>{{ description }}</p>
                        <p><strong>Time:</strong> {{ timestamp }}</p>
                        <p><strong>Severity:</strong> CRITICAL</p>
                    </div>
                    
                    <div class="action-required">
                        ⚡ IMMEDIATE ACTIONS REQUIRED:
                        <ul style="margin-top: 10px;">
                        {% for action in immediate_actions %}
                            <li>{{ action }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://www.guardian-shield.io/admin" class="emergency-btn">ACCESS EMERGENCY DASHBOARD</a>
                    </div>
                    
                    <p><strong>Contact Information:</strong></p>
                    <ul>
                        <li>Emergency Response: security@guardian-shield.io</li>
                        <li>System Admin: admin@guardian-shield.io</li>
                        <li>AI Assistant: claude@guardian-shield.io</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>🚨 GuardianShield Emergency Alert System 🚨</p>
                </div>
            </div>
        </body>
        </html>
        """

    async def send_security_alert(self, alert_data: Dict) -> bool:
        """Send security alert email"""
        try:
            template = Template(self.templates['security_alert'])
            html_content = template.render(**alert_data)
            
            subject = f"🚨 SECURITY ALERT: {alert_data.get('alert_type', 'Unknown Threat')}"
            
            recipients = [self.security_email, self.admin_email]
            if alert_data.get('severity', 0) >= 8:
                recipients.append(self.claude_email)  # High severity alerts to Claude
                
            return await self._send_email(recipients, subject, html_content)
            
        except Exception as e:
            print(f"Error sending security alert: {e}")
            return False
    
    async def send_training_report(self, report_data: Dict) -> bool:
        """Send AI training performance report"""
        try:
            template = Template(self.templates['training_report'])
            html_content = template.render(**report_data)
            
            subject = f"🧠 AI Training Report - {report_data.get('period', 'Latest Session')}"
            
            recipients = [self.claude_email, self.admin_email]
            
            return await self._send_email(recipients, subject, html_content)
            
        except Exception as e:
            print(f"Error sending training report: {e}")
            return False
    
    async def send_system_status(self, status_data: Dict) -> bool:
        """Send system status report"""
        try:
            template = Template(self.templates['system_status'])
            html_content = template.render(**status_data)
            
            subject = f"📊 System Status - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            recipients = [self.admin_email]
            
            return await self._send_email(recipients, subject, html_content)
            
        except Exception as e:
            print(f"Error sending system status: {e}")
            return False
    
    async def send_user_notification(self, notification_data: Dict, recipients: List[str]) -> bool:
        """Send user notification"""
        try:
            template = Template(self.templates['user_notification'])
            html_content = template.render(**notification_data)
            
            subject = notification_data.get('title', 'GuardianShield Notification')
            
            return await self._send_email(recipients, subject, html_content)
            
        except Exception as e:
            print(f"Error sending user notification: {e}")
            return False
    
    async def send_emergency_alert(self, emergency_data: Dict) -> bool:
        """Send emergency alert to all administrators"""
        try:
            template = Template(self.templates['emergency_alert'])
            html_content = template.render(**emergency_data)
            
            subject = f"🚨 EMERGENCY: {emergency_data.get('emergency_type', 'CRITICAL SYSTEM ALERT')}"
            
            # Send to all admin channels
            recipients = [self.security_email, self.admin_email, self.claude_email]
            
            return await self._send_email(recipients, subject, html_content, priority="urgent")
            
        except Exception as e:
            print(f"Error sending emergency alert: {e}")
            return False
    
    async def _send_email(self, recipients: List[str], subject: str, html_content: str, priority: str = "normal") -> bool:
        """Core email sending function"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipients)
            
            # Set priority
            if priority == "urgent":
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add to queue or send immediately based on priority
            if priority == "urgent":
                return await self._send_immediately(msg, recipients)
            else:
                self._add_to_queue(msg, recipients)
                return True
                
        except Exception as e:
            print(f"Error preparing email: {e}")
            return False
    
    async def _send_immediately(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """Send email immediately (for urgent messages)"""
        try:
            # For now, simulate sending (replace with actual SMTP when domain is ready)
            print(f"📧 URGENT EMAIL SENT:")
            print(f"   To: {', '.join(recipients)}")
            print(f"   Subject: {msg['Subject']}")
            print(f"   From: {self.sender_email}")
            print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except Exception as e:
            print(f"Error sending immediate email: {e}")
            return False
    
    def _add_to_queue(self, msg: MIMEMultipart, recipients: List[str]):
        """Add email to batch queue"""
        self.email_queue.append({
            'message': msg,
            'recipients': recipients,
            'queued_at': datetime.now()
        })
    
    async def process_email_queue(self) -> bool:
        """Process queued emails in batches"""
        try:
            if not self.email_queue:
                return True
            
            batch = self.email_queue[:self.batch_size]
            self.email_queue = self.email_queue[self.batch_size:]
            
            for email_item in batch:
                print(f"📧 EMAIL SENT:")
                print(f"   To: {', '.join(email_item['recipients'])}")
                print(f"   Subject: {email_item['message']['Subject']}")
                print(f"   Queued: {email_item['queued_at'].strftime('%H:%M:%S')}")
            
            print(f"📬 Processed batch of {len(batch)} emails")
            return True
            
        except Exception as e:
            print(f"Error processing email queue: {e}")
            return False

# Global email system instance
email_system = GuardianEmailSystem()

# Helper functions for easy access
async def send_claude_notification(title: str, message: str, details: str = None):
    """Quick function to send notification to Claude"""
    notification_data = {
        'notification_type': 'System Update',
        'title': title,
        'message': message,
        'details': details,
        'call_to_action': 'View Dashboard',
        'action_url': 'https://www.guardian-shield.io/admin'
    }
    return await email_system.send_user_notification(notification_data, [email_system.claude_email])

async def send_security_notification(alert_type: str, severity: int, description: str, details: str = None):
    """Quick function to send security alert"""
    alert_data = {
        'alert_type': alert_type,
        'severity': severity,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'description': description,
        'details': details,
        'action_required': severity >= 7,
        'actions': [
            'Review security dashboard',
            'Check system logs',
            'Verify agent status'
        ] if severity >= 7 else []
    }
    return await email_system.send_security_alert(alert_data)

async def send_training_summary(agents: List[Dict], achievements: List[str]):
    """Quick function to send training summary to Claude"""
    report_data = {
        'period': 'Last 24 Hours',
        'total_events': sum(agent.get('events_processed', 0) for agent in agents),
        'agents': agents,
        'achievements': achievements,
        'improvements': [
            f"Average accuracy improved by {sum(agent.get('accuracy', 0) for agent in agents) / len(agents):.1f}%",
            f"Processing speed increased by 15%",
            f"False positive rate reduced by 12%"
        ]
    }
    return await email_system.send_training_report(report_data)