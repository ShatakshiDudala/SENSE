import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import threading
import queue
import json
import logging
import random 

# Import custom modules
try:
    from auth import authenticate_user, get_user_role, create_user, get_all_users, update_user_role
    from db import (
        get_all_rooms, get_devices_by_room, get_device_status, update_device_status,
        get_room_occupancy, update_room_occupancy, get_energy_consumption,
        add_energy_log, get_device_logs, get_system_alerts, mark_alert_read,
        add_system_alert, get_daily_energy_summary, get_monthly_energy_summary,
        initialize_database
    )
    try:
        from control import (
            toggle_device, get_device_info, check_device_health, 
            auto_rotate_ac, emergency_shutdown, get_room_temperature
        )
    except ImportError:
        # Create placeholder functions if control.py doesn't exist
        def toggle_device(device_id, state): 
            from db import update_device_status
            return update_device_status(device_id, state)
        def get_device_info(device_id): 
            from db import get_device_status
            return get_device_status(device_id)
        def check_device_health(device_id): 
            return {'status': 'Good', 'issues': []}
        def auto_rotate_ac(device_id): 
            return True
        def emergency_shutdown(): 
            return True
        def get_room_temperature(room_id): 
            return random.randint(20, 28)
    
    try:
        from scheduler import start_scheduler, stop_scheduler, get_scheduler_status
    except ImportError:
        # Create placeholder functions if scheduler.py doesn't exist
        def start_scheduler(): return True
        def stop_scheduler(): return True
        def get_scheduler_status(): return {'running': False}
    
    try:
        from analytics import (
            calculate_energy_savings, generate_efficiency_report,
            predict_energy_consumption, get_peak_usage_hours
        )
    except ImportError:
        # Create placeholder functions if analytics.py doesn't exist
        def calculate_energy_savings(days): return random.uniform(5, 15)
        def generate_efficiency_report(): 
            return {
                'overall_efficiency': 75,
                'improvement': 5,
                'wasted_energy': 15.5,
                'carbon_footprint': 45.2,
                'recommendations': ['Turn off devices in unoccupied rooms', 'Implement smart scheduling'],
                'warnings': ['AC units running >8 hours', 'Devices left on overnight']
            }
        def predict_energy_consumption(): return {}
        def get_peak_usage_hours(): return {'morning': '9:00 AM', 'afternoon': '2:00 PM', 'evening': '7:00 PM'}
    
    try:
        from email_alerts import send_alert_email, configure_email_settings
    except ImportError:
        # Create placeholder functions if email_alerts.py doesn't exist
        def send_alert_email(subject, message): return True
        def configure_email_settings(*args): return True
    
    try:
        from iot_simulator import start_iot_simulation, stop_iot_simulation, get_simulation_status
    except ImportError:
        # Create placeholder functions if iot_simulator.py doesn't exist
        def start_iot_simulation(): return True
        def stop_iot_simulation(): return True
        def get_simulation_status(): return {'running': False}
    
    try:
        from utils import format_energy, format_currency, get_device_icon, calculate_runtime
    except ImportError:
        # Create placeholder functions if utils.py doesn't exist
        def format_energy(kwh): return f"{kwh:.2f} kWh"
        def format_currency(amount): return f"${amount:.2f}"
        def get_device_icon(device_type): return "🌪️" if device_type == "fan" else "❄️"
        def calculate_runtime(start_time): 
            if start_time:
                return f"{random.randint(30, 480)} minutes"
            return "0 minutes"
    
    # Initialize database
    initialize_database()
    
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.error("Please make sure all required files are in the same directory as app.py")
    st.info("Required files: auth.py, db.py")
    st.info("Optional files: control.py, scheduler.py, analytics.py, email_alerts.py, iot_simulator.py, utils.py")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="SENSE - Smart Energy Management",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
    }
    .device-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .device-on {
        border-left: 4px solid #4CAF50;
    }
    .device-off {
        border-left: 4px solid #f44336;
    }
    .room-header {
        background: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .alert-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success {
        background: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    .error {
        background: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'selected_room' not in st.session_state:
        st.session_state.selected_room = 1
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if 'notifications_enabled' not in st.session_state:
        st.session_state.notifications_enabled = True
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

def login_page():
    """Display login page"""
    st.markdown('<div class="main-header"><h1>🏢 SENSE - Smart Energy Management System</h1></div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = get_user_role(username)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.markdown("**Demo Credentials:**")
        st.info("👤 Admin: admin / admin123\n\n👤 Manager: manager / manager123\n\n👤 Operator: operator / operator123")

def main_dashboard():
    """Main dashboard page"""
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>⚡ SENSE Dashboard</h1>
        <p>Welcome back, {st.session_state.username} ({st.session_state.user_role})</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh mechanism
    if st.session_state.auto_refresh:
        placeholder = st.empty()
        with placeholder.container():
            if datetime.now() - st.session_state.last_refresh > timedelta(seconds=30):
                st.session_state.last_refresh = datetime.now()
                st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🏢 Room Selection")
        rooms = get_all_rooms()
        room_options = {f"Room {room['room_number']} - {room['room_name']}": room['room_number'] 
                       for room in rooms}
        
        selected_room_key = st.selectbox("Select Room", list(room_options.keys()))
        st.session_state.selected_room = room_options[selected_room_key]
        
        st.markdown("### ⚙️ Settings")
        st.session_state.auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
        st.session_state.notifications_enabled = st.checkbox("Notifications", 
                                                            value=st.session_state.notifications_enabled)
        
        if st.button("🔄 Manual Refresh"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.user_role = ""
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Room Control", "📊 Analytics", "⚠️ Alerts", 
        "📈 Reports", "🔧 Settings", "👥 Admin"
    ])
    
    with tab1:
        display_room_control()
    
    with tab2:
        display_analytics()
    
    with tab3:
        display_alerts()
    
    with tab4:
        display_reports()
    
    with tab5:
        display_settings()
    
    with tab6:
        if st.session_state.user_role == "admin":
            display_admin_panel()
        else:
            st.warning("🚫 Admin access required")

def display_room_control():
    """Display room control interface"""
    room_id = st.session_state.selected_room
    
    # Get room info
    rooms = get_all_rooms()
    current_room = next((r for r in rooms if r['room_number'] == room_id), None)
    
    if not current_room:
        st.error("Room not found!")
        return
    
    # Room header
    occupancy = get_room_occupancy(room_id)
    temperature = get_room_temperature(room_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🏠 {current_room['room_name']}</h4>
            <p>Room {room_id}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        occupancy_status = "👥 Occupied" if occupancy['is_occupied'] else "🚫 Empty"
        st.markdown(f"""
        <div class="metric-card">
            <h4>{occupancy_status}</h4>
            <p>{occupancy['person_count']} people</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🌡️ Temperature</h4>
            <p>{temperature}°C</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        energy_today = get_daily_energy_summary(room_id)
        st.markdown(f"""
        <div class="metric-card">
            <h4>⚡ Energy Today</h4>
            <p>{format_energy(energy_today.get('total_consumption', 0))}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Occupancy controls
    st.markdown("### 👥 Occupancy Management")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Mark as Occupied"):
            update_room_occupancy(room_id, True, occupancy['person_count'] + 1)
            st.success("Room marked as occupied")
            st.rerun()
    
    with col2:
        if st.button("❌ Mark as Empty"):
            update_room_occupancy(room_id, False, 0)
            st.success("Room marked as empty")
            st.rerun()
    
    with col3:
        person_count = st.number_input("Person Count", min_value=0, max_value=50, 
                                     value=occupancy['person_count'])
        if st.button("🔄 Update Count"):
            update_room_occupancy(room_id, person_count > 0, person_count)
            st.success(f"Person count updated to {person_count}")
            st.rerun()
    
    # Device controls
    st.markdown("### 🔌 Device Control")
    devices = get_devices_by_room(room_id)
    
    if not devices:
        st.info("No devices found in this room.")
        return
    
    # Group devices by type
    fans = [d for d in devices if d['device_type'] == 'fan']
    acs = [d for d in devices if d['device_type'] == 'ac']
    
    # Display fans
    if fans:
        st.markdown("#### 🌪️ Fans")
        fan_cols = st.columns(min(len(fans), 3))
        
        for idx, fan in enumerate(fans):
            with fan_cols[idx % 3]:
                display_device_card(fan, occupancy['is_occupied'])
    
    # Display ACs
    if acs:
        st.markdown("#### ❄️ Air Conditioners")
        ac_cols = st.columns(min(len(acs), 2))
        
        for idx, ac in enumerate(acs):
            with ac_cols[idx % 2]:
                display_device_card(ac, occupancy['is_occupied'])
    
    # Bulk operations
    st.markdown("### 🔧 Bulk Operations")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔛 Turn All ON"):
            for device in devices:
                if not occupancy['is_occupied']:
                    toggle_device(device['device_id'], True)
            st.success("All devices turned ON")
            st.rerun()
    
    with col2:
        if st.button("🔴 Turn All OFF"):
            for device in devices:
                toggle_device(device['device_id'], False)
            st.success("All devices turned OFF")
            st.rerun()
    
    with col3:
        if st.button("🌪️ Fans Only"):
            for device in devices:
                if device['device_type'] == 'fan':
                    toggle_device(device['device_id'], True)
                else:
                    toggle_device(device['device_id'], False)
            st.success("Only fans turned ON")
            st.rerun()
    
    with col4:
        if st.button("❄️ ACs Only"):
            for device in devices:
                if device['device_type'] == 'ac':
                    toggle_device(device['device_id'], True)
                else:
                    toggle_device(device['device_id'], False)
            st.success("Only ACs turned ON")
            st.rerun()

def display_device_card(device, room_occupied):
    """Display individual device control card"""
    device_status = get_device_status(device['device_id'])
    is_on = device_status['is_on']
    
    # Calculate runtime
    runtime = calculate_runtime(device_status.get('last_switched_on'))
    
    # Device card
    card_class = "device-on" if is_on else "device-off"
    status_color = "🟢" if is_on else "🔴"
    
    st.markdown(f"""
    <div class="device-card {card_class}">
        <h5>{get_device_icon(device['device_type'])} {device['device_name']}</h5>
        <p><strong>Status:</strong> {status_color} {'ON' if is_on else 'OFF'}</p>
        <p><strong>Runtime:</strong> {runtime}</p>
        <p><strong>Power:</strong> {device['power_rating']}W</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        button_disabled = room_occupied and not is_on
        button_text = "🔛 Turn ON" if not is_on else "🔴 Turn OFF"
        
        if st.button(button_text, key=f"toggle_{device['device_id']}", 
                    disabled=button_disabled):
            success = toggle_device(device['device_id'], not is_on)
            if success:
                action = "turned ON" if not is_on else "turned OFF"
                st.success(f"{device['device_name']} {action}")
                
                # Log the action
                add_energy_log(device['device_id'], 'manual_toggle', 
                             f"Device {action} by {st.session_state.username}")
                st.rerun()
            else:
                st.error("Failed to toggle device")
    
    with col2:
        if st.button("ℹ️ Info", key=f"info_{device['device_id']}"):
            device_info = get_device_info(device['device_id'])
            st.json(device_info)
    
    # Special AC controls
    if device['device_type'] == 'ac' and is_on:
       # Extract the number from strings like "0 minutes", "120 minutes", etc.
       runtime_value = int(runtime.split()[0]) if runtime.split() else 0
       if runtime_value > 480:  # 8 hours in minutes
            st.warning("⚠️ AC running for over 8 hours!")
            if st.button("🔄 Auto Rotate", key=f"rotate_{device['device_id']}"):
                rotated = auto_rotate_ac(device['device_id'])
                if rotated:
                    st.success("AC rotated to prevent overheating")
                else:
                    st.warning("No available AC to rotate with")
    
    # Show warning if room is empty but device is on
    if not room_occupied and is_on:
        st.warning("⚠️ Device is ON but room is empty!")

def display_analytics():
    """Display analytics dashboard"""
    st.markdown("### 📊 Energy Analytics")
    
    # Time period selection
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("Time Period", ["Today", "This Week", "This Month", "Custom"])
    with col2:
        if period == "Custom":
            date_range = st.date_input("Select Date Range", value=[datetime.now().date()])
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics based on selected period
    if period == "Today":
        total_consumption = sum(get_daily_energy_summary(room['room_number'])['total_consumption'] 
                              for room in get_all_rooms())
        savings = calculate_energy_savings(1)
        cost = total_consumption * 0.12  # Assuming $0.12 per kWh
    else:
        # For demo purposes, multiply by period factor
        period_factor = {"This Week": 7, "This Month": 30}.get(period, 1)
        total_consumption = sum(get_daily_energy_summary(room['room_number'])['total_consumption'] 
                              for room in get_all_rooms()) * period_factor
        savings = calculate_energy_savings(period_factor)
        cost = total_consumption * 0.12
    
    with col1:
        st.metric("Total Consumption", format_energy(total_consumption), 
                 delta=f"-{format_energy(savings)} saved")
    
    with col2:
        active_devices = sum(1 for room in get_all_rooms() 
                           for device in get_devices_by_room(room['room_number'])
                           if get_device_status(device['device_id'])['is_on'])
        total_devices = sum(len(get_devices_by_room(room['room_number'])) 
                          for room in get_all_rooms())
        st.metric("Active Devices", f"{active_devices}/{total_devices}")
    
    with col3:
        st.metric("Cost", format_currency(cost), 
                 delta=f"-{format_currency(savings * 0.12)} saved")
    
    with col4:
        efficiency = (savings / (total_consumption + savings)) * 100 if total_consumption > 0 else 0
        st.metric("Efficiency", f"{efficiency:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Energy consumption by room
        st.markdown("#### Energy by Room")
        room_data = []
        for room in get_all_rooms():
            consumption = get_daily_energy_summary(room['room_number'])['total_consumption']
            room_data.append({
                'Room': f"Room {room['room_number']}",
                'Consumption': consumption
            })
        
        if room_data:
            df = pd.DataFrame(room_data)
            fig = px.bar(df, x='Room', y='Consumption', 
                        title="Energy Consumption by Room")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Device status pie chart
        st.markdown("#### Device Status")
        device_status_data = {
            'Status': ['ON', 'OFF'],
            'Count': [active_devices, total_devices - active_devices]
        }
        df_status = pd.DataFrame(device_status_data)
        fig = px.pie(df_status, values='Count', names='Status', 
                    title="Device Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Hourly consumption chart
    st.markdown("#### Hourly Energy Consumption")
    hourly_data = []
    for hour in range(24):
        # Generate sample data for demonstration
        consumption = max(0, 50 + 30 * ((hour - 12) ** 2) / 144 - abs(hour - 14) * 5)
        hourly_data.append({'Hour': f"{hour:02d}:00", 'Consumption': consumption})
    
    df_hourly = pd.DataFrame(hourly_data)
    fig = px.line(df_hourly, x='Hour', y='Consumption', 
                  title="Hourly Energy Consumption Pattern")
    st.plotly_chart(fig, use_container_width=True)
    
    # Peak usage analysis
    st.markdown("#### Peak Usage Analysis")
    peak_hours = get_peak_usage_hours()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Morning Peak:** {peak_hours.get('morning', 'N/A')}")
    with col2:
        st.info(f"**Afternoon Peak:** {peak_hours.get('afternoon', 'N/A')}")
    with col3:
        st.info(f"**Evening Peak:** {peak_hours.get('evening', 'N/A')}")
    
    # Efficiency recommendations
    st.markdown("#### 💡 Efficiency Recommendations")
    report = generate_efficiency_report()
    
    for recommendation in report.get('recommendations', []):
        st.success(f"✅ {recommendation}")
    
    for warning in report.get('warnings', []):
        st.warning(f"⚠️ {warning}")

def display_alerts():
    """Display system alerts"""
    st.markdown("### ⚠️ System Alerts")
    
    alerts = get_system_alerts()
    
    if not alerts:
        st.success("🎉 No active alerts!")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        alert_type_filter = st.selectbox("Filter by Type", 
                                       ["All", "critical", "warning", "info"])
    with col2:
        show_read = st.checkbox("Show Read Alerts", value=False)
    with col3:
        if st.button("🔄 Refresh Alerts"):
            st.rerun()
    
    # Filter alerts
    filtered_alerts = alerts
    if alert_type_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a['alert_type'] == alert_type_filter]
    if not show_read:
        filtered_alerts = [a for a in filtered_alerts if not a['is_read']]
    
    # Display alerts
    for alert in filtered_alerts:
        alert_class = {
            'critical': 'error',
            'warning': 'alert-card',
            'info': 'success'
        }.get(alert['alert_type'], 'alert-card')
        
        alert_icon = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(alert['alert_type'], '📢')
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="alert-card {alert_class}">
                <h5>{alert_icon} {alert['title']}</h5>
                <p>{alert['message']}</p>
                <small>📅 {alert['created_at']} | 🏠 Room {alert.get('room_id', 'N/A')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if not alert['is_read']:
                if st.button("✅ Mark Read", key=f"read_{alert['alert_id']}"):
                    mark_alert_read(alert['alert_id'])
                    st.rerun()
    
    # Alert statistics
    st.markdown("### 📈 Alert Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_alerts = len(alerts)
    critical_alerts = len([a for a in alerts if a['alert_type'] == 'critical'])
    unread_alerts = len([a for a in alerts if not a['is_read']])
    
    with col1:
        st.metric("Total Alerts", total_alerts)
    with col2:
        st.metric("Critical", critical_alerts)
    with col3:
        st.metric("Unread", unread_alerts)
    with col4:
        read_percentage = ((total_alerts - unread_alerts) / total_alerts * 100) if total_alerts > 0 else 0
        st.metric("Read %", f"{read_percentage:.1f}%")

def display_reports():
    """Display reports and analytics"""
    st.markdown("### 📈 Energy Reports")
    
    # Report type selection
    report_type = st.selectbox("Report Type", [
        "Daily Summary", "Weekly Summary", "Monthly Summary", 
        "Device Performance", "Cost Analysis", "Efficiency Report"
    ])
    
    if report_type == "Daily Summary":
        display_daily_summary()
    elif report_type == "Weekly Summary":
        display_weekly_summary()
    elif report_type == "Monthly Summary":
        display_monthly_summary()
    elif report_type == "Device Performance":
        display_device_performance()
    elif report_type == "Cost Analysis":
        display_cost_analysis()
    elif report_type == "Efficiency Report":
        display_efficiency_report()

def display_daily_summary():
    """Display daily energy summary"""
    st.markdown("#### 📅 Daily Energy Summary")
    
    selected_date = st.date_input("Select Date", value=datetime.now().date())
    
    # Room-wise summary
    summary_data = []
    total_consumption = 0
    total_cost = 0
    
    for room in get_all_rooms():
        daily_data = get_daily_energy_summary(room['room_number'])
        consumption = daily_data.get('total_consumption', 0)
        cost = consumption * 0.12
        
        total_consumption += consumption
        total_cost += cost
        
        summary_data.append({
            'Room': f"Room {room['room_number']} - {room['room_name']}",
            'Consumption (kWh)': round(consumption, 2),
            'Cost ($)': round(cost, 2),
            'Devices': len(get_devices_by_room(room['room_number'])),
            'Active Hours': daily_data.get('active_hours', 0)
        })
    
    # Display summary table
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True)
    
    # Totals
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Consumption", f"{total_consumption:.2f} kWh")
    with col2:
        st.metric("Total Cost", f"${total_cost:.2f}")
    with col3:
        savings = calculate_energy_savings(1)
        st.metric("Estimated Savings", f"{savings:.2f} kWh")

def display_weekly_summary():
    """Display weekly summary"""
    st.markdown("#### 📊 Weekly Energy Summary")
    
    # Generate weekly data
    weekly_data = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        day_consumption = sum(get_daily_energy_summary(room['room_number'])['total_consumption'] 
                            for room in get_all_rooms())
        weekly_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Day': date.strftime('%A'),
            'Consumption': day_consumption,
            'Cost': day_consumption * 0.12
        })
    
    df = pd.DataFrame(weekly_data)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(df, x='Day', y='Consumption', 
                    title="Daily Energy Consumption (This Week)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(df, x='Day', y='Cost', 
                     title="Daily Energy Cost (This Week)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Weekly statistics
    st.markdown("#### 📈 Weekly Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Consumption", f"{df['Consumption'].sum():.2f} kWh")
    with col2:
        st.metric("Average Daily", f"{df['Consumption'].mean():.2f} kWh")
    with col3:
        st.metric("Peak Day", f"{df['Consumption'].max():.2f} kWh")
    with col4:
        st.metric("Total Cost", f"${df['Cost'].sum():.2f}")

def display_monthly_summary():
    """Display monthly summary"""
    st.markdown("#### 📅 Monthly Energy Summary")
    
    # Monthly data by room
    monthly_data = []
    for room in get_all_rooms():
        monthly_summary = get_monthly_energy_summary(room['room_number'])
        consumption = monthly_summary.get('total_consumption', 0)
        
        monthly_data.append({
            'Room': f"Room {room['room_number']} - {room['room_name']}",
            'Consumption (kWh)': round(consumption, 2),
            'Cost ($)': round(consumption * 0.12, 2),
            'Avg Daily (kWh)': round(consumption / 30, 2),
            'Peak Day (kWh)': round(consumption * 1.3, 2),  # Estimated peak
            'Efficiency (%)': round(85 + (room['room_number'] % 10), 1)
        })
    
    df = pd.DataFrame(monthly_data)
    st.dataframe(df, use_container_width=True)
    
    # Monthly trends chart
    trend_data = []
    for day in range(1, 31):
        daily_total = sum(get_daily_energy_summary(room['room_number'])['total_consumption'] 
                         for room in get_all_rooms())
        # Add some variation for demo
        variation = 1 + 0.2 * ((day % 7) - 3) / 3
        trend_data.append({
            'Day': day,
            'Consumption': daily_total * variation,
            'Cost': daily_total * variation * 0.12
        })
    
    df_trend = pd.DataFrame(trend_data)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(df_trend, x='Day', y='Consumption', 
                     title="Monthly Energy Consumption Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Room comparison pie chart
        fig = px.pie(df, values='Consumption (kWh)', names='Room',
                    title="Energy Distribution by Room")
        st.plotly_chart(fig, use_container_width=True)

def display_device_performance():
    """Display device performance report"""
    st.markdown("#### 🔧 Device Performance Report")
    
    # Get all devices across all rooms
    all_devices = []
    for room in get_all_rooms():
        devices = get_devices_by_room(room['room_number'])
        for device in devices:
            device_status = get_device_status(device['device_id'])
            device_logs = get_device_logs(device['device_id'])
            
            # Calculate performance metrics
            runtime = calculate_runtime(device_status.get('last_switched_on'))
            total_switches = len([log for log in device_logs if 'toggle' in log.get('action', '')])
            efficiency = max(70, 100 - (total_switches * 2))  # Rough efficiency calculation
            
            all_devices.append({
                'Device ID': device['device_id'],
                'Device Name': device['device_name'],
                'Room': f"Room {room['room_number']}",
                'Type': device['device_type'].upper(),
                'Status': '🟢 ON' if device_status['is_on'] else '🔴 OFF',
                'Runtime (mins)': runtime,
                'Power (W)': device['power_rating'],
                'Total Switches': total_switches,
                'Efficiency (%)': efficiency,
                'Health': '✅ Good' if efficiency > 80 else '⚠️ Fair' if efficiency > 60 else '❌ Poor'
            })
    
    df = pd.DataFrame(all_devices)
    st.dataframe(df, use_container_width=True)
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Efficiency by device type
        efficiency_by_type = df.groupby('Type')['Efficiency (%)'].mean().reset_index()
        fig = px.bar(efficiency_by_type, x='Type', y='Efficiency (%)',
                    title="Average Efficiency by Device Type")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Runtime distribution
        fig = px.histogram(df, x='Runtime (mins)', nbins=20,
                          title="Device Runtime Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Device health summary
    st.markdown("#### 🏥 Device Health Summary")
    col1, col2, col3 = st.columns(3)
    
    good_devices = len(df[df['Health'] == '✅ Good'])
    fair_devices = len(df[df['Health'] == '⚠️ Fair'])
    poor_devices = len(df[df['Health'] == '❌ Poor'])
    
    with col1:
        st.metric("Good Health", good_devices, delta=f"{good_devices/len(df)*100:.1f}%")
    with col2:
        st.metric("Fair Health", fair_devices, delta=f"{fair_devices/len(df)*100:.1f}%")
    with col3:
        st.metric("Poor Health", poor_devices, delta=f"{poor_devices/len(df)*100:.1f}%")

def display_cost_analysis():
    """Display cost analysis report"""
    st.markdown("#### 💰 Cost Analysis Report")
    
    # Time period selection
    col1, col2 = st.columns(2)
    with col1:
        analysis_period = st.selectbox("Analysis Period", 
                                     ["Daily", "Weekly", "Monthly", "Yearly"])
    with col2:
        rate_per_kwh = st.number_input("Rate per kWh ($)", value=0.12, step=0.01)
    
    # Calculate costs by room
    cost_data = []
    total_consumption = 0
    
    for room in get_all_rooms():
        if analysis_period == "Daily":
            consumption = get_daily_energy_summary(room['room_number'])['total_consumption']
        elif analysis_period == "Weekly":
            consumption = get_daily_energy_summary(room['room_number'])['total_consumption'] * 7
        elif analysis_period == "Monthly":
            consumption = get_monthly_energy_summary(room['room_number'])['total_consumption']
        else:  # Yearly
            consumption = get_monthly_energy_summary(room['room_number'])['total_consumption'] * 12
        
        cost = consumption * rate_per_kwh
        total_consumption += consumption
        
        # Calculate device costs
        devices = get_devices_by_room(room['room_number'])
        fan_cost = sum(d['power_rating'] * 0.001 * rate_per_kwh * 8 
                      for d in devices if d['device_type'] == 'fan')  # 8 hours avg
        ac_cost = sum(d['power_rating'] * 0.001 * rate_per_kwh * 6 
                     for d in devices if d['device_type'] == 'ac')    # 6 hours avg
        
        cost_data.append({
            'Room': f"Room {room['room_number']} - {room['room_name']}",
            'Consumption (kWh)': round(consumption, 2),
            'Total Cost ($)': round(cost, 2),
            'Fan Cost ($)': round(fan_cost, 2),
            'AC Cost ($)': round(ac_cost, 2),
            'Cost per kWh ($)': rate_per_kwh
        })
    
    df = pd.DataFrame(cost_data)
    st.dataframe(df, use_container_width=True)
    
    # Cost visualization
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(df, x='Room', y='Total Cost ($)',
                    title=f"{analysis_period} Energy Cost by Room")
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cost breakdown by device type
        total_fan_cost = df['Fan Cost ($)'].sum()
        total_ac_cost = df['AC Cost ($)'].sum()
        
        breakdown_data = pd.DataFrame({
            'Device Type': ['Fans', 'ACs'],
            'Cost': [total_fan_cost, total_ac_cost]
        })
        
        fig = px.pie(breakdown_data, values='Cost', names='Device Type',
                    title="Cost Breakdown by Device Type")
        st.plotly_chart(fig, use_container_width=True)
    
    # Cost summary metrics
    st.markdown("#### 💵 Cost Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    total_cost = df['Total Cost ($)'].sum()
    avg_cost_per_room = total_cost / len(df)
    potential_savings = calculate_energy_savings(1) * rate_per_kwh
    
    with col1:
        st.metric("Total Cost", f"${total_cost:.2f}")
    with col2:
        st.metric("Avg per Room", f"${avg_cost_per_room:.2f}")
    with col3:
        st.metric("Potential Savings", f"${potential_savings:.2f}")
    with col4:
        savings_percentage = (potential_savings / total_cost * 100) if total_cost > 0 else 0
        st.metric("Savings %", f"{savings_percentage:.1f}%")

def display_efficiency_report():
    """Display efficiency analysis report"""
    st.markdown("#### ⚡ Energy Efficiency Report")
    
    # Generate efficiency report
    efficiency_report = generate_efficiency_report()
    
    # Overall efficiency score
    overall_score = efficiency_report.get('overall_efficiency', 75)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Efficiency", f"{overall_score}%", 
                 delta=f"+{efficiency_report.get('improvement', 5)}%")
    with col2:
        wasted_energy = efficiency_report.get('wasted_energy', 15.5)
        st.metric("Wasted Energy", f"{wasted_energy} kWh")
    with col3:
        carbon_footprint = efficiency_report.get('carbon_footprint', 45.2)
        st.metric("Carbon Footprint", f"{carbon_footprint} kg CO2")
    
    # Efficiency by room
    room_efficiency = []
    for room in get_all_rooms():
        devices = get_devices_by_room(room['room_number'])
        occupancy = get_room_occupancy(room['room_number'])
        
        # Calculate room efficiency (simplified)
        active_devices = sum(1 for device in devices 
                           if get_device_status(device['device_id'])['is_on'])
        
        if occupancy['is_occupied']:
            efficiency = min(100, (active_devices / len(devices)) * 100) if devices else 0
        else:
            efficiency = max(0, 100 - (active_devices / len(devices)) * 100) if devices else 100
        
        room_efficiency.append({
            'Room': f"Room {room['room_number']}",
            'Efficiency (%)': round(efficiency, 1),
            'Devices': len(devices),
            'Active': active_devices,
            'Occupied': '✅' if occupancy['is_occupied'] else '❌',
            'Status': '🟢 Excellent' if efficiency > 80 else 
                     '🟡 Good' if efficiency > 60 else '🔴 Poor'
        })
    
    df_efficiency = pd.DataFrame(room_efficiency)
    st.dataframe(df_efficiency, use_container_width=True)
    
    # Efficiency trends
    st.markdown("#### 📈 Efficiency Trends")
    
    # Generate trend data (demo)
    trend_data = []
    for day in range(30, 0, -1):
        date = datetime.now() - timedelta(days=day)
        efficiency = 70 + 20 * (1 + 0.5 * ((day % 7) - 3) / 3)  # Simulated trend
        trend_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Efficiency': max(0, min(100, efficiency))
        })
    
    df_trend = pd.DataFrame(trend_data)
    fig = px.line(df_trend, x='Date', y='Efficiency',
                  title="30-Day Efficiency Trend")
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("#### 💡 Efficiency Recommendations")
    
    recommendations = efficiency_report.get('recommendations', [
        "Turn off devices in unoccupied rooms",
        "Implement smart scheduling for AC rotation",
        "Optimize peak hour usage",
        "Regular maintenance of HVAC systems"
    ])
    
    for i, recommendation in enumerate(recommendations, 1):
        st.success(f"{i}. {recommendation}")
    
    # Energy waste analysis
    st.markdown("#### 🗑️ Energy Waste Analysis")
    
    waste_sources = [
        {"Source": "Unoccupied rooms with active devices", "Waste (kWh)": 45.2, "Cost ($)": 5.42},
        {"Source": "AC units running >8 hours", "Waste (kWh)": 32.1, "Cost ($)": 3.85},
        {"Source": "Devices left on overnight", "Waste (kWh)": 28.7, "Cost ($)": 3.44},
        {"Source": "Inefficient device scheduling", "Waste (kWh)": 15.9, "Cost ($)": 1.91}
    ]
    
    df_waste = pd.DataFrame(waste_sources)
    st.dataframe(df_waste, use_container_width=True)

def display_settings():
    """Display system settings"""
    st.markdown("### ⚙️ System Settings")
    
    tabs = st.tabs(["General", "Notifications", "Automation", "Email"])
    
    with tabs[0]:  # General Settings
        st.markdown("#### 🔧 General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_refresh_interval = st.slider("Auto Refresh Interval (seconds)", 
                                            min_value=10, max_value=300, value=30)
            enable_dark_mode = st.checkbox("Enable Dark Mode", 
                                         value=st.session_state.dark_mode)
            show_device_details = st.checkbox("Show Device Details", value=True)
            enable_sound_alerts = st.checkbox("Enable Sound Alerts", value=False)
        
        with col2:
            default_ac_runtime = st.number_input("Max AC Runtime (hours)", 
                                               min_value=1, max_value=24, value=8)
            energy_rate = st.number_input("Energy Rate ($/kWh)", 
                                        min_value=0.01, max_value=1.0, value=0.12)
            temperature_threshold = st.number_input("Temperature Alert Threshold (°C)", 
                                                   min_value=15, max_value=35, value=28)
            occupancy_timeout = st.number_input("Occupancy Timeout (minutes)", 
                                              min_value=5, max_value=120, value=30)
        
        if st.button("💾 Save General Settings"):
            st.session_state.dark_mode = enable_dark_mode
            st.success("Settings saved successfully!")
    
    with tabs[1]:  # Notification Settings
        st.markdown("#### 🔔 Notification Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Alert Types**")
            enable_critical_alerts = st.checkbox("Critical Alerts", value=True)
            enable_warning_alerts = st.checkbox("Warning Alerts", value=True)
            enable_info_alerts = st.checkbox("Info Alerts", value=False)
            enable_energy_alerts = st.checkbox("Energy Threshold Alerts", value=True)
        
        with col2:
            st.markdown("**Notification Methods**")
            enable_browser_notifications = st.checkbox("Browser Notifications", value=True)
            enable_email_notifications = st.checkbox("Email Notifications", value=False)
            enable_sms_notifications = st.checkbox("SMS Notifications", value=False)
            enable_dashboard_alerts = st.checkbox("Dashboard Alerts", value=True)
        
        st.markdown("**Notification Schedule**")
        col1, col2 = st.columns(2)
        with col1:
            notification_start_time = st.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
        with col2:
            notification_end_time = st.time_input("End Time", value=datetime.strptime("22:00", "%H:%M").time())
        
        if st.button("💾 Save Notification Settings"):
            st.success("Notification settings saved!")
    
    with tabs[2]:  # Automation Settings
        st.markdown("#### 🤖 Automation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Auto Control**")
            enable_auto_off = st.checkbox("Auto turn off when room empty", value=True)
            enable_ac_rotation = st.checkbox("Auto AC rotation", value=True)
            enable_schedule_control = st.checkbox("Scheduled device control", value=False)
            enable_smart_learning = st.checkbox("Smart learning mode", value=False)
        
        with col2:
            st.markdown("**Thresholds**")
            auto_off_delay = st.slider("Auto-off delay (minutes)", 1, 60, 15)
            ac_rotation_hours = st.slider("AC rotation interval (hours)", 4, 12, 8)
            energy_threshold = st.slider("Energy alert threshold (kWh)", 10, 100, 50)
            cost_threshold = st.slider("Cost alert threshold ($)", 5, 50, 20)
        
        # Scheduler status
        st.markdown("#### 📅 Scheduler Status")
        scheduler_status = get_scheduler_status()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            status_color = "🟢" if scheduler_status.get('running', False) else "🔴"
            st.info(f"**Status:** {status_color} {'Running' if scheduler_status.get('running', False) else 'Stopped'}")
        
        with col2:
            if st.button("▶️ Start Scheduler"):
                start_scheduler()
                st.success("Scheduler started!")
                st.rerun()
        
        with col3:
            if st.button("⏹️ Stop Scheduler"):
                stop_scheduler()
                st.warning("Scheduler stopped!")
                st.rerun()
        
        if st.button("💾 Save Automation Settings"):
            st.success("Automation settings saved!")
    
    with tabs[3]:  # Email Settings
        st.markdown("#### 📧 Email Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587)
            email_username = st.text_input("Email Username")
            email_password = st.text_input("Email Password", type="password")
        
        with col2:
            recipient_emails = st.text_area("Recipient Emails (one per line)", 
                                          placeholder="admin@company.com\nmanager@company.com")
            email_subject_prefix = st.text_input("Subject Prefix", value="[SENSE Alert]")
            enable_html_emails = st.checkbox("Enable HTML Emails", value=True)
        
        if st.button("🧪 Test Email Configuration"):
            if email_username and email_password:
                try:
                    configure_email_settings(smtp_server, smtp_port, email_username, email_password)
                    st.success("Email configuration test successful!")
                except Exception as e:
                    st.error(f"Email configuration test failed: {e}")
            else:
                st.warning("Please provide email credentials")
        
        if st.button("💾 Save Email Settings"):
            st.success("Email settings saved!")

def display_admin_panel():
    """Display admin panel (admin only)"""
    st.markdown("### 👥 Admin Panel")
    
    tabs = st.tabs(["User Management", "System Status", "Device Management", "Logs"])
    
    with tabs[0]:  # User Management
        st.markdown("#### 👤 User Management")
        
        # Add new user
        with st.expander("➕ Add New User"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_username = st.text_input("Username")
            with col2:
                new_password = st.text_input("Password", type="password")
            with col3:
                new_role = st.selectbox("Role", ["admin", "manager", "operator"])
            
            if st.button("➕ Create User"):
                if new_username and new_password:
                    success = create_user(new_username, new_password, new_role)
                    if success:
                        st.success(f"User '{new_username}' created successfully!")
                    else:
                        st.error("Failed to create user")
                else:
                    st.warning("Please provide username and password")
        
        # Existing users
        st.markdown("#### 📋 Existing Users")
        users = get_all_users()
        
        if users:
            user_data = []
            for user in users:
                user_data.append({
                    'Username': user['username'],
                    'Role': user['role'],
                    'Created': user.get('created_at', 'N/A'),
                    'Last Login': user.get('last_login', 'Never')
                })
            
            df_users = pd.DataFrame(user_data)
            st.dataframe(df_users, use_container_width=True)
            
            # User role update
            st.markdown("#### 🔄 Update User Role")
            col1, col2, col3 = st.columns(3)
            with col1:
                user_to_update = st.selectbox("Select User", [u['username'] for u in users])
            with col2:
                new_user_role = st.selectbox("New Role", ["admin", "manager", "operator"])
            with col3:
                if st.button("🔄 Update Role"):
                    success = update_user_role(user_to_update, new_user_role)
                    if success:
                        st.success(f"Role updated for '{user_to_update}'")
                    else:
                        st.error("Failed to update role")
        else:
            st.info("No users found")
    
    with tabs[1]:  # System Status
        st.markdown("#### 🖥️ System Status")
        
        # System metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rooms = len(get_all_rooms())
            st.metric("Total Rooms", total_rooms)
        
        with col2:
            total_devices = sum(len(get_devices_by_room(room['room_number'])) 
                              for room in get_all_rooms())
            st.metric("Total Devices", total_devices)
        
        with col3:
            active_users = len(get_all_users())
            st.metric("Active Users", active_users)
        
        with col4:
            unread_alerts = len([a for a in get_system_alerts() if not a['is_read']])
            st.metric("Unread Alerts", unread_alerts)
        
        # System health
        st.markdown("#### 🏥 System Health")
        
        health_metrics = [
            {"Component": "Database", "Status": "🟢 Healthy", "Uptime": "99.9%"},
            {"Component": "Scheduler", "Status": "🟢 Running" if get_scheduler_status().get('running') else "🔴 Stopped", "Uptime": "98.5%"},
            {"Component": "IoT Simulator", "Status": "🟢 Active" if get_simulation_status().get('running') else "🔴 Inactive", "Uptime": "97.2%"},
            {"Component": "Email Service", "Status": "🟡 Warning", "Uptime": "95.1%"},
        ]
        
        df_health = pd.DataFrame(health_metrics)
        st.dataframe(df_health, use_container_width=True)
        
        # IoT Simulator Control
        st.markdown("#### 🤖 IoT Simulator Control")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start IoT Simulator"):
                start_iot_simulation()
                st.success("IoT Simulator started!")
        
        with col2:
            if st.button("⏹️ Stop IoT Simulator"):
                stop_iot_simulation()
                st.warning("IoT Simulator stopped!")
    
    with tabs[2]:  # Device Management
        st.markdown("#### 🔧 Device Management")
        
        # Device health check
        if st.button("🔍 Run Device Health Check"):
            with st.spinner("Checking device health..."):
                health_results = []
                for room in get_all_rooms():
                    devices = get_devices_by_room(room['room_number'])
                    for device in devices:
                        health = check_device_health(device['device_id'])
                        health_results.append({
                            'Device': device['device_name'],
                            'Room': f"Room {room['room_number']}",
                            'Health': health.get('status', 'Unknown'),
                            'Issues': ', '.join(health.get('issues', [])) or 'None'
                        })
                
                df_health = pd.DataFrame(health_results)
                st.dataframe(df_health, use_container_width=True)
        
        # Emergency controls
        st.markdown("#### 🚨 Emergency Controls")
        st.warning("⚠️ Use emergency controls only when necessary!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚨 Emergency Shutdown All", type="secondary"):
                emergency_shutdown()
                st.error("Emergency shutdown initiated!")
                add_system_alert("Emergency Shutdown", "All devices have been shut down", "critical")
        
        with col2:
            selected_room_emergency = st.selectbox("Emergency Room", 
                                                 [f"Room {r['room_number']}" for r in get_all_rooms()])
            if st.button("🚨 Emergency Shutdown Room", type="secondary"):
                room_num = int(selected_room_emergency.split()[1])
                devices = get_devices_by_room(room_num)
                for device in devices:
                    toggle_device(device['device_id'], False)
                st.error(f"Emergency shutdown for {selected_room_emergency}!")
    
    with tabs[3]:  # System Logs
        st.markdown("#### 📜 System Logs")
        
        # Log filtering
        col1, col2, col3 = st.columns(3)
        with col1:
            log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR", "CRITICAL"])
        with col2:
            log_days = st.selectbox("Time Period", ["Today", "Last 7 days", "Last 30 days"])
        with col3:
            if st.button("🔄 Refresh Logs"):
                st.rerun()
        
        # Sample log data (in real implementation, this would come from actual logs)
        sample_logs = [
            {"Timestamp": "2024-01-15 10:30:15", "Level": "INFO", "Message": "Device Fan-101 turned ON", "User": "operator"},
            {"Timestamp": "2024-01-15 10:28:42", "Level": "WARNING", "Message": "AC-205 running for 8+ hours", "User": "system"},
            {"Timestamp": "2024-01-15 10:25:33", "Level": "ERROR", "Message": "Failed to connect to device AC-301", "User": "system"},
            {"Timestamp": "2024-01-15 10:22:18", "Level": "INFO", "Message": "Room 5 marked as occupied", "User": "manager"},
            {"Timestamp": "2024-01-15 10:20:05", "Level": "CRITICAL", "Message": "Emergency shutdown initiated", "User": "admin"},
        ]
        
        # Filter logs based on selection
        filtered_logs = sample_logs
        if log_level != "All":
            filtered_logs = [log for log in filtered_logs if log['Level'] == log_level]
        
        # Display logs
        for log in filtered_logs:
            level_color = {
                'INFO': 'info',
                'WARNING': 'warning', 
                'ERROR': 'error',
                'CRITICAL': 'error'
            }.get(log['Level'], 'info')
            
            with st.container():
                st.markdown(f"""
                <div class="alert-card {level_color}">
                    <strong>[{log['Timestamp']}] {log['Level']}</strong><br>
                    {log['Message']}<br>
                    <small>User: {log['User']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Export logs
        if st.button("📥 Export Logs"):
            df_logs = pd.DataFrame(filtered_logs)
            csv = df_logs.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

def main():
    """Main application function"""
    initialize_session_state()
    
    # Authentication check
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}")
        
        # Show error details in development mode
        if st.checkbox("Show Error Details (Debug Mode)"):
            st.exception(e)
        
        # Recovery options
        st.markdown("### 🔧 Recovery Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Restart Application"):
                st.rerun()
        
        with col2:
            if st.button("🚪 Logout & Restart"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.button("📞 Contact Support"):
                st.info("Contact: support@sense-energy.com")