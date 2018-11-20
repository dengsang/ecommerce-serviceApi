import logging.config
import os

from flask import Flask, Blueprint
# from flask_restful import Api
# from src.api.productsCRUD.endpoints.products import ProductList
# from src.api.productsCRUD.business import Product, ProductBuy, ProductLike, ProductList
from src.api.productsCRUD.endpoints.products import ns as productsCRUD_namespace
from src.api.auth.endpoints.user_profile import ns as auth_namespace
from src.api.restplus import api
from src.models import db
from flask_mail import Mail
from flask_bcrypt import Bcrypt

app = Flask(__name__)
logging.config.fileConfig('logging.conf')
app.config.from_pyfile('config.py')
log = logging.getLogger(__name__)
mail = Mail()
bcrypt = Bcrypt(app)


def configure_app(flask_app):
    flask_app.config.from_object(os.environ['APP_SETTINGS'])


def initialize_app(flask_app):
    configure_app(flask_app)

    blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
    api.init_app(blueprint)
    api.add_namespace(auth_namespace)
    api.add_namespace(productsCRUD_namespace)
    flask_app.register_blueprint(blueprint)
    mail.init_app(flask_app)
    db.init_app(flask_app)
    with flask_app.app_context():
        db.create_all()
    return flask_app


def main():
    initialize_app(app)
    log.info('>>>>> Starting development server at http://{}/api/v1/ <<<<<'.format(
        app.config['FLASK_SERVER_NAME']))
    app.run(debug=app.config['DEBUG'])


# api = Api(app)
# api.add_resource(Product, '/api/product', '/api/product/<int:_id>')
# api.add_resource(ProductList, '/api/products')
# api.add_resource(ProductLike, '/api/product/<int:_id>/like')
# api.add_resource(ProductBuy, '/api/product/<int:_id>/buy')
# api.add_resource(UserRegister, '/api/user/register')

if __name__ == '__main__':
    main()
