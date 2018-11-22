import logging
from flask import request
from flask_restplus import Resource
from src.api.auth.serializers import login
from src.api.restplus import api
from src.api.auth.business import create_user, auth_status, logout, login_user
from src.api.auth.serializers import new_user
from src.api.restplus import auth_required

log = logging.getLogger(__name__)

ns = api.namespace('auth', description='Operations related to User login')


@ns.route('/login')
class UserLogin(Resource):
    @api.response(200, 'User authorized.')
    @api.expect(login)
    def post(self):
        """
        Verify User.
        """
        data = request.json
        return login_user(data)


@ns.route('/status')
class UserCollection(Resource):
    @api.response(200, 'User authorized.')
    @auth_required
    def get(self):
        """
        Verify Token Status.
        """
        token = request.headers['X-API-TOKEN']
        auth_header = 'Bearer ' + token
        return auth_status(auth_header)


@ns.route('/register')
class UserRegister(Resource):

    @api.response(202, 'User already exists. Please Log in.')
    @api.response(201, 'User successfully created.')
    @api.expect(new_user)
    def post(self):
        """
        Create a new User.
        """
        data = request.json
        return create_user(data)


@ns.route('/logout')
class UserLogout(Resource):
    @api.response(200, 'Successfully logged out')
    @auth_required
    def post(self):
        """
        Logout user using token provided.
        """
        token = request.headers['X-API-TOKEN']
        auth_header = 'Bearer ' + token
        return logout(auth_header)
