from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import datetime
import jwt

db = SQLAlchemy()


class ProductModel(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(80))
    npc = db.Column(db.String(80))
    stock = db.Column(db.Integer)
    price = db.Column(db.Float(precision=2))
    likes = db.Column(db.Integer, default=0)
    last_update = db.Column(db.DateTime)
    logs = db.relationship('PurchaseLogModel', lazy='dynamic')

    def __init__(self, item, npc, stock, price):
        self.item = item
        self.npc = npc
        self.stock = stock
        self.price = price

    def __repr__(self):
        return '< id: {} item: {} npc: {} stock: {} price: {} likes: {} last_update: {} logs: {}'.format(
            self.id, self.item, self.npc, self.stock, self.price, self.likes, self.last_update, self.logs
        )

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_name(cls, name, *order_by, **pagination):
        return cls.query.filter_by(name=name).order_by(*order_by).paginate(**pagination)

    @classmethod
    def all_items(cls, *order_by, **pagination):
        return cls.query.order_by(*order_by).paginate(**pagination)

    def to_dict(self):
        return {
            'id': self.id,
            'item': self.item,
            'npc': self.npc,
            'stock': self.stock,
            'price': self.price,
            'likes': self.likes,
            'last_update': str(self.last_update)
        }

    def save_to_db(self):
        self.last_update = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class PurchaseLogModel(db.Model):
    __tablename__ = 'purchase_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('UserModel')
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product = db.relationship('ProductModel')
    purchase_quantity = db.Column(db.Integer)
    datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, user, product_id, purchase_quantity):
        self.user = user
        self.product_id = product_id
        self.purchase_quantity = purchase_quantity

    def __repr__(self):
        return '< id: {} user_id: {} user: {} product_id: {} product: {} purchase_quantity: {} datetime: {}'.format(
            self.id, self.user_id, self.user, self.product_id, self.product, self.purchase_quantity, self.datetime
        )

    @classmethod
    def find_by_user(cls, user):
        return cls.query.filter_by(user=user).all()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_product(cls, product):
        return cls.query.filter_by(product=product).all()

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.username,
            'product': self.product.to_dict(),
            'datetime': str(self.datetime)
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80))
    password = db.Column(db.String(90))
    role = db.Column(db.String(50))
    logs = db.relationship('PurchaseLogModel', lazy='dynamic')

    def __init__(self, email, password, role):
        self.email = email
        self.password = password
        self.role = role

    def __repr__(self):
        return '< id: {} email: {} password: {} role: {} '.format(
            self.id, self.email, self.password, self.role
        )

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_username(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_role(cls, role):
        return cls.query.filter_by(role=role).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def encode_auth_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0,
                                                                       seconds=current_app.config[
                                                                           'PAYLOAD_EXPIRATION_TIME']),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Decodes the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, current_app.config.get('SECRET_KEY'))
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


class BlacklistToken(db.Model):
    """
        Token Model for storing JWT tokens
        """
    __tablename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False


class ProductList(db.Model):
    __tablename__ = 'productlist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80))
    items = db.relationship('ProductListItem', backref='productlist',
                            cascade='all, delete, delete-orphan', single_parent=True,
                            lazy='dynamic')
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    date_modified = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, name, created_by):
        self.name = name
        self.created_by = created_by

    def __repr__(self):
        return '< id: {} name: {} date_created: {} date_modified: {} created_by: {}'.format(
            self.id, self.name, self.date_created, self.date_modified, self.created_by
        )


class ProductListItem(db.Model):
    __tablename__ = 'productlistitem'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item = db.Column(db.String)
    productlist_id = db.Column(db.Integer, db.ForeignKey('productlist.id', ondelete='CASCADE'),
                               nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    date_modified = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow)
    likes = db.Column(db.Boolean)

    def __init__(self, name, producttlist_id, likes=False):
        self.item = name
        self.productlist_id = producttlist_id
        self.likes = likes

    def __repr__(self):
        return '<id: {} item: {} productlist_id: {} date_created: {} date_modified: {} done: {}'.format(
            self.id, self.item, self.productlist_id, self.date_created, self.date_modified, self.likes
        )
