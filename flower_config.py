# Enable debug logging
import os

logging = 'DEBUG'

# view address
# address = '0.0.0.0'
# Run the http server on a given port
port = 5555

basic_auth = [os.environ.get('FLOWER_BASIC_AUTH', 'flower:flower')]

# Refresh dashboards automatically
auto_refresh = True

# Enable support of X-Real-Ip and X-Scheme headers
xheaders = True

# A database file to use if persistent mode is enabled
# db = '/var/flower/db/flower.db'

# Enable persistent mode. If the persistent mode is enabled Flower saves the current state and reloads on restart
persistent = True

# commands to run flower in docker.
# docker build -t "flower" .
# $ docker run -d -p=49555:5555 --rm --name flower -e CELERY_BROKER_URL=redis://0.0.0.0:6379/0 flower flower --port=5555.

# command to run flower in terminal
# celery -A ImageMatchingPlatformBackend flower --conf=flowerconfig.py