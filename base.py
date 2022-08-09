from PIL import Image, ImageFont, ImageDraw, ImageChops, ImageOps
import textwrap
# from io import BytesIO, FileIO
# from collections import namedtuple
# from utils import fmt
# from mock import post
from utils import make_qrcode, round_corners





class BaseTweetImage:
    '''A class to transform a tweet post into an image
    
    '''

    IMAGE_SIZE = (500,350)
    LOGO_SIZE = (35, 35)
    PADDING = 15
    LINE_SPACING = 2
    ICON_SIZE = (12, 12)
    QRCODE_SIZE = (50, 50)
    TEXT_FONT_SIZE = 18
    CHAR_PER_LINE=52
    CHAR_PER_LINE_SIMPLE=65
    FONTS = {
        'text': ImageFont.truetype('static/fonts/weather/weather.ttf', 18),
        'simple_text': ImageFont.truetype('static/fonts/Abel/Abel-Regular.ttf', 18),
        'name': ImageFont.truetype('static/fonts/Kreon/Kreon-VariableFont_wght.ttf', 16),
    }

    def __init__(self, post, *, roll=False, media=False):
        self.post = post
        self.image_size = self.get_image_size(post, roll=roll)

        if media and self.post['media']:
            im = Image.open(self.post['media'])
            size = self.IMAGE_SIZE[0] - (2*self.PADDING), im.size[1]
            photo = ImageOps.contain(im, size)
            self.post['media'] = photo

            h = photo.size[1]
            self.image_size = self.image_size[0], self.image_size[1] + h + self.PADDING

        self.image = Image.new('RGBA', self.image_size, (255,255,255,255))
        self.canvas = ImageDraw.Draw(self.image)
        self.cursor = (0,0)

    def add_header(self, user,*, qrcode=False):
        """add_header(
                user: {name: str, username: str, image: File}, cords: (x,y)
            )
            Adds a header to the image

            Parameters
            ------------
            image
                An image instance to operate on. This is the same image instance used on the canvas
            canvas
                An instance of ImageDraw to draw on.
            user
                A dictionary containing name, username and image
            cords
                The cordinates for the header

            returns
            -------
            :file: `~PIL.Image` 
        """

        # paste the username and name at the upper left just to the right of profile picture
        name = user['name']
        username = user['username']
        font = self.FONTS['name']
        text_height = font.getsize(name)[1]
        
        self.cursor = (self.PADDING, self.cursor[1])

        profile_pic = self.create_round_thumbnail(user['image'])
        self.image.paste(profile_pic, self.cursor, mask=profile_pic)
        self.cursor = (
            self.cursor[0] + self.LOGO_SIZE[0] + self.PADDING,
            self.cursor[1] + self.LOGO_SIZE[0]/2 - (text_height + 1)
        )

        self.canvas.text(self.cursor, name,font = font,fill = (0,0,0,255))
        self.cursor = self.cursor[0], self.cursor[1] + text_height + 2
        self.canvas.text(self.cursor,f'@{username}', font = font, fill = (0,0,0,255))
        
        #paste the qrcode to the upper right of the canvas
        if qrcode:
            url = self.post['url'] if not isinstance(self.post, list) else self.post[0]['url']
            qrcode = make_qrcode(url, user['image'])
            qrcode = qrcode.convert('RGBA').resize(self.QRCODE_SIZE)
            icon_cord = self.image_size[0] - (self.QRCODE_SIZE[0] + self.PADDING)
            self.image.paste(qrcode, (icon_cord, self.PADDING))

            self.cursor = self.cursor = self.cursor[0], self.cursor[1] + text_height
        return self.cursor[1]


    

    def paste_tweet(self, tweet):
        """paste_tweet(
            self, canvas, tweet, cords, font, *, width
        )

         pastes a tweet on a canvas the given cordinates

         parameters
         -----------
        canvas
            An instance of ImageDraw where the text is to be drawn
        tweet
            The tweet text to be pasted
        cords
            A tuple of x,y cordinates where the tweet is to be printed
        font
            An instance of ImageFont to be used 
        width
            the width of text used with textwrap to split lines. defaults to 70 if not provided

        returns
        --------
        :int:
        """
        canvas = self.canvas
        text_lines = textwrap.wrap(tweet, width = self.CHAR_PER_LINE)
        xcord, ycord = self.cursor
        font = self.FONTS['text']


        for line in text_lines:
            line_width, line_height = font.getsize(line)
            xcord = self.PADDING
            canvas.text((xcord, ycord),line,font = font,fill = (0,0,0,255))		
            ycord += line_height
            ycord += self.LINE_SPACING
        self.cursor = xcord, int(ycord)
        return ycord

    def add_photo(self):
        if not self.post['media']:
            return
        
        photo = self.post['media']
        cords = self.PADDING, self.cursor[1] + self.PADDING

        self.image.paste(photo, cords)
        self.cursor = 0, cords[1] + photo.size[1]



    def add_footer(self):
        """add_footer(
            canvas, metrics, cords
        )
        Adds a footer containing the public metrics at a given cordinates.
        
        parameters
        ----------
        canvas
            An instance of ImageDraw to draw on
        metrics
            a dictionary containing public likes, comments, retweets
        cords
            The cordinates where the footer should be added

        returns
        -------
        :int:
        """
    

        font = self.FONTS['text']
        brand_text = '@prettiercam'
        text_width, text_height = font.getsize(brand_text)
        xcord = self.image_size[0] - (text_width + self.PADDING)
        ycord = self.image_size[1] - (self.PADDING + text_height)
        self.canvas.text((xcord, ycord - 10), brand_text, font = font,fill = (100,100,255,255))

        return ycord

    
    def create_round_thumbnail(self, image):
        #convert post logo into a circular thumbnail
        post_logo = Image.open(image).convert('RGBA').resize(self.LOGO_SIZE)
        bigsize = (post_logo.width * 3, post_logo.height * 3)
        mask = Image.new('L', bigsize, 0)
        ImageDraw.Draw(mask).ellipse((0,0) + bigsize, fill=255)
        mask = mask.resize(post_logo.size, Image.ANTIALIAS)
        mask = ImageChops.darker(mask, post_logo.split()[-1])
        post_logo.putalpha(mask)
        return post_logo

    @classmethod
    def text_height(cls, post):
        post_height = 0
        lines = textwrap.wrap(post, width=cls.CHAR_PER_LINE)
        font = cls.FONTS['text']
        w,h = font.getsize(lines[0])
        for line in lines:
            post_height += h
            post_height += cls.LINE_SPACING
        return post_height

    @classmethod
    def get_image_size(cls, posts, roll):
        height = 0
        #add top header
        height += cls.QRCODE_SIZE[1]

        if isinstance(posts, list):
            if not roll:
                for post in posts:
                    height += cls.text_height(post['text'])
                    height += cls.PADDING
            else:
                for post in posts:
                    height += cls.text_height(post['text'])
                    height += cls.QRCODE_SIZE[1]
        else:
            height += cls.text_height(posts['text'])
            height += cls.PADDING

        #add footer to height
        height += cls.PADDING + 40

        return (cls.IMAGE_SIZE[0], max(height, 320))
    


    def process(self, post):
        pass