from src.models import db, UserModel, BlacklistToken
from src.api.auth.serializers import token_status
from flask_restplus import marshal


def create_user(data):
    user = UserModel.query.filter_by(email=data.get('email')).first()
    if not user:
        try:
            user = UserModel(
                email=data.get('email'),
                password=data.get('password')
            )
            db.session.add(user)
            db.session.commit()
            # generate the auth token
            auth_token = user.encode_auth_token(user.id)
            responseObject = {
                'status': 'success',
                'message': 'Successfully registered.',
                'auth_token': auth_token.decode()
            }
            return responseObject, 201
        except Exception as e:
            responseObject = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.'
            }
            return responseObject, 401
    else:
        responseObject = {
            'status': 'fail',
            'message': 'User already exists. Please Log in.',
        }
        return responseObject, 202


def login_user(data):
    try:
        from src.app import bcrypt
        # fetch the user data
        user = UserModel.query.filter_by(email=data.get('email')).first()
        if user and bcrypt.check_password_hash(user.password, data.get('password')
                                               ):
            auth_token = user.encode_auth_token(user.id)
            if auth_token:
                responseObject = {
                    'status': 'success',
                    'message': 'Successfully logged in.',
                    'auth_token': auth_token.decode()
                }
                return responseObject, 200
        else:
            responseObject = {
                'status': 'fail',
                'message': 'User does not exist.'
            }
            return responseObject, 401
    except Exception as e:
        print(e)
        responseObject = {
            'status': 'fail',
            'message': 'Try again'
        }
        return responseObject, 500


def auth_status(auth_header):
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''
    if auth_token:
        resp = UserModel.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            user = UserModel.query.filter_by(id=resp).first()
            responseObject = {
                'status': 'success',
                'data': {
                    'user_id': user.id,
                    'email': user.email,
                    'admin': user.admin,
                    'registered_on': user.registered_on
                }
            }
            # import pdb;pdb.set_trace()
            return marshal(responseObject, token_status), 200
        responseObject = {
            'status': 'fail',
            'message': resp
        }
        return responseObject, 401
    else:
        responseObject = {
            'status': 'fail',
            'message': 'Provide a valid auth token.'
        }
        return responseObject, 401


def logout(auth_header):
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''
    if auth_token:
        resp = UserModel.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            # mark the token as blacklisted
            blacklist_token = BlacklistToken(token=auth_token)
            try:
                # insert the token
                db.session.add(blacklist_token)
                db.session.commit()
                responseObject = {
                    'status': 'success',
                    'message': 'Successfully logged out.'
                }
                return responseObject, 200
            except Exception as e:
                responseObject = {
                    'status': 'fail',
                    'message': e
                }
                return responseObject, 200
        else:
            responseObject = {
                'status': 'fail',
                'message': resp
            }
            return responseObject, 401
    else:
        responseObject = {
            'status': 'fail',
            'message': 'Provide a valid auth token.'
        }
        return responseObject, 403
