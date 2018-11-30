from flask import Flask, redirect, url_for, session, request, jsonify
from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
from flask_oauthlib.client import OAuth

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'development'

    oauth = OAuth(app)
    github = oauth.remote_app(
        'github',
        consumer_key='2188276e979471fccaed',
        consumer_secret='ef3a4a718b70989c9715878f6a06e283bac0e7e0',
        request_token_params={'scope': 'user:email'},
        base_url='http://localhost:5000/tweets',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize'
    )

    from config import Config
    app.config.from_object(Config)
    db.init_app(app)

    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).filter_by(api_key=user_id).first()

    @app.route('/hello')
    def hello():
        return "Goodbye World!"

    @app.route('/')
    def index():
        if 'github_token' in session:
            me = github.get('user')
            return jsonify(me.data)
        return redirect(url_for('login'))


    @app.route('/login')
    def login():
        return github.authorize(callback=url_for('authorized', _external=True))


    @app.route('/logout')
    def logout():
        session.pop('github_token', None)
        return redirect(url_for('index'))


    @app.route('/login/authorized')
    def authorized():
        resp = github.authorized_response()
        if resp is None or resp.get('access_token') is None:
            return 'Access denied: reason=%s error=%s resp=%s' % (
                request.args['error'],
                request.args['error_description'],
                resp
            )
        session['github_token'] = (resp['access_token'], '')
        me = github.get('user')
        return jsonify(me.data)


    @github.tokengetter
    def get_github_oauth_token():
        return session.get('github_token')

    from .apis.tweets import api as tweets
    api = Api()
    api.add_namespace(tweets)
    api.init_app(app)

    app.config['ERROR_404_HELP'] = False
    return app
