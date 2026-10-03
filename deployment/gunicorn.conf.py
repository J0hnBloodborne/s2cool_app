"""One process keeps demo state and the model-run lock consistent."""

import os

bind = f"{os.environ.get('HOST', '127.0.0.1')}:{os.environ.get('PORT', '8050')}"
workers = 1
worker_class = "gthread"
threads = 4
# gthread still answers page/health requests while a model is running.
timeout = 300
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
capture_output = True
