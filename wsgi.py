from sspi_flask_app import init_app
from config import Config, DevConfig, ProdConfig

app = init_app(DevConfig)

if __name__ == "__main__":
    app.run(host='0.0.0.0')