
import json
import random
import tweepy
import logging
from collections import deque
from post import TweetImage
import settings
import enum
from thread import ThreadImage
from utils import get_users, paginate, save_users, tweet_to_post

logger = logging.getLogger(__name__)

class Listener(tweepy.Stream):
    auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
    )

    class Type(enum.Enum):
        post=1
        thread=2
        roll=3

    def on_data(self, data):
        try:
            res = json.loads(data)
            tagger = res['user']['screen_name']

            #check if user is a follower
            users = get_users()
            if not tagger in users:
                userid = res['user']['id']
                friend_res = self.api.lookup_friendships(
                    screen_name=tagger,
                    user_id=[userid,]
                )
                is_follower = friend_res[0].is_followed_by
                if is_follower:
                    users.append(tagger)
                    save_users(users)
                else:
                    return

            target_tweet_id = res['in_reply_to_status_id']
            text = res['text']
            rang = res['display_text_range']
            command = text[rang[0]: rang[1]]
            post_type = self.parse(command)
            if not post_type:
                return
            
            post = self.process_tweet(target_tweet_id, post_type=post_type)
            #generate post if given a single post or generate thread if given list with atleast two posts
            if isinstance(post, list) and len(post) > 1:
                pages = []
                roll = False if post_type == self.Type.thread else True
                for item in paginate(post):
                    pages.append(ThreadImage(post = item, roll=roll).process())
                response = pages
            else:
                if isinstance(post, list):
                    post = post[0]
                response = TweetImage(post=post).process()

            #upload the image back to twitter mentioning the requester
            self.post_image(response, in_reply_to_status_id=target_tweet_id, tagger=tagger)
        except BaseException as e:
            logger.exception('An error occured: ')
            print("Error: ", e)

        return True

    def on_error(self, status):
        print(status)
        return True

    def process_tweet(self, tweet_id, post_type: Type):

        if post_type == self.Type.post:
            data = self.api.get_status(tweet_id, tweet_mode='extended')._json
            return tweet_to_post(data)
        elif post_type == self.Type.thread:
            return self.get_thread(tweet_id)
        elif post_type == self.Type.roll:
            return self.get_thread(tweet_id, roll=True)


    def get_thread(self, tweet_id, roll=False):
        #Recursively generate a thread for a tweetid. 
        tweets = []
        userid=0
        def get_tweet(tweet_id):
            data = self.api.get_status(tweet_id, tweet_mode='extended')._json
            user = data['user']
            if not roll and not tweets:
                nonlocal userid
                userid = user['id']
            elif not roll and user['id'] != userid:
                return
            tweets.append(tweet_to_post(data))
            next = data['in_reply_to_status_id']
            
            if next:
                get_tweet(next)
        
        get_tweet(tweet_id)
        tweets.reverse()
        return tweets


    def post_image(self, images, in_reply_to_status_id, tagger):
        if isinstance(images, list):
            media_ids = []
            for image in images:
                media_ids.append(self.upload_image(image))
        else:
            media_ids = [self.upload_image(images),]
        
        status = f'''Here is Your screenshot @{tagger}. Remember your commands: 
        1. capture
        2. capture thread
        3. capture roll -- for multi level thread.
        
        Also send a dm to @diexlabs to brand your screenshots for free. ♥ '''
        
        self.api.update_status(
            status,
            in_reply_to_status_id=in_reply_to_status_id,
            auto_populate_reply_metadata=True,
            media_ids=media_ids
        )
        return True

    def upload_image(self, image):
        image.seek(0)
        upload_res = self.api.media_upload(
            f'post-{random.randint(1,10)}.png',
            file=image,
            chunked=True
        )
        return upload_res.media_id

    def parse(self, command):
        if not command:
                return

        command = deque(command.split(" "))
        command.popleft()
        try:
            if len(command) >= 2:
                action = command.popleft()
                kind = command.popleft()
                if action.lower() == 'capture' and kind.lower() == 'post':
                    post_type = self.Type.post
                elif action.lower() == 'capture' and kind.lower() == 'thread':
                    post_type = self.Type.thread
                elif action.lower() == 'capture' and kind.lower() == 'roll':
                    post_type = self.Type.roll
                else:
                    return
            elif command[0].lower() == 'capture':
                post_type = self.Type.post

            return post_type
        except:
            return


stream = Listener(
    settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET,
    settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET
)




if not stream.running:
    print('********************************* Stream is about to start ***********************************')
    stream.filter(track=["@prettiercam"])
print('********************************* Stream is Running ***********************************')