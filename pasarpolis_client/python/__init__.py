"""
Pasarpolis Alert Client - Python

A simplified client for pasarpolis services to send alerts to Lark and Slack
with sensible defaults.
"""

from .client import Client, Environment, Provider

__all__ = ["Client", "Environment", "Provider"]