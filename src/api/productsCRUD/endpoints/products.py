import logging

from flask import request
from flask_restplus import Resource

from src.api.productsCRUD.business import create_productlist, delete_productlist, \
    update_productlist
from src.api.productsCRUD.serializers import productlist, \
    productlist_item, page_of_productlist, page_of_product_items, productlist_input
from src.api.productsCRUD.business import create_product_item, update_item, delete_item
from src.api.restplus import api
from src.models import ProductList
from src.api.productsCRUD.parsers import pagination_arguments, search_argument
from src.api.restplus import auth_required
from flask import abort, current_app, _app_ctx_stack

log = logging.getLogger(__name__)

ns = api.namespace('productsCRUD', description='Operations related to Products')


@ns.route('/')
class ProductListCollection(Resource):

    @api.expect(pagination_arguments, search_argument, productlist)
    @api.marshal_with(page_of_productlist)
    @auth_required
    def get(self):
        """
        List all the created items list.
        """
        search_args = search_argument.parse_args(request)
        args = pagination_arguments.parse_args(request)
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        search_term = search_args.get('q')
        with current_app.app_context():
            user_data = _app_ctx_stack.user_data
        if search_term:
            search_query = ProductList.query.filter_by(created_by=user_data[
                'user_id'], name=search_term)

            if search_query.count():
                productlists = search_query.paginate(page, per_page, error_out=False)
                return productlists, 200
            abort(404, 'productlist not found')
        else:
            productlist_query = ProductList.query.filter_by(created_by=user_data['user_id'])
            productlists = productlist_query.paginate(page, per_page, error_out=False)
            return productlists, 200

    @api.response(201, 'Productlist successfully created.')
    @api.expect(productlist_input, validate=True)
    @auth_required
    def post(self):
        """
        Create a new bucket list.
        """
        data = request.json
        return create_productlist(data), 201


@ns.route('/<int:id>')
@api.param('id', 'Productlist ID')
@api.response(404, 'Productlist Item not found.')
class ProductList(Resource):

    @api.expect(pagination_arguments, productlist)
    @api.marshal_with(page_of_product_items)
    @auth_required
    def get(self, id):
        """
        Get single bucket list.
        """
        args = pagination_arguments.parse_args(request)
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        with current_app.app_context():
            user_data = _app_ctx_stack.user_data
            created_by = user_data['user_id']
        try:
            productlist_query = ProductList.query.filter_by(created_by=created_by, id=id)
            if not productlist_query.count():
                abort(404)
            product_items = productlist_query[0].items
            productlist_items_paginated = product_items.paginate(page, per_page, error_out=False)
            productlist_items_paginated.date_modified = productlist_query[0].date_modified
            productlist_items_paginated.created_by = productlist_query[0].created_by
            productlist_items_paginated.id = productlist_query[0].id
            productlist_items_paginated.date_created = productlist_query[0].date_created
            productlist_items_paginated.name = productlist_query[0].name
            return productlist_items_paginated
        except Exception as e:
            abort(404, str(e))

    @api.expect(productlist_input, productlist)
    @api.response(204, 'Productlist item successfully updated.')
    @auth_required
    def put(self, id):
        """
        Update this product list.
        * Specify the ID of the productlist to modify in the request URL path.
        """
        data = request.json
        return update_productlist(id, data), 200

    @api.response(204, 'ProductList item successfully deleted.')
    @auth_required
    def delete(self, id):
        """
        Delete this single bucket list.
        """

        return delete_productlist(id), 204


@ns.route('/<int:id>/item/')
@api.param('id', 'Productlist id')
@api.response(201, 'Productlist item successfully created.')
class ProductItemsCollection(Resource):

    @api.expect(productlist_item, productlist)
    @auth_required
    def post(self, id):
        """
        Create a new item in bucket list.
        """

        return create_product_item(id, request.json), 201


@ns.route('/<int:id>/item/<int:item_id>')
@api.param('item_id', 'Productlist Item ID')
@api.param('id', 'Productlist ID')
@api.response(404, 'Item not found.')
class ProductlistItem(Resource):

    @api.expect(productlist_item, productlist)
    @api.response(200, 'Item successfully updated.')
    @auth_required
    def put(self, id, item_id):
        """
        Update a product list item.
        """
        data = request.json
        return update_item(id, item_id, data), 200

    @api.response(204, 'Item successfully deleted.')
    @auth_required
    def delete(self, id, item_id):
        """
        Delete an item in a product list.
        """

        return delete_item(id, item_id), 204
