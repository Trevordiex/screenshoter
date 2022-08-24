from base import BaseTweetImage
from io import BytesIO
# from mock import post

class TweetImage(BaseTweetImage):

    def __init__(self, post):
        super().__init__(post, media=True)

    def process(self):
        image_width,image_height = self.image.size

        #draw a white background polygon to cover the canvas
        self.canvas.polygon(
            [(0,0),(image_width,0),(image_width,image_height),(0,image_height)],
            fill = self.BLACK
        )
        
        #add header
        user = {
            'name': self.post['name'],
            'username': self.post['username'],
            'image': self.post['image']
        }

        text = self.post['text']
        if self.post['media']:
            h = self.post['media'].size[1]
            ycord = (self.image_size[1] - (self.text_height(text) + self.LOGO_SIZE[1] + h + self.PADDING)) // 2
        else:
            ycord = (self.image_size[1] - (self.text_height(text) + self.LOGO_SIZE[1] + self.PADDING)) // 2

        self.cursor = self.PADDING, ycord
        self.add_header(user, qrcode=True)
            
        #paste tweet
        ycord += self.QRCODE_SIZE[1] + self.PADDING
        self.cursor = self.PADDING, ycord
        
        ycord = self.paste_tweet(text)

        if self.post['media']:
            self.add_photo()

        # #add footer to the image
        ycord = self.add_footer()

        # self.image.show()
            
        pic = BytesIO()
        self.image.save(pic, format='PNG')
        return pic
