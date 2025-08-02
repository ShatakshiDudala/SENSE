# =============================================================================
# 5. control.py - Device Control Logic
# =============================================================================

import time
import threading
from datetime import datetime, timedelta
from db import SenseDB
from utils import generate_sensor_data, calculate_power_consumption

class DeviceController:
    def __init__(self):
        self.db = SenseDB()
        self.auto_control_active = True
        self.ac_rotation_active = True
        
    def toggle_device(self, device_id, user_id, force=False):
        """Toggle device on/off with safety checks"""
        room_status = self.get_room_by_device(device_id)
        
        if not room_status:
            return False, "Device not found"
        
        room = room_status['room']
        
        # Check if room is critical and user has permission
        if room[7] and not force:  # is_critical column
            return False, "Critical room - Admin permission required"
        
        # Check if room is VIP and needs special handling
        if room[6]:  # is_vip column
            self.log_vip_access(user_id, device_id)
        
        new_state = self.db.toggle_device(device_id, user_id)
        
        if new_state is not None:
            return True, f"Device {'ON' if new_state else 'OFF'}"
        
        return False, "Failed to toggle device"
    
    def auto_control_empty_rooms(self):
        """Automatically control devices in empty rooms"""
        if not self.auto_control_active:
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get rooms that have been empty for > 15 minutes
        empty_threshold = datetime.now() - timedelta(minutes=15)
        
        cursor.execute('''SELECT r.id, r.room_number, r.occupancy, r.is_critical, r.is_vip
                         FROM rooms r
                         WHERE r.occupancy = 0 AND r.is_critical = FALSE''')
        
        empty_rooms = cursor.fetchall()
        
        for room in empty_rooms:
            room_id = room[0]
            
            # Get devices that are ON in empty rooms
            cursor.execute('SELECT id, device_type FROM devices WHERE room_id = ? AND is_on = TRUE', (room_id,))
            active_devices = cursor.fetchall()
            
            # Turn off non-critical devices
            for device in active_devices:
                device_id, device_type = device
                if device_type in ['light', 'fan', 'projector']:
                    cursor.execute('UPDATE devices SET is_on = FALSE, last_switched = ? WHERE id = ?',
                                 (datetime.now(), device_id))
                    
                    # Log auto action
                    cursor.execute('''INSERT INTO activity_logs (user_id, action, details) 
                                     VALUES (?, ?, ?)''',
                                  (1, "Auto OFF", f"Empty room auto-control: Device {device_id}"))
        
        conn.commit()
        conn.close()
    
    def ac_rotation_system(self):
        """8-hour AC rotation system to prevent overheating"""
        if not self.ac_rotation_active:
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get ACs that have been running for > 8 hours
        eight_hours_ago = datetime.now() - timedelta(hours=8)
        
        cursor.execute('''SELECT d.id, d.room_id, d.device_name, d.last_switched
                         FROM devices d
                         WHERE d.device_type = 'ac' 
                         AND d.is_on = TRUE 
                         AND d.last_switched < ?''', (eight_hours_ago,))
        
        overdue_acs = cursor.fetchall()
        
        for ac in overdue_acs:
            ac_id, room_id, ac_name, last_switched = ac
            
            # Find replacement AC in the same room
            cursor.execute('''SELECT id FROM devices 
                             WHERE room_id = ? AND device_type = 'ac' 
                             AND is_on = FALSE AND status = 'active'
                             ORDER BY last_switched ASC LIMIT 1''', (room_id,))
            
            replacement = cursor.fetchone()
            
            if replacement:
                replacement_id = replacement[0]
                
                # Switch ACs
                current_time = datetime.now()
                cursor.execute('UPDATE devices SET is_on = FALSE, last_switched = ? WHERE id = ?',
                             (current_time, ac_id))
                cursor.execute('UPDATE devices SET is_on = TRUE, last_switched = ? WHERE id = ?',
                             (current_time, replacement_id))
                
                # Log rotation
                cursor.execute('''INSERT INTO activity_logs (user_id, action, details) 
                                 VALUES (?, ?, ?)''',
                              (1, "AC Rotation", f"Room {room_id}: AC {ac_id} -> AC {replacement_id}"))
        
        conn.commit()
        conn.close()
    
    def schedule_room_preconditioning(self, room_id, start_time, end_time):
        """Pre-condition room before scheduled events"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Schedule room preparation 30 minutes before event
        prep_time = start_time - timedelta(minutes=30)
        
        cursor.execute('''INSERT INTO schedules (room_id, event_name, start_time, end_time) 
                         VALUES (?, ?, ?, ?)''',
                      (room_id, "Auto Preconditioning", prep_time, end_time))
        
        conn.commit()
        conn.close()
    
    def get_room_by_device(self, device_id):
        """Get room information by device ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT r.*, d.device_name, d.device_type
                         FROM rooms r
                         JOIN devices d ON r.id = d.room_id
                         WHERE d.id = ?''', (device_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'room': result[:12],  # Room columns
                'device_name': result[12],
                'device_type': result[13]
            }
        return None
    
    def log_vip_access(self, user_id, device_id):
        """Log access to VIP room devices"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''INSERT INTO activity_logs (user_id, action, details) 
                         VALUES (?, ?, ?)''',
                      (user_id, "VIP Access", f"VIP room device control: Device {device_id}"))
        
        conn.commit()
        conn.close()
    
    def emergency_shutdown(self, building_id=None, floor=None):
        """Emergency shutdown of non-critical systems"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = '''UPDATE devices SET is_on = FALSE, last_switched = ?
                   WHERE room_id IN (
                       SELECT id FROM rooms WHERE is_critical = FALSE'''
        
        params = [datetime.now()]
        
        if building_id:
            query += ' AND building_id = ?'
            params.append(building_id)
        
        if floor:
            query += ' AND floor = ?'
            params.append(floor)
        
        query += ')'
        
        cursor.execute(query, params)
        
        # Log emergency action
        cursor.execute('''INSERT INTO activity_logs (user_id, action, details) 
                         VALUES (?, ?, ?)''',
                      (1, "Emergency Shutdown", f"Building: {building_id}, Floor: {floor}"))
        
        conn.commit()
        conn.close()
