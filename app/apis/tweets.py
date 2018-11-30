from flask_restplus import Namespace, Resource, fields
from flask import abort, request
from app.models import Tweet, User
from app import db
import pdb

api = Namespace('tweets')

class JsonUser(fields.Raw):
    def format(self, value):
        return {
            'username': value.username,
            'email': value.email
        }

json_tweet = api.model('Tweet', {
    'id': fields.Integer,
    'text': fields.String,
    'created_at': fields.DateTime,
    'user': JsonUser
})

json_new_tweet = api.model('New tweet', {
    'text': fields.String(required=True)
})

@api.route('/<int:id>')
@api.response(404, 'Tweet not found')
@api.param('id', 'The tweet unique identifier')
class TweetResource(Resource):
    @api.marshal_with(json_tweet)
    def get(self, id):
        tweet = db.session.query(Tweet).get(id)
        if tweet is None:
            api.abort(404, "Tweet {} doesn't exist".format(id))
        else:
            return tweet

    @api.marshal_with(json_tweet, code=200)
    @api.expect(json_new_tweet, validate=True)
    def patch(self, id):
        tweet = db.session.query(Tweet).get(id)
        #pdb.set_trace() #ll in server + ... + continue
        api_key = request.args.get('api_key')
        if tweet is None:
            api.abort(404, "Tweet {} doesn't exist".format(id))

        if api_key is None or api_key != tweet.user.api_key:
            abort(401, "Not owner of the tweet")

        tweet.text = api.payload["text"]
        db.session.commit()
        return tweet

    def delete(self, id):
        tweet = db.session.query(Tweet).get(id)
        if tweet is None:
            api.abort(404, "Tweet {} doesn't exist".format(id))
        api_key = request.args.get('api_key')

        if api_key is None or api_key != tweet.user.api_key:
            abort(401, "Not owner of the tweet")

        db.session.delete(tweet)
        db.session.commit()
        return None

@api.route('')
class TweetsResource(Resource):
    @api.marshal_with(json_tweet, code=201)
    @api.expect(json_new_tweet, validate=True)
    @api.response(422, 'Invalid tweet')
    def post(self):
        api_key = request.args.get('api_key')
        user = db.session.query(User).filter_by(api_key=api_key).first()
        if user == None:
            return abort(401, "Unknown user")

        text = api.payload["text"]
        if len(text) > 0:
            tweet = Tweet(text=text)
            tweet.user_id = user.id
            db.session.add(tweet)
            db.session.commit()
            return tweet, 201
        else:
            return abort(422, "Tweet text can't be empty")

    @api.marshal_list_with(json_tweet)
    def get(self):
        tweets = db.session.query(Tweet).all()
        return tweets
