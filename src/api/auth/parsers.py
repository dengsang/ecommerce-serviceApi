
from flask_restplus import reqparse

authorization_arguments = reqparse.RequestParser()
authorization_arguments.add_argument('Authorization', location='headers', type=str,
                                     required=True, help='Bearer authorization token')