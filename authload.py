from sspi_flask_app import init_app
from config import ProdConfig
from sspi_flask_app.models.usermodel import User
from flask_sqlalchemy import SQLAlchemy
import flask_bcrypt
import secrets
import os
from sspi_flask_app import db 
## Run via the command below:
## sudo -u www-data bash -c 'source /var/www/sspi.world/env/bin/activate && python /var/www/sspi.world/authload.py'

app = init_app(ProdConfig)

auth_dir = os.environ.get('USER_AUTH_DIR')
user_info = []
for filename in os.listdir(auth_dir):
    filepath = os.path.join(auth_dir, filename)
    if os.path.isfile(filepath):
        with open(filepath, 'r') as file:
            raw_info = file.read()
            line_list = raw_info.split('\n')[:2]
            output_dict = {}
            for line in line_list:
                line_split = line.split("=")
                output_dict[line_split[0]] = line_split[1]
            print(user_info)
            user_info.append(output_dict)

# with app.app_context():
#     for user in user_info:
#         hashed_password = flask_bcrypt.generate_password_hash(
#             user["PASSWORD"]
#         )
#         new_user = User(
#             username=user["USERNAME"],
#             password=hashed_password,
#             secretkey=secrets.token_hex(32),
#             apikey=secrets.token_hex(64)
#         )
#         db.session.add(new_user)
#     db.session.commit()

with app.app_context():
    print(str(db.session.query(User).all()))
