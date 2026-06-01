import logging
import json
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio
from services.presence import get_pretty_presence, subscribe_to_ids_and_build
from services.redis_client import redis_client
from services.metrics import inc_connected_session, dec_connected_session, inc_inbound_message, inc_outbound_message

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 30000
CONNECTED_CLIENTS = {}

@socketio.on('connect')
def handle_connect(auth):
    """Handle new WebSocket connection - send Hello opcode."""
    client_id = auth['sid'] if isinstance(auth, dict) else auth
    CONNECTED_CLIENTS[client_id] = {
        'sid': client_id,
        'awaiting_init': True,
        'subscribed_users': set(),
    }

    inc_connected_session()
    emit('message', {
        'op': 1,
        'd': {'heartbeat_interval': HEARTBEAT_INTERVAL}
    })
    logger.info(f"Client connected: {client_id}")

@socketio.on('message')
def handle_message(data):
    """Handle incoming WebSocket messages."""
    inc_inbound_message()

    if not isinstance(data, dict):
        try:
            data = json.loads(data)
        except:
            emit('message', {
                'op': 0,
                't': 'ERROR',
                'd': {'code': 4006, 'message': 'invalid_payload'}
            })
            return

    op = data.get('op')

    if op == 2:  # Initialize
        handle_initialize(data)
    elif op == 3:  # Heartbeat
        handle_heartbeat(data)
    else:
        emit('message', {
            'op': 0,
            't': 'ERROR',
            'd': {'code': 4004, 'message': 'unknown_opcode'}
        })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    from flask_socketio import request
    client_id = request.sid

    if client_id in CONNECTED_CLIENTS:
        del CONNECTED_CLIENTS[client_id]

    dec_connected_session()
    logger.info(f"Client disconnected: {client_id}")

def handle_initialize(data):
    """Handle Initialize opcode (op 2)."""
    from flask_socketio import request
    client_id = request.sid

    d = data.get('d')
    if not d or not isinstance(d, dict) or len(d) == 0:
        emit('message', {
            'op': 0,
            't': 'ERROR',
            'd': {'code': 4005, 'message': 'requires_data_object'}
        }, skip_sid=True)
        return

    client = CONNECTED_CLIENTS.get(client_id)
    if not client:
        return

    client['awaiting_init'] = False
    init_state = None

    if 'subscribe_to_ids' in d:
        user_ids = d['subscribe_to_ids']
        if isinstance(user_ids, list):
            init_state = subscribe_to_ids_and_build(user_ids)
            client['subscribed_users'] = set(user_ids)
            for user_id in user_ids:
                join_room(f"user:{user_id}", skip_sid=True)

    elif 'subscribe_to_id' in d:
        user_id = d['subscribe_to_id']
        status, response = get_pretty_presence(user_id)
        if status == 200:
            init_state = response['data']
        else:
            init_state = {}
        client['subscribed_users'] = {user_id}
        join_room(f"user:{user_id}", skip_sid=True)

    elif d.get('subscribe_to_all'):
        all_users = redis_client.smembers("lanyard:monitored_users")
        init_state = {}
        for user_id in all_users:
            status, response = get_pretty_presence(user_id)
            if status == 200:
                init_state[user_id] = response['data']
        client['subscribed_users'] = all_users
        for user_id in all_users:
            join_room(f"user:{user_id}", skip_sid=True)

    emit('message', {
        'op': 0,
        'seq': 1,
        't': 'INIT_STATE',
        'd': init_state or {}
    })

def handle_heartbeat(data):
    """Handle Heartbeat opcode (op 3)."""
    pass

def broadcast_presence_update(user_id: str, presence_data: dict):
    """Broadcast presence update to all subscribed clients."""
    from services.presence import build_pretty_presence
    # kv_data = kv_get_all(user_id)
    pretty = build_pretty_presence(presence_data, {})
    pretty['user_id'] = user_id

    socketio.emit('message', {
        'op': 0,
        'seq': 2,
        't': 'PRESENCE_UPDATE',
        'd': pretty
    }, room=f"user:{user_id}")
