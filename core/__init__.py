"""Shared platform primitives.

Celery will be enabled when the first durable worker workflow is introduced.
Keeping it optional prevents every Django command from depending on an
otherwise unconfigured task queue.
"""
