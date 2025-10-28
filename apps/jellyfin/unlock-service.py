#!/usr/bin/env python3
"""
ZFS Unlock Service for Jellyfin
Provides a password-protected web interface to unlock and start/stop Jellyfin
"""
import os
import subprocess
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Get credentials from environment (set these securely)
UNLOCK_USER = os.getenv('UNLOCK_USER', 'admin')
UNLOCK_PASSWORD_HASH = os.getenv('UNLOCK_PASSWORD_HASH', generate_password_hash('changeme'))

# Get ZFS configuration
ZFS_PATH = os.getenv('ZFS_PATH', '/tank/media')
SERVICE_NAME = 'jellyfin'
COMPOSE_PATH = Path(__file__).parent / 'docker-compose.yml'

def run_command(cmd, shell=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
        return {'success': True, 'output': result.stdout, 'error': result.stderr}
    except subprocess.CalledProcessError as e:
        return {'success': False, 'output': '', 'error': str(e)}

def check_auth(username, password):
    """Check if username and password are correct"""
    if username != UNLOCK_USER:
        return False
    return check_password_hash(UNLOCK_PASSWORD_HASH, password)

def is_zfs_mounted():
    """Check if ZFS dataset is mounted"""
    return Path(ZFS_PATH).is_mount()

def is_jellyfin_running():
    """Check if Jellyfin container is running"""
    result = run_command(f'docker ps -q -f name={SERVICE_NAME}')
    if result['success'] and result['output'].strip():
        return True
    return False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'zfs_mounted': is_zfs_mounted(),
        'jellyfin_running': is_jellyfin_running()
    })

@app.route('/status', methods=['GET'])
def status():
    """Get current status"""
    return jsonify({
        'zfs_mounted': is_zfs_mounted(),
        'jellyfin_running': is_jellyfin_running(),
        'zfs_path': ZFS_PATH
    })

@app.route('/unlock', methods=['POST'])
def unlock():
    """Unlock ZFS dataset with password"""
    # Check authentication
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    zfs_password = data.get('password')
    
    if not zfs_password:
        return jsonify({'error': 'Password required'}), 400
    
    if is_zfs_mounted():
        return jsonify({
            'success': True,
            'message': 'ZFS already mounted',
            'zfs_mounted': True
        })
    
    # Load ZFS key and mount
    # Note: This passes the password via stdin to zfs load-key
    cmd = f'echo "{zfs_password}" | zfs load-key -a'
    result = run_command(cmd)
    
    if not result['success']:
        return jsonify({
            'error': 'Failed to load ZFS key',
            'details': result['error']
        }), 500
    
    # Mount ZFS
    mount_result = run_command('zfs mount -a')
    if not mount_result['success']:
        return jsonify({
            'error': 'Failed to mount ZFS',
            'details': mount_result['error']
        }), 500
    
    # Wait for mount to complete
    for _ in range(10):
        if is_zfs_mounted():
            return jsonify({
                'success': True,
                'message': 'ZFS unlocked and mounted successfully',
                'zfs_mounted': True
            })
        time.sleep(1)
    
    return jsonify({
        'error': 'Mount verification failed',
        'zfs_mounted': False
    }), 500

@app.route('/start', methods=['POST'])
def start():
    """Start Jellyfin container"""
    # Check authentication
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not is_zfs_mounted():
        return jsonify({
            'error': 'ZFS must be mounted first',
            'zfs_mounted': False
        }), 400
    
    if is_jellyfin_running():
        return jsonify({
            'success': True,
            'message': 'Jellyfin already running',
            'jellyfin_running': True
        })
    
    # Start Jellyfin
    result = run_command(f'cd {COMPOSE_PATH.parent} && docker-compose up -d {SERVICE_NAME}')
    
    if not result['success']:
        return jsonify({
            'error': 'Failed to start Jellyfin',
            'details': result['error']
        }), 500
    
    # Wait for container to start
    for _ in range(10):
        if is_jellyfin_running():
            return jsonify({
                'success': True,
                'message': 'Jellyfin started successfully',
                'jellyfin_running': True
            })
        time.sleep(1)
    
    return jsonify({
        'error': 'Container start verification failed',
        'jellyfin_running': False
    }), 500

@app.route('/stop', methods=['POST'])
def stop():
    """Stop Jellyfin container"""
    # Check authentication
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not is_jellyfin_running():
        return jsonify({
            'success': True,
            'message': 'Jellyfin not running',
            'jellyfin_running': False
        })
    
    # Stop Jellyfin
    result = run_command(f'cd {COMPOSE_PATH.parent} && docker-compose stop {SERVICE_NAME}')
    
    return jsonify({
        'success': True,
        'message': 'Jellyfin stopped',
        'jellyfin_running': False
    })

@app.route('/unmount', methods=['POST'])
def unmount():
    """Unmount ZFS dataset (and optionally stop Jellyfin)"""
    # Check authentication
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Stop Jellyfin first if running
    if is_jellyfin_running():
        stop()
    
    if not is_zfs_mounted():
        return jsonify({
            'success': True,
            'message': 'ZFS not mounted',
            'zfs_mounted': False
        })
    
    # Unmount ZFS
    result = run_command(f'zfs unmount {ZFS_PATH}')
    
    return jsonify({
        'success': True,
        'message': 'ZFS unmounted',
        'zfs_mounted': False
    })

@app.route('/', methods=['GET'])
def index():
    """Serve the unlock UI"""
    return send_from_directory(Path(__file__).parent, 'unlock-ui.html')

if __name__ == '__main__':
    # Generate a default password hash if not set
    if UNLOCK_PASSWORD_HASH == generate_password_hash('changeme'):
        print("WARNING: Using default password 'changeme'. Set UNLOCK_PASSWORD_HASH env var.")
    
    app.run(host='0.0.0.0', port=8888, debug=False)

