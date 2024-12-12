import os

# Bind to the port provided by Render
port = int(os.environ.get("PORT", 8000))
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 4
threads = 2
timeout = 120
worker_class = "sync"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"