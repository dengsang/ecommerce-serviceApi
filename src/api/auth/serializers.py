from flask_restplus import fields
from src.api.restplus import api
EMAIL_REGEX = r'\S+@\S+\.\S+'


new_user = api.model('User Register', {

    'email': fields.String(description="user email address", example='email@domain.com',
                           required=True, pattern=EMAIL_REGEX),
    'password': fields.String(required=True, description='User password', example='password')
})

login = api.model('User Login', {
    'email': fields.String(required=True, description='Username', example='email@domain.com',
                           pattern=EMAIL_REGEX),
    'password': fields.String(required=True, description='password', example='password'),
})

auth_header = api.model('Authorization header', {
    'Authorization': fields.String(required=True, description='Authorization token',
                                   location='head')
})

user_data = api.model('User details', {
    'user_id': fields.Integer(description='user id'),
    'email': fields.String(description='user email address'),
    'admin': fields.Boolean(description='if user is admin'),
    'registered_on': fields.DateTime(dt_format='rfc822')

})

token_status = api.model('Token status', {
    'status': fields.String(description='token status', example='success'),
    'data': fields.Nested(user_data)
})