"""Application factory"""

import os

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'todor.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # prosta strona powitania
    @app.route('/hello')
    def hello():
        return 'Witaj!'

    # import i inicjacja bazy danych
    from . import db
    db.init_app(app)

    # import i rejestracja blueprinta auth
    from . import auth
    app.register_blueprint(auth.bp)

    # import i rejestracja blueprinta blog
    from . import zadania
    app.register_blueprint(zadania.bp)
    app.add_url_rule('/', endpoint='index')

    return app

# export FLASK_APP=todor
# export FLASK_ENV=development
# flask init-db
# flask run