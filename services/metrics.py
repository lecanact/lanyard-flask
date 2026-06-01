from prometheus_client import Counter, Gauge, Histogram
import time

# Counters
lanyard_2xx_responses = Counter(
    'lanyard_2xx_responses',
    'Number of 2xx responses'
)
lanyard_4xx_responses = Counter(
    'lanyard_4xx_responses',
    'Number of 4xx responses'
)
lanyard_5xx_responses = Counter(
    'lanyard_5xx_responses',
    'Number of 5xx responses'
)
lanyard_messages_inbound = Counter(
    'lanyard_messages_inbound',
    'Number of inbound WebSocket messages'
)
lanyard_messages_outbound = Counter(
    'lanyard_messages_outbound',
    'Number of outbound WebSocket messages'
)

# Gauges
lanyard_connected_sessions = Gauge(
    'lanyard_connected_sessions',
    'Number of connected WebSocket sessions'
)
lanyard_monitored_users = Gauge(
    'lanyard_monitored_users',
    'Number of monitored Discord users'
)

# Histograms
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

def inc_2xx():
    lanyard_2xx_responses.inc()

def inc_4xx():
    lanyard_4xx_responses.inc()

def inc_5xx():
    lanyard_5xx_responses.inc()

def inc_inbound_message():
    lanyard_messages_inbound.inc()

def inc_outbound_message():
    lanyard_messages_outbound.inc()

def inc_connected_session():
    lanyard_connected_sessions.inc()

def dec_connected_session():
    lanyard_connected_sessions.dec()

def set_monitored_users(count: int):
    lanyard_monitored_users.set(count)

def record_request_time(duration: float):
    api_request_duration.observe(duration)
