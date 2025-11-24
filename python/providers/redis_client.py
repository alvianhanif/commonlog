"""
Redis client for commonlog (Python)
"""

class RedisConfigError(Exception):
    pass

def get_redis_client(config):
    import redis  # Import lazily to avoid distutils issues in Python 3.12+
    host = getattr(config, 'redis_host', None)
    port = getattr(config, 'redis_port', None)
    if not host or not port:
        raise RedisConfigError("redis_host and redis_port must be set in config")
    return redis.StrictRedis(host=host, port=port, decode_responses=True)
