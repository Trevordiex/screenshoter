from base import BaseTweetImage
# from mock import post, post2, post3
from io import BytesIO

# posts = [post, post2, post3]


class ThreadImage(BaseTweetImage):

    def __init__(self, post, roll= False):
        self.roll = roll
        super().__init__(post, roll=roll)

    def process(self):
        image_width,image_height = self.image.size

        #draw a white background polygon to cover the canvas
        self.canvas.polygon(
            [(0,0),(image_width,0),(image_width,image_height),(0,image_height)],
            fill = self.BLACK
            )
        posts = self.post
        post = posts[0]
        #add header
        user = {
            'name': post['name'],
            'username': post['username'],
            'image': post['image']
        }
        self.cursor = self.PADDING, self.PADDING
        self.add_header(user, qrcode=True)
            
        #compose tweets
        font =  self.FONTS['text']
        last_user = user['username']

        for post in posts:
            if self.roll and last_user != post['username']:
                self.cursor = self.cursor[0], self.cursor[1] + 20
                self.add_header({
                    'name': post['name'],
                    'username': post['username'],
                    'image': post['image']
                })
            self.cursor = (self.PADDING, self.cursor[1] + 20)
            text = post['text']
            self.paste_tweet(text)

        #add footer to the image
        
        self.add_footer()

        # self.image.show()
            
        pic = BytesIO()
        self.image.save(pic, format='PNG')
        return pic
