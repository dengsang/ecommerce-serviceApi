from src.models import db
from flask_restful import Resource, reqparse, inputs
from flask_jwt import jwt_required
from src.models import ProductModel, PurchaseLogModel
from flask import abort, current_app, _app_ctx_stack
from sqlalchemy import desc
from math import ceil
from functools import wraps
from flask_jwt import current_identity
from flask_restplus import marshal
from src.api.productsCRUD.serializers import productlist as productlist_fields
from src.api.productsCRUD.serializers import productlist_item_output


def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_identity.role == 'admin':
                return fn(*args, **kwargs)
            return {
                       'message': 'User has not permission to perform this operation'
                   }, 403

        return decorator

    return wrapper


def log_purchase():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            fn_response = fn(*args, **kwargs)
            if fn_response.get('successful_purchase'):
                log = PurchaseLogModel(current_identity, *args)
                log.save_to_db()
            return fn_response

        return decorator

    return wrapper


class ProductBuy(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('quantity', type=inputs.positive, required=True)

    @jwt_required()
    def patch(self, _id):
        kwargs = ProductBuy.parser.parse_args()
        data = ProductService.buy_product(_id, kwargs.get('quantity'))

        if data.get('not_found'):
            return data, 404
        elif data.get('stock_not_enough'):
            return data, 200
        elif data.get('error'):
            return data, 500

        return data, 200


class ProductLike(Resource):

    @jwt_required()
    def patch(self, _id):

        data = ProductService.give_like_product(_id)

        if data.get('not_found'):
            return data, 404
        elif data.get('error'):
            return data, 500

        return data, 200


class ProductList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('orderBy', type=str, action='append')
    parser.add_argument('searchByName', type=str)
    parser.add_argument('page', type=inputs.positive, required=True,
                        help="page field cannot be left blank!")
    parser.add_argument('per_page', type=inputs.positive, required=True,
                        help="per_page field cannot be left blank!")

    def get(self):
        kwargs = ProductList.parser.parse_args()
        order_by = kwargs.get('orderBy')
        search_by = kwargs.get('searchByName')
        page = kwargs.get('page')
        per_page = kwargs.get('per_page')

        data = ProductService.get_product_list(search_by, order_by,
                                               page, per_page)
        return data, 200


class Product(Resource):

    @jwt_required()
    @admin_required()
    def delete(self, _id):
        data = ProductService.delete_product(_id)

        if data.get('not_found'):
            return data, 404

        return data, 200

    @jwt_required()
    @admin_required()
    def patch(self, _id):

        parser = reqparse.RequestParser()
        parser.add_argument('item', type=str)
        parser.add_argument('npc', type=str)
        parser.add_argument('stock', type=inputs.positive)
        parser.add_argument('price', type=float)
        data = parser.parse_args()

        data = ProductService.update_product(_id, **data)

        if data.get('not_found'):
            return data, 404
        elif data.get('error'):
            return data, 500

        return data, 200

    def get(self, _id):
        data = ProductService.get_product(_id)
        if data.get('not_found'):
            return data, 404

        return data, 200

    @jwt_required()
    @admin_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('item', type=str, required=True,
                            help="item field cannot be left blank!")
        parser.add_argument('npc', type=str, required=True,
                            help="npc field cannot be left blank!")
        parser.add_argument('stock', type=inputs.positive, required=True,
                            help="stock field cannot be left blank!")
        parser.add_argument('price', type=float, required=True,
                            help="price field cannot be left blank!")
        data = parser.parse_args()

        data = ProductService.create_product(**data)
        if data.get('exists'):
            return data, 400
        elif data.get('error'):
            return data, 500

        return data, 201


class ProductService:

    @staticmethod
    def get_product_list(search_by, order_by, page, per_page):
        sorting = []

        if order_by:
            for field in order_by:
                if field == 'likes':
                    field = desc(field)
                    sorting.append(field)
        else:
            sorting.append('item')  # default order only by item
        order_by = sorting

        pagination = {'page': page, 'per_page': per_page}

        if search_by:
            products = ProductModel.find_by_name(search_by, *order_by, **pagination)
        else:
            products = ProductModel.all_items(*order_by, **pagination)

        total_pages = ceil(products.total / per_page)
        link = '/products?page={}&per_page={}'
        prev_page = page - 1 if page > 1 else 1
        next_page = page + 1 if page < total_pages else total_pages

        return {
            'metadata': {
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_products': products.total,
                'links': {
                    'self': link.format(page, per_page),
                    'first': link.format(1, per_page),
                    'prev': link.format(prev_page, per_page),
                    'next': link.format(next_page, per_page),
                    'last': link.format(total_pages, per_page)
                }
            },
            'products': tuple(map(ProductModel.to_dict, products.items))
        }

    @staticmethod
    @log_purchase()
    def buy_product(_id, quantity):
        product = ProductModel.find_by_id(_id)

        if not product:
            return {'not_found': 'Product not found'}

        if product.stock < quantity:
            return {'stock_not_enough': {'current_stock': product.stock}}

        product.stock -= quantity

        try:
            product.save_to_db()
        except:
            return {'error': 'An error occurred buying a product.'}

        return {
            'successful_purchase': {
                'product': {
                    'id': product.id,
                    'item': product.name,
                    'npc': product.npc,
                    'current_stock': product.stock,
                    'price': product.price
                },
                'purchase_quantity': quantity
            }
        }

    @staticmethod
    def give_like_product(_id):
        product = ProductModel.find_by_id(_id)
        if not product:
            return {'not_found': 'Product not found'}

        product.likes += 1

        try:
            product.save_to_db()
        except:
            return {"error": "An error occurred giving a like to the product."}

        return product.to_dict()

    @staticmethod
    def create_product(*args, **data):
        product = ProductModel.find_by_name(data.get('item')).items
        if product:
            return {'exists':
                        "A product with item '{}' already exists."
                            .format(data.get('item'))}
        try:
            product = ProductModel(data.get('item'),
                                   data.get('npc'),
                                   data.get('stock'),
                                   data.get('price'))
            product.save_to_db()
        except:
            return {"error": "An error occurred inserting the product."}

        return product.to_dict()

    @staticmethod
    def delete_product(_id):
        product = ProductModel.find_by_id(_id)
        if not product:
            return {'not_found': 'Product not found'}

        product.delete_from_db()
        return {'ok': 'Product deleted'}

    @staticmethod
    def update_product(_id, *args, **data):
        product = ProductModel.find_by_id(_id)
        if not product:
            return {'not_found': 'Product not found'}

        name = data.get('item')
        npc = data.get('npc')
        stock = data.get('stock')
        price = data.get('price')

        if name:
            product.name = name
        if npc:
            product.npc = npc
        if stock:
            product.stock = stock
        if price:
            product.price = price

        try:
            product.save_to_db()
        except:
            return {"error": "An error occurred updating the product."}

        return product.to_dict()

    @staticmethod
    def get_product(_id):
        product = ProductModel.find_by_id(_id)
        if not product:
            return {'not_found': 'Product not found'}

        return product.to_dict()


def create_product_item(_id, data):
    name = data.get('item')
    npc = data.get('npc')
    stock = data.get('stock')
    price = data.get('price')
    product_id = id
    product_item = ProductModel(name, npc, stock, price, product_id)
    if ProductModel.query.filter_by(id=id).first() is not None:
        db.session.add(product_item)
        db.session.commit()
        responseObject = {
            'status': 'success',
            'message': 'Products item successfully created.',
            'Productlist_item': marshal(product_item, productlist_item_output)
        }
        return responseObject
    else:
        abort(404, 'Bucketlist not found')


def update_item(id, item_id, data):
    name = data.get('item')
    if not name.strip():
        abort(400, {"message": "Input payload validation failed",
                    "field": "'item' is a required property"})
    with current_app.app_context():
        user_data = _app_ctx_stack.user_data
        created_by = user_data['user_id']
    try:
        item = ProductModel.query.filter_by(
            created_by=created_by, id=id).first().items.filter_by(id=item_id).first_or_404()

        item.name = name
        item.likes = data.get('likes')
        db.session.add(item)
        db.session.commit()
        responseObject = {
            'status': 'success',
            'message': 'Productlist item successfully updated.',
            'productlist_item': marshal(item, productlist_item_output)
        }
        return responseObject
    except Exception:
        abort(400)


def delete_item(id, item_id):
    with current_app.app_context():
        user_data = _app_ctx_stack.user_data
        created_by = user_data['user_id']
    item = ProductModel.query.filter_by(
        created_by=created_by, id=id).first().items.filter_by(id=item_id)
    if not item.count():
        abort(403)
    db.session.delete(item.first_or_404())
    db.session.commit()
    responseObject = {
        'status': 'success',
        'message': 'Item successfully deleted.'
    }
    return responseObject


def create_productlist(data):
    name = data.get('item')
    if not name.strip():
        abort(400, {"message": "Input payload validation failed",
                    "field": "'item' is a required property"})
    with current_app.app_context():
        user_data = _app_ctx_stack.user_data
        created_by = user_data['user_id']
    products = ProductModel(name, created_by)
    db.session.add(products)
    db.session.commit()
    responseObject = {
        'status': 'success',
        'message': 'Productlist successfully created.',
        'productlist': marshal(products, productlist_fields)
    }
    return responseObject


def update_productlist(bucketlist_id, data):
    name = data.get('item')
    if not name.strip():
        abort(400, {"message": "Input payload validation failed",
                    "field": "'item' is a required property"})
    with current_app.app_context():
        user_data = _app_ctx_stack.user_data
        created_by = user_data['user_id']
    products = ProductModel.query.filter_by(created_by=created_by, id=bucketlist_id).first_or_404()
    products.name = name
    db.session.add(products)
    db.session.commit()
    responseObject = {
        'status': 'success',
        'message': 'ProductsList successfully updated.',
        'productlist': marshal(products, productlist_fields)
    }
    return responseObject


def delete_productlist(b_id):
    with current_app.app_context():
        user_data = _app_ctx_stack.user_data
        created_by = user_data['user_id']
    products = ProductModel.query.filter_by(created_by=created_by, id=b_id)
    if not products.count():
        abort(403)
    db.session.delete(products.first_or_404())
    db.session.commit()
    responseObject = {
        'status': 'success',
        'message': 'Product item successfully deleted.'
    }
    return responseObject
