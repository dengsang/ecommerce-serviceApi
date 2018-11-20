import os
import coverage
from flask import g
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app import app
from src.models import db
app.config.from_object(os.environ['APP_SETTINGS'])
app.config.from_pyfile('config.py')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)
COV = coverage.coverage(
    branch=True,
    include='src/*',
    omit=[
        'src/models.py',
        'src/api/auth/endpoints/*',
        'src/api/productsCRUD/endpoints/*',
        'src/api/restplus.py',
        'src/app.py',
        'src/models.py'
    ]
)
COV.start()


@manager.command
def create_db():
    """Creates the db tables."""
    if 'db' not in g:
        g.db = db.create_all()

    return g.d


# db.create_all()


@manager.command
def drop_db():
    """Drops the db tables."""
    db.drop_all()


if __name__ == '__main__':
    manager.run()
