from flask_restplus import fields
from src.api.restplus import api

productlist_item = api.model('Productlist Item', {
    'item': fields.String(required=True, description='Productlist item item', example='Jump to the '
                                                                                     'peak'),
    'likes': fields.Boolean(required=True, example=True)
})

productlist_item_output = api.inherit('Productlist item output', productlist_item, {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a Bucketlist item'),
    'date_modified': fields.DateTime(description='date modified'),
    'date_created': fields.DateTime,

})

pagination = api.model('A page of results', {
    'page': fields.Integer(description='Number of this page of results'),
    'pages': fields.Integer(description='Total number of pages of results'),
    'per_page': fields.Integer(description='Number of items per page of results'),
    'total': fields.Integer(description='Total number of results'),
})

productlist_input = api.model('Productlist', {
    'item': fields.String(required=True, description='Productlist item', example='Climb Mountain')

})

productlist = api.model('Productlist', {
    'id': fields.Integer(readOnly=True, nullable=False, description='The unique identifier of a  '
                                                                    'Productlist'),
    'item': fields.String(required=True, description='Productlist item', example='Climb Mountain'),
    'date_created': fields.DateTime,
    'date_modified': fields.DateTime,
    'created_by': fields.Integer(required=True, example=1)

})

productlist_with_items = api.inherit('Productlist with items', productlist, {
    'items': fields.List(fields.Nested(productlist_item_output)),
    'date_modified': fields.DateTime

})

page_of_productlist = api.inherit('Page of productlist', pagination, {
    'items': fields.List(fields.Nested(productlist_with_items))
})

page_of_product_items = api.inherit('Page of productlist item', productlist,
                                    pagination,
                                    {'items': fields.List(fields.Nested(productlist_item_output))
})
