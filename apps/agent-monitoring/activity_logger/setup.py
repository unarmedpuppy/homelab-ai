"""
Setup script for activity_logger package.
Allows installation as a package for MCP tools to import.
"""

from setuptools import setup, find_packages

setup(
    name="agent-activity-logger",
    version="0.1.0",
    description="Activity logger for agent monitoring system",
    py_modules=["activity_logger"],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses standard library only
    ],
)

