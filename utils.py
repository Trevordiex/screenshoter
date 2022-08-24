import html
import requests
import re
from io import BytesIO
import qrcode
from PIL import Image, ImageDraw
from collections import deque
import json


def fmt(number):
    if number >= 1000000:
        return str(round(number/ 1000000, 1)) + 'M'
    elif number >= 1000:
        return str(round(number/ 1000, 1)) + 'K'
    return str(number)

def tweet_to_post(tweet):
    user = tweet['user']
    text = tweet['full_text']
    text = re.sub(r"https://t.co/\w+", "", text)
    text_list = deque(text.split(' '))
    while text_list[0].startswith('@'):
        text_list.popleft()

    text = html.unescape(' '.join(text_list))

    media = ''
    if 'media' in tweet['entities']:
        media_url = tweet['entities']['media'][0]['media_url_https']
        media = get_image(media_url)
    
    post = {
        'text': text,
        'name' : user['name'],
        'username' : user['screen_name'],
        'image': get_image(user['profile_image_url_https']),
        'url': f"https://twitter.com/{user['screen_name']}/status/{tweet['id']}",
        'media': media
    }
    return post

def get_image(url):
    req = requests.get(url, allow_redirects=True)
    return BytesIO(req.content)

def make_qrcode(url, logo):
    logo = Image.open(logo)
    basewidth = 100

    wpercent = (basewidth/float(logo.size[0]))
    hsize = int((float(logo.size[1])* float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
    QRcode = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    QRcode.add_data(url)
    QRcolor = 'black'

    QRimg = QRcode.make_image(
        fill_color=QRcolor, back_color="white"
    ).convert('RGB')

    # pos = ((QRimg.size[0] - logo.size[0]) // 2, (QRimg.size[1] - logo.size[1]) // 2)
    # QRimg.paste(logo, pos)

    return QRimg

def paginate(li, roll=False):
    pages = []
    if not roll:
        length = 5
        items = li[:20]
    else:
        length = 3
        items = li[:12]

    while items:
        pages.append(items[:length])
        items = items[length:]

    return pages


def round_corners(im, rad=30):
    '''The image im has to be an Image instance'''
    circle = Image.new('L', (rad * 2, rad *2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0,0, rad * 2, rad * 2), 0)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)))
    im.putalpha(alpha)

    return im

def get_users():
    with open('users.json', 'rb') as fp:
        users = json.load(fp)
        return users

def save_users(users):
    with open('users.json', 'w') as fp:
        json.dump(users, fp)