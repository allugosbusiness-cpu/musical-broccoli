# DEPRECATED: This file has been moved to server/api/models.py
# Import here for backwards compatibility only

try:
    from server.api.models import *
except ImportError:
    # If server.api is not available, models should be imported directly from server.api
    pass
