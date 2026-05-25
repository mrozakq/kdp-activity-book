from pathlib import Path
from PIL import ImageFont

BASE_DIR = Path(__file__).parent
DATA = BASE_DIR / 'data'
READY = BASE_DIR / 'ready'


save = True
save_format = 'png'
show = True

dpi = (300, 300)

page_width = 2550    #2550 x 3300 matches 8.5 x 11 inches with 300 dpi
page_height = 3300

resize_image = False
resize_width = page_width - 300

letters_fill = 'white'
stroke_color = 'black'
stroke_width = 20
font_size = 350
spacing = 4
adding_breaks = 7

frame = False
frame_padding_left = 150
frame_padding_right = 150
frame_padding_top = 150
frame_padding_bottom = 150
frame_border_width = 10
frame_color = 'black'
frame_border_radius = 0
frame_corners = (True, True, True, True)


harlow_font = ImageFont.truetype(str(DATA / 'fonts' / 'Harlow Solid Regular' / 'Harlow Solid Regular.ttf'))
courgette_font = ImageFont.truetype(str(DATA / 'fonts' / 'Courgette' / 'Courgette-Regular.ttf'))
shrikhand_font = ImageFont.truetype(str(DATA / 'fonts' / 'Shrikhand' / 'Shrikhand-Regular.ttf'))
lobster_font = ImageFont.truetype(str(DATA / 'fonts' / 'Lobster' / 'Lobster-Regular.ttf'))
passionone_font = ImageFont.truetype(str(DATA / 'fonts' / 'Passion_One' / 'PassionOne-Regular.ttf'))
fugazone_font = ImageFont.truetype(str(DATA / 'fonts' / 'Fugaz_One' / 'FugazOne-Regular.ttf'))
carterone_font = ImageFont.truetype(str(DATA / 'fonts' / 'Carter_One' / 'CarterOne-Regular.ttf'))
pattaya_font = ImageFont.truetype(str(DATA / 'fonts' / 'Pattaya' / 'Pattaya-Regular.ttf'))
calistoga_font = ImageFont.truetype(str(DATA / 'fonts' / 'Calistoga' / 'Calistoga-Regular.ttf'))
oleo_font = ImageFont.truetype(str(DATA / 'fonts' / 'Oleo_Script_Swash_Caps' / 'OleoScriptSwashCaps-Regular.ttf'))
lemon_font = ImageFont.truetype(str(DATA / 'fonts' / 'Lemon' / 'Lemon-Regular.ttf'))
mochiy_font = ImageFont.truetype(str(DATA / 'fonts' / 'Mochiy_Pop_One' / 'MochiyPopOne-Regular.ttf'))
spicy_font = ImageFont.truetype(str(DATA / 'fonts' / 'Spicy_Rice' / 'SpicyRice-Regular.ttf'))
mochiy2_font = ImageFont.truetype(str(DATA / 'fonts' / 'Mochiy_Pop_P_One' / 'MochiyPopPOne-Regular.ttf'))
kavoon_font = ImageFont.truetype(str(DATA / 'fonts' / 'Kavoon' / 'Kavoon-Regular.ttf'))

fonts = [
            shrikhand_font,
            lobster_font,
            passionone_font,
            fugazone_font,
            carterone_font,
            pattaya_font,
            harlow_font,
            courgette_font,
            calistoga_font,
            oleo_font,
            lemon_font,
            mochiy_font,
            spicy_font,
            mochiy2_font,
            kavoon_font,

    ]
