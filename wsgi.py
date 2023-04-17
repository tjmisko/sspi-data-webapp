from sspi_flask_app import init_app
import sys
import logging
import socket

if socket.gethostname() == "sspi-web-server":
    logging.basicConfig(level=logging.DEBUG, filename='/var/www/sspi.world/logs/sspi.world.log', format='%(asctime)s %(message)s')
    sys.path.insert(0, '/var/www/sspi.world')
    sys.path.insert(0, '/var/www/sspi.world/env/lib/python3.9/site-packages')

from config import Config, DevConfig, ProdConfig

print("Startup info:", str(dir(DevConfig)))
print("SQLALCHEMY_DATABASE_URI", DevConfig.SQLALCHEMY_DATABASE_URI)

if socket.gethostname() == "sspi-web-server":
    app = init_app(ProdConfig)
else:
    app = init_app(DevConfig)

if __name__ == "__main__":
    print("Starting app on port 5000")
    app.run(host='0.0.0.0')
