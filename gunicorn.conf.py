bind = '0.0.0.0:5000'  # Specify the host and port for Gunicorn to listen on
workers = 4  # Number of worker processes
worker_class = 'sync'  # Worker processing type
timeout = 60  # Timeout for worker processes in seconds