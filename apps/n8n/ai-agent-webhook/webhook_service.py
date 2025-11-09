#!/usr/bin/env python3
"""
AI Agent Webhook Service

Receives events from n8n workflows and formats them for AI agent processing.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Configuration
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8080'))
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')
EVENT_STORAGE_PATH = Path(os.getenv('EVENT_STORAGE_PATH', './events'))
EVENT_RETENTION_DAYS = int(os.getenv('EVENT_RETENTION_DAYS', '7'))
SERVER_IP = os.getenv('SERVER_IP', '192.168.86.47')
SERVER_PATH = os.getenv('SERVER_PATH', '~/server')

# Ensure event storage directory exists
EVENT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


class EventStore:
    """Simple file-based event storage"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_event(self, event: Dict) -> str:
        """Save event to storage and return event ID"""
        event_id = f"evt_{int(datetime.now().timestamp() * 1000)}"
        event['event_id'] = event_id
        event['status'] = 'pending'
        event['created_at'] = datetime.now().isoformat()
        
        # Save to file
        event_file = self.storage_path / f"{event_id}.json"
        with open(event_file, 'w') as f:
            json.dump(event, f, indent=2)
        
        logger.info(f"Saved event: {event_id} ({event.get('event_type')})")
        return event_id
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get event by ID"""
        event_file = self.storage_path / f"{event_id}.json"
        if not event_file.exists():
            return None
        
        with open(event_file, 'r') as f:
            return json.load(f)
    
    def list_events(self, limit: int = 50, event_type: Optional[str] = None,
                   severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """List events with filters"""
        events = []
        
        # Get all event files
        event_files = sorted(self.storage_path.glob('evt_*.json'), reverse=True)
        
        for event_file in event_files[:limit * 2]:  # Get more to filter
            try:
                with open(event_file, 'r') as f:
                    event = json.load(f)
                
                # Apply filters
                if event_type and event.get('event_type') != event_type:
                    continue
                if severity and event.get('severity') != severity:
                    continue
                if status and event.get('status') != status:
                    continue
                
                # Only include summary fields
                events.append({
                    'event_id': event.get('event_id'),
                    'event_type': event.get('event_type'),
                    'severity': event.get('severity'),
                    'timestamp': event.get('timestamp') or event.get('created_at'),
                    'status': event.get('status', 'pending'),
                    'workflow_name': event.get('workflow_name')
                })
                
                if len(events) >= limit:
                    break
            except Exception as e:
                logger.error(f"Error reading event file {event_file}: {e}")
        
        return events
    
    def update_event(self, event_id: str, updates: Dict):
        """Update event with new data"""
        event = self.get_event(event_id)
        if not event:
            return False
        
        event.update(updates)
        event['updated_at'] = datetime.now().isoformat()
        
        event_file = self.storage_path / f"{event_id}.json"
        with open(event_file, 'w') as f:
            json.dump(event, f, indent=2)
        
        logger.info(f"Updated event: {event_id}")
        return True
    
    def cleanup_old_events(self, days: int = 7):
        """Remove events older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        for event_file in self.storage_path.glob('evt_*.json'):
            try:
                with open(event_file, 'r') as f:
                    event = json.load(f)
                
                created_at = event.get('created_at')
                if created_at:
                    event_time = datetime.fromisoformat(created_at)
                    if event_time < cutoff:
                        event_file.unlink()
                        removed += 1
            except Exception as e:
                logger.error(f"Error processing event file {event_file}: {e}")
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old events")
        
        return removed


# Initialize event store
event_store = EventStore(EVENT_STORAGE_PATH)


def validate_webhook_auth():
    """Validate webhook authentication"""
    if not WEBHOOK_SECRET:
        return True  # No auth required if secret not set
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    
    token = auth_header[7:]
    return token == WEBHOOK_SECRET


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'event_count': len(list(EVENT_STORAGE_PATH.glob('evt_*.json')))
    })


@app.route('/webhook/ai-agent', methods=['POST'])
def receive_webhook():
    """Receive events from n8n workflows"""
    # Validate authentication
    if not validate_webhook_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get event data
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['event_type', 'severity', 'timestamp', 'event_data']
        for field in required_fields:
            if field not in event_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Save event
        event_id = event_store.save_event(event_data)
        
        logger.info(f"Received event: {event_id} - {event_data.get('event_type')}")
        
        return jsonify({
            'status': 'received',
            'event_id': event_id,
            'message': 'Event received and queued for AI agent processing'
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/events', methods=['GET'])
def list_events():
    """List events with optional filters"""
    limit = int(request.args.get('limit', 50))
    event_type = request.args.get('event_type')
    severity = request.args.get('severity')
    status = request.args.get('status')
    
    events = event_store.list_events(
        limit=limit,
        event_type=event_type,
        severity=severity,
        status=status
    )
    
    return jsonify({
        'events': events,
        'total': len(events)
    })


@app.route('/events/<event_id>', methods=['GET'])
def get_event(event_id: str):
    """Get details of a specific event"""
    event = event_store.get_event(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    return jsonify(event)


@app.route('/events/<event_id>/analyze', methods=['POST'])
def analyze_event(event_id: str):
    """Trigger AI agent analysis for a specific event"""
    event = event_store.get_event(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Update event status
    event_store.update_event(event_id, {
        'status': 'analyzing',
        'analysis_requested_at': datetime.now().isoformat()
    })
    
    logger.info(f"Analysis requested for event: {event_id}")
    
    # TODO: Integrate with AI agent API
    # For now, just mark as analyzing
    
    return jsonify({
        'status': 'analyzing',
        'event_id': event_id,
        'message': 'AI agent analysis started'
    })


@app.route('/events/<event_id>/update', methods=['POST'])
def update_event(event_id: str):
    """Update event with AI agent analysis results"""
    event = event_store.get_event(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    updates = request.get_json()
    if not updates:
        return jsonify({'error': 'No update data provided'}), 400
    
    event_store.update_event(event_id, updates)
    
    return jsonify({
        'status': 'updated',
        'event_id': event_id,
        'message': 'Event updated successfully'
    })


if __name__ == '__main__':
    # Cleanup old events on startup
    event_store.cleanup_old_events(EVENT_RETENTION_DAYS)
    
    logger.info(f"Starting AI Agent Webhook Service on port {WEBHOOK_PORT}")
    logger.info(f"Event storage: {EVENT_STORAGE_PATH}")
    
    app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False)

