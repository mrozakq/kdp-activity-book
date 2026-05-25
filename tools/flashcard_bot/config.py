from pathlib import Path
from PIL import ImageFont

BASE_DIR = Path(__file__).parent
DATA = BASE_DIR / 'data'
READY = BASE_DIR / 'ready'

show = True
save = True
save_format = 'png'
dpi = (300, 300)

page_width = 1500          #1500x2100 matches 5x7 inches with 300 DPI. Set pixel size values according to dpi
page_height = 2100

resize_image = True
image_width_resize = page_width - 500
image_height_resize = None

center_image_width = True
center_image_height = True
image_from_top = 250
image_from_left = 0

image_background = False
resize_background = True
resize_bg_width = None
resize_bg_height = page_height

bg_color = '#fff2c9'
bg_colors = ['#e2d3fe', '#739de0', '#f4667b', '#92d6ad', '#fecd60', '#fea48e', '#6ccbbf', '#78d08a']
random_colors = True

round_corners_radius = 50
page_border = 0
page_border_color = '#272B35'
border_colors = ['#e2d3fe', '#739de0', '#f4667b', '#92d6ad', '#fecd60', '#fea48e', '#6ccbbf', '#78d08a']
random_border_colors = False

top_text_fill = '#272B35'
bottom_text_fill = '#272B35'
top_text_stroke_color = 'black'
bottom_text_stroke_color = 'black'
top_text_stroke_width = 0
bottom_text_stroke_width = 0
font_top_size = 250
font_bottom_size = 200

top_text_center = True
top_text_margin_left = 500

bottom_text_center = True
bottom_text_margin_left = 100

text_from_top = 350
text_from_bottom = 200

text_to_bottom = False

plane_top = False
plane_bottom = True
plane_full_width = False
plane_full_width_stripe = False
plane_color = 'white'
plane_colors = ['#e8f1e4', '#fff2c9', '#cbf3fa', '#ffe8ec', '#c4ecef', '#fad4b6', '#daeac2', '#e2d3fe']
plane_random_colors = False

plane_as_bg = False
plane_as_border = False

plane_border_radius = 50
plane_border_width = 0
plane_border_color = '#272B35'
padding_lr = 100
padding_top = 50
padding_bottom = 70

solid_under_image = False
solid_as_bg = False
solid_color = 'white'
solid_colors = ['#e8f1e4', '#fff2c9', '#cbf3fa', '#ffe8ec', '#c4ecef', '#fad4b6', '#daeac2', '#e2d3fe']
solid_random_colors = False
solid_margin_top = 50
solid_margin_bottom = 50
solid_margin_lr = 50
solid_border_color = '#272B35'
solid_border_width = 0
solid_border_radius = 50

corners_page = (True, True, True, True)
corners_top_plane = (True, True, True, True)
corners_bottom_plane = (True, True, True, True)
corners_solid_under_image = (True, True, True, True)

only_text_in_center = False      #For generating text cards. "Text 1" from the table is used.

font_top_path = DATA / 'fonts' / 'GentySans-Regular' / 'GentySans-Regular.ttf'
font_bottom_path = DATA / 'fonts' / 'GentySans-Regular' / 'GentySans-Regular.ttf'

font_top = ImageFont.truetype(str(font_top_path))
font_bottom = ImageFont.truetype(str(font_bottom_path))
