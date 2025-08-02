# =============================================================================
# 8. email_alerts.py - Alert System
# =============================================================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

class AlertSystem:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = "sense.alerts@company.com"  # Configure your email
        self.email_password = "your_app_password"     # Configure your password
        self.logger = logging.getLogger(__name__)
        
    def send_email_alert(self, to_email, subject, message, alert_type="INFO"):
        """Send email alert (simulation)"""
        try:
            # In a real implementation, you would send actual emails
            # For now, we'll just log the alert
            alert_log = {
                'timestamp': datetime.now().isoformat(),
                'to': to_email,
                'subject': subject,
                'message': message,
                'type': alert_type
            }
            
            self.logger.info(f"EMAIL ALERT: {alert_log}")
            
            # Simulate email sending delay
            import time
            time.sleep(0.1)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def send_high_consumption_alert(self, building_name, current_load, threshold=50.0):
        """Send high consumption alert"""
        if current_load > threshold:
            subject = f"⚠️ High Energy Consumption Alert - {building_name}"
            message = f"""
            High energy consumption detected in {building_name}:
            
            Current Load: {current_load:.2f} kW
            Threshold: {threshold:.2f} kW
            Excess: {current_load - threshold:.2f} kW
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please review device usage and consider load optimization.
            
            - SENSE Energy Management System
            """
            
            return self.send_email_alert("admin@company.com", subject, message, "WARNING")
        return False
    
    def send_maintenance_alert(self, device_name, room_number, due_date):
        """Send maintenance reminder alert"""
        subject = f"🔧 Maintenance Due - {device_name}"
        message = f"""
        Device maintenance reminder:
        
        Device: {device_name}
        Location: {room_number}
        Due Date: {due_date}
        
        Please schedule maintenance to ensure optimal performance.
        
        - SENSE Energy Management System
        """
        
        return self.send_email_alert("maintenance@company.com", subject, message, "MAINTENANCE")
    
    def send_emergency_alert(self, event_type, building_name, details):
        """Send emergency alert"""
        subject = f"🚨 EMERGENCY ALERT - {event_type}"
        message = f"""
        EMERGENCY SITUATION DETECTED:
        
        Event: {event_type}
        Building: {building_name}
        Details: {details}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Immediate action required!
        
        - SENSE Energy Management System
        """
        
        # Send to multiple recipients for emergency
        recipients = ["admin@company.com", "security@company.com", "emergency@company.com"]
        
        success = True
        for recipient in recipients:
            success &= self.send_email_alert(recipient, subject, message, "EMERGENCY")
        
        return success
    
    def send_ac_rotation_alert(self, room_number, old_ac, new_ac):
        """Send AC rotation notification"""
        subject = f"🔄 AC Rotation - Room {room_number}"
        message = f"""
        Automatic AC rotation completed:
        
        Room: {room_number}
        Switched OFF: {old_ac}
        Switched ON: {new_ac}
        Reason: 8-hour operation limit reached
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        This is an automated system action to prevent equipment overheating.
        
        - SENSE Energy Management System
        """
        
        return self.send_email_alert("operations@company.com", subject, message, "INFO")
    
    def send_wastage_alert(self, empty_rooms, total_wasted_power):
        """Send energy wastage alert"""
        if not empty_rooms:
            return False
            
        subject = f"💡 Energy Wastage Detected - {len(empty_rooms)} Rooms"
        
        room_list = "\n".join([f"- {room[0]} ({room[1]} devices)" for room in empty_rooms])
        
        message = f"""
        Energy wastage detected in empty rooms:
        
        {room_list}
        
        Total Wasted Power: {total_wasted_power:.2f} kW
        Estimated Daily Cost: ₹{total_wasted_power * 24 * 8:.2f}
        
        Consider implementing auto-shutoff for these areas.
        
        - SENSE Energy Management System
        """
        
        return self.send_email_alert("energy.manager@company.com", subject, message, "WARNING")
