import logging
import traceback
from flask_restplus import Api
from sqlalchemy.orm.exc import NoResultFound
from flask import request, json, abort, current_app, _app_ctx_stack
from functools import wraps


log = logging.getLogger(__name__)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'item': 'X-API-TOKEN'
    }
}


def auth_required(func):
    func = api.doc(security='apikey')(func)

    @wraps(func)
    def check_auth(*args, **kwargs):
        if 'X-API-TOKEN' not in request.headers:
            responseObject = {
                'status': 'fail',
                'message': 'Authorization token required'
            }
            abort(401, responseObject)
        token = request.headers['X-API-TOKEN']
        auth_token = 'Bearer ' + token
        from src.api.auth.business import auth_status
        res = auth_status(auth_token)
        resobj = json.dumps(res)
        resjson = json.loads(resobj)
        status_code = resjson[-1]
        data = resjson[0]
        if data['status'] == 'success':
            with current_app.app_context():
                ctxapp = _app_ctx_stack
                ctxapp.user_data = data['data']
            return func(*args, **kwargs)

        responseObject = {
            'status': data['status'],
            'message': data['message']
        }
        abort(status_code, responseObject)
    return check_auth


api = Api(version='1.0', title='E- Commerce Rest API',
          description='API for CRUD E-commerce services', validate=True, doc='/doc/',
          authorizations=authorizations)


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not current_app.config['DEBUG']:
        return {'message': message}, 500


@api.errorhandler(NoResultFound)
def database_not_found_error_handler(e):
    log.warning(traceback.format_exc())
    return {'message': 'A database result was required but none was found.'}, 404
