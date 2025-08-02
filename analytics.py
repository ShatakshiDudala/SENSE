# =============================================================================
# 7. analytics.py - Analytics and Reporting
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from db import SenseDB

class SenseAnalytics:
    def __init__(self):
        self.db = SenseDB()
    
    def get_energy_dashboard_data(self):
        """Get data for energy dashboard"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Current power consumption
        cursor.execute('''SELECT SUM(d.power_rating) as current_load
                         FROM devices d
                         WHERE d.is_on = TRUE''')
        current_load = cursor.fetchone()[0] or 0
        
        # Today's consumption
        today = datetime.now().date()
        cursor.execute('''SELECT SUM(consumption_kwh) as today_consumption,
                                SUM(cost) as today_cost
                         FROM energy_consumption
                         WHERE DATE(timestamp) = ?''', (today,))
        today_data = cursor.fetchone()
        today_consumption = today_data[0] or 0
        today_cost = today_data[1] or 0
        
        # This month's consumption
        first_day_month = datetime.now().replace(day=1).date()
        cursor.execute('''SELECT SUM(consumption_kwh) as month_consumption,
                                SUM(cost) as month_cost
                         FROM energy_consumption
                         WHERE DATE(timestamp) >= ?''', (first_day_month,))
        month_data = cursor.fetchone()
        month_consumption = month_data[0] or 0
        month_cost = month_data[1] or 0
        
        # Device type breakdown
        cursor.execute('''SELECT d.device_type, COUNT(*) as count,
                                SUM(CASE WHEN d.is_on THEN 1 ELSE 0 END) as active_count
                         FROM devices d
                         GROUP BY d.device_type''')
        device_breakdown = cursor.fetchall()
        
        conn.close()
        
        return {
            'current_load': current_load,
            'today_consumption': today_consumption,
            'today_cost': today_cost,
            'month_consumption': month_consumption,
            'month_cost': month_cost,
            'device_breakdown': device_breakdown
        }
    
    def create_consumption_trend_chart(self, days=7):
        """Create energy consumption trend chart"""
        conn = self.db.get_connection()
        
        # Get data for last N days
        start_date = datetime.now() - timedelta(days=days)
        
        query = '''SELECT DATE(timestamp) as date, 
                         SUM(consumption_kwh) as total_consumption,
                         SUM(cost) as total_cost,
                         COUNT(DISTINCT device_id) as active_devices
                  FROM energy_consumption
                  WHERE timestamp >= ?
                  GROUP BY DATE(timestamp)
                  ORDER BY date'''
        
        df = pd.read_sql_query(query, conn, params=(start_date,))
        conn.close()
        
        if df.empty:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(text="No data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Energy Consumption (kWh)', 'Cost (₹)', 
                           'Active Devices', 'Efficiency Trend'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Energy consumption
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['total_consumption'],
                      mode='lines+markers', name='Consumption (kWh)',
                      line=dict(color='#1f77b4', width=3)),
            row=1, col=1
        )
        
        # Cost
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['total_cost'],
                      mode='lines+markers', name='Cost (₹)',
                      line=dict(color='#ff7f0e', width=3)),
            row=1, col=2
        )
        
        # Active devices
        fig.add_trace(
            go.Bar(x=df['date'], y=df['active_devices'],
                   name='Active Devices', marker_color='#2ca02c'),
            row=2, col=1
        )
        
        # Efficiency (Cost per kWh)
        efficiency = df['total_cost'] / df['total_consumption'].replace(0, 1)
        fig.add_trace(
            go.Scatter(x=df['date'], y=efficiency,
                      mode='lines+markers', name='Cost/kWh (₹)',
                      line=dict(color='#d62728', width=3)),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False,
                         title_text="Energy Analytics Dashboard")
        
        return fig
    
    def create_device_utilization_chart(self):
        """Create device utilization chart"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT d.device_type,
                                COUNT(*) as total_devices,
                                SUM(CASE WHEN d.is_on THEN 1 ELSE 0 END) as active_devices,
                                AVG(d.hours_on) as avg_runtime
                         FROM devices d
                         GROUP BY d.device_type
                         ORDER BY total_devices DESC''')
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            fig = go.Figure()
            fig.add_annotation(text="No device data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        device_types = [row[0] for row in data]
        total_devices = [row[1] for row in data]
        active_devices = [row[2] for row in data]
        utilization = [row[2]/row[1]*100 if row[1] > 0 else 0 for row in data]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Device Count by Type', 'Utilization Rate (%)'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Device count
        fig.add_trace(
            go.Bar(x=device_types, y=total_devices, name='Total',
                   marker_color='lightblue'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=device_types, y=active_devices, name='Active',
                   marker_color='darkblue'),
            row=1, col=1
        )
        
        # Utilization rate
        fig.add_trace(
            go.Bar(x=device_types, y=utilization, name='Utilization %',
                   marker_color='green'),
            row=1, col=2
        )
        
        fig.update_layout(height=400, title_text="Device Utilization Analysis")
        
        return fig
    
    def create_room_efficiency_chart(self):
        """Create room efficiency analysis chart"""
        conn = self.db.get_connection()
        
        query = '''SELECT r.room_number, b.name as building_name,
                         r.occupancy, r.max_capacity,
                         COUNT(d.id) as total_devices,
                         SUM(CASE WHEN d.is_on THEN 1 ELSE 0 END) as active_devices,
                         SUM(CASE WHEN d.is_on THEN d.power_rating ELSE 0 END) as current_load
                  FROM rooms r
                  JOIN buildings b ON r.building_id = b.id
                  LEFT JOIN devices d ON r.id = d.room_id
                  GROUP BY r.id, r.room_number, b.name, r.occupancy, r.max_capacity
                  ORDER BY current_load DESC'''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No room data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Calculate efficiency metrics
        df['occupancy_rate'] = (df['occupancy'] / df['max_capacity'] * 100)
        df['power_per_person'] = df['current_load'] / df['occupancy'].replace(0, 1)
        df['room_label'] = df['building_name'] + ' - ' + df['room_number']
        
        # Create bubble chart
        fig = px.scatter(df, x='occupancy_rate', y='current_load',
                        size='total_devices', color='power_per_person',
                        hover_name='room_label',
                        labels={'occupancy_rate': 'Occupancy Rate (%)',
                               'current_load': 'Current Power Load (kW)',
                               'power_per_person': 'Power per Person (kW)'},
                        title='Room Efficiency Analysis',
                        color_continuous_scale='RdYlBu_r')
        
        fig.update_layout(height=500)
        return fig
    
    def get_building_summary(self):
        """Get building-wise summary"""
        conn = self.db.get_connection()
        
        query = '''SELECT b.name as building_name,
                         COUNT(DISTINCT r.id) as total_rooms,
                         SUM(r.occupancy) as total_occupancy,
                         SUM(r.max_capacity) as total_capacity,
                         COUNT(d.id) as total_devices,
                         SUM(CASE WHEN d.is_on THEN 1 ELSE 0 END) as active_devices,
                         SUM(CASE WHEN d.is_on THEN d.power_rating ELSE 0 END) as current_load
                  FROM buildings b
                  LEFT JOIN rooms r ON b.id = r.building_id
                  LEFT JOIN devices d ON r.id = d.room_id
                  GROUP BY b.id, b.name
                  ORDER BY current_load DESC'''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def generate_efficiency_report(self):
        """Generate comprehensive efficiency report"""
        dashboard_data = self.get_energy_dashboard_data()
        building_summary = self.get_building_summary()
        
        # Calculate efficiency metrics
        total_devices = sum([row[1] for row in dashboard_data['device_breakdown']])
        active_devices = sum([row[2] for row in dashboard_data['device_breakdown']])
        overall_utilization = (active_devices / total_devices * 100) if total_devices > 0 else 0
        
        # Identify wastage
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Rooms with devices ON but no occupancy
        cursor.execute('''SELECT r.room_number, b.name, COUNT(d.id) as wasted_devices
                         FROM rooms r
                         JOIN buildings b ON r.building_id = b.id
                         JOIN devices d ON r.id = d.room_id
                         WHERE r.occupancy = 0 AND d.is_on = TRUE
                         GROUP BY r.id, r.room_number, b.name
                         HAVING COUNT(d.id) > 0''')
        
        wastage_data = cursor.fetchall()
        conn.close()
        
        return {
            'overall_utilization': overall_utilization,
            'current_load': dashboard_data['current_load'],
            'today_cost': dashboard_data['today_cost'],
            'month_cost': dashboard_data['month_cost'],
            'building_summary': building_summary,
            'wastage_rooms': wastage_data,
            'total_devices': total_devices,
            'active_devices': active_devices
        }