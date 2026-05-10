#!/usr/bin/env python3
"""
Priva VP9508 Greenhouse Climate Control - Data Analytics Dashboard
Sensor data from 2020-01-25 to 2026-04-25 (6+ years, 371 channels, ~6.5M records)
"""

from flask import Flask, render_template, jsonify, send_from_directory, request
from ai_assistant import generate_ai_response
import pickle
import json
import datetime
import os
import statistics

app = Flask(__name__)

# Load pre-processed data
DATA_FILE = '/home/claude/greenhouse_data_clean.pkl'
JSON_FILE = 'static/data.json'

with open(JSON_FILE, 'r') as f:
    SENSOR_DATA = json.load(f)

# Channel groups and metadata
GROUPS = {
    'weather': {'label': 'Xarici Hava', 'icon': '🌤️', 'color': '#00d4aa'},
    'greenhouse_temp': {'label': 'İstixana Temperaturu', 'icon': '🌡️', 'color': '#ff6b6b'},
    'humidity': {'label': 'Rütubət', 'icon': '💧', 'color': '#4ecdc4'},
    'heating': {'label': 'Isıtma Sistemi', 'icon': '🔥', 'color': '#f7b731'},
    'ventilation': {'label': 'Ventilyasiya', 'icon': '💨', 'color': '#a29bfe'},
    'co2': {'label': 'CO₂ Sistemi', 'icon': '🌿', 'color': '#6c5ce7'},
    'curtain': {'label': 'Pərdə Sistemi', 'icon': '🎭', 'color': '#fd79a8'},
    'water': {'label': 'Su Temperaturu', 'icon': '🌊', 'color': '#0984e3'},
    'water_quality': {'label': 'Su Keyfiyyəti', 'icon': '⚗️', 'color': '#00b894'},
    'energy': {'label': 'Enerji / Qaz', 'icon': '⚡', 'color': '#e17055'},
}

@app.route('/')
def index():
    # Build summary stats
    summary = {}
    for ch_id, info in SENSOR_DATA.items():
        group = info['group']
        if group not in summary:
            summary[group] = []
        summary[group].append({
            'id': ch_id,
            'name': info['name'],
            'unit': info['unit'],
            'records': info['total_records'],
            'date_from': info['date_from'],
            'date_to': info['date_to'],
            'min_val': info['min_val'],
            'max_val': info['max_val'],
            'avg_val': info['avg_val'],
        })
    
    total_records = sum(info['total_records'] for info in SENSOR_DATA.values())
    
    return render_template('index.html',
        summary=summary,
        groups=GROUPS,
        total_records=total_records,
        total_channels=len(SENSOR_DATA),
        date_from='2020-01-25',
        date_to='2026-04-25',
    )

@app.route('/api/channel/<ch_id>')
def get_channel(ch_id):
    if ch_id not in SENSOR_DATA:
        return jsonify({'error': 'Channel not found'}), 404
    return jsonify(SENSOR_DATA[ch_id])

@app.route('/api/channels')
def get_channels():
    result = {}
    for ch_id, info in SENSOR_DATA.items():
        result[ch_id] = {
            'name': info['name'],
            'unit': info['unit'],
            'group': info['group'],
            'total_records': info['total_records'],
            'min_val': info['min_val'],
            'max_val': info['max_val'],
            'avg_val': info['avg_val'],
            'date_from': info['date_from'],
            'date_to': info['date_to'],
        }
    return jsonify(result)

@app.route('/api/group/<group_name>')
def get_group(group_name):
    channels = {k: v for k, v in SENSOR_DATA.items() if v['group'] == group_name}
    return jsonify(channels)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    history = data.get('history', [])  # son 10 mesaj
    if not message:
        return jsonify({'error': 'Mesaj boşdur'}), 400
    response = generate_ai_response(message, SENSOR_DATA, history)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
