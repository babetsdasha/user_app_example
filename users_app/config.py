import ast as _ast
import os as _os


def _env(key, default=None):
    try:
        value = _os.environ[key]
        return _ast.literal_eval(value)
    except KeyError:
        return default
    except (SyntaxError, ValueError):
        return value


cassandra_host = _env('CASSANDRA_HOST', ['127.0.0.1'])
default_keyspace = _env('DEFAULT_KEYSPACE', 'users_web')
default_connection = _env('DEFAULT_CONNECTION', 'Test Cluster')
bootstrap_servers = _env('KAFKA_ADVERTISED_HOST_NAME', 'localhost')
kafka_port = _env('KAFKA_ADVERTISED_PORT', '9092')
notification_topic = _env('KAFKA_TOPIC_NAME', 'notifications')
log_service = _env('LOG_SERVICE', '172.0.0.1:8000')
max_retry = 15

debug = _env('DEBUG', False)

if debug:
    sleep = _env('SLEEP', 5)
