"""Top-level package for goalee."""

__author__ = """Konstantinos Panayiotou"""
__email__ = 'klpanagi@gmail.com'
__version__ = '0.1.0'

from goalee.target import (
    Target, Middleware, MQTTMiddleware, RedisMiddleware, AMQPMiddleware
)
