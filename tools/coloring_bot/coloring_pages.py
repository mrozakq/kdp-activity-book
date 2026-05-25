from config import *
import os
import csv
from random import randint
from PIL import Image, ImageDraw


def check_csv_delimiter(file_path):
    with open(file_path, 'r') as file:
        first_line = file.readline().strip()

        if ',' in first_line:
            return ','
        elif ';' in first_line:
            return ';'
        else:
            return ','


def resize_ratio(image, width=None, height=None):
    global resized_image
    if width:
        wpercent = (width / float(image.size[0]))
        hsize = int((float(image.size[1]) * float(wpercent)))
        resized_image = image.resize((width, hsize))
    elif height:
        hpercent = (height / float(image.size[1]))
        wsize = int((float(image.size[0]) * float(hpercent)))
        resized_image = image.resize((wsize, height))
    return resized_image


def get_font(path, size):
    font = ImageFont.truetype(path, size)
    return font


def add_line_breaks(quote):
    split = quote.split(' ')
    new_string = ''

    count = 0

    for e in split:
        if len(new_string) < count:
            new_string += f' {e}'
        else:
            new_string += f'\n{e}'
            count += adding_breaks

    new_quote = new_string.strip()

    return new_quote


def open_quotes():
    file_path = DATA / 'quotes.csv'
    delimiter = check_csv_delimiter(file_path)

    with open(file_path, "r", newline="") as quotes:
        # heading = next(database)

        reader = csv.reader(quotes, delimiter=delimiter)

        try:
            folder_dir = DATA / 'images'
            bg_images = []
            for i in os.listdir(folder_dir):
                if (i.endswith(".png") or i.endswith(".jpg") or i.endswith(".jpeg")):
                    image_path = os.path.join(folder_dir, i)
                    bg_images.append(image_path)
        except:
            raise Exception("Check for images in the 'images' folder")

        count = 0
        for row in reader:
            count += 1
            quote = row[0]

            try:
                img = bg_images[randint(0, len(bg_images) - 1)]
                bg_images.remove(img)
            except:
                raise Exception("All images have been used for generation (without any repetitions).\n"
                                "If you want to regenerate using the same images, simply run the code again.")

            quote_with_breaks = add_line_breaks(quote)

            create_page(quote_with_breaks, img, count)


def create_page(quote, img, count):
    im = Image.new('RGBA', (page_width, page_height), 'white')

    background = Image.open(img).convert('RGBA')

    if resize_image:
        background = resize_ratio(background, width=resize_width)

    width, height = im.size

    offset_w = (width - background.size[0]) // 2
    offset_h = (height - background.size[1]) // 2

    im.alpha_composite(background, (offset_w, offset_h))

    font = fonts[randint(0, len(fonts) - 1)]

    draw = ImageDraw.Draw(im)

    draw.text((width / 2, height / 2), quote, align='center', anchor="mm",
              font=get_font(font.path, font_size),
              fill=letters_fill,
              stroke_width=stroke_width, stroke_fill=stroke_color, spacing=spacing)

    if frame:
        frm = Image.new('RGBA', (page_width, page_height), (0, 0, 0, 0))
        draw_frame = ImageDraw.Draw(frm)

        shape = (frame_padding_left,
                 frame_padding_top,
                 page_width-frame_padding_right,
                 page_height-frame_padding_bottom)

        draw_frame.rounded_rectangle(shape, fill=(0, 0, 0, 0), radius=frame_border_radius,
                               outline=frame_color, width=frame_border_width, corners=frame_corners)

        im.alpha_composite(frm, (0, 0))

    if show:
        im.show()

    if save:
        filename = f'{str(count)}.{save_format}'
        image_path = os.path.join(READY, filename)

        im.save(image_path, dpi=dpi)
        print(f'{count} image saved')
