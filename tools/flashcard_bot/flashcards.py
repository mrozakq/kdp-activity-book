from config import *
import datetime
import os
import csv
from random import randint
from PIL import Image, ImageDraw, ImageFont, ImageChops
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def check_csv_delimiter(file_path):
    with open(file_path, 'r') as file:
        first_line = file.readline().strip()

        if ',' in first_line:
            return ','
        elif ';' in first_line:
            return ';'
        else:
            return ','


def round_corners(im, rad=50):
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + bigsize, fill=255, radius=rad)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, im.split()[-1])
    im.putalpha(mask)

    return im


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


def open_data():
    file_path = DATA / 'data.csv'
    delimiter = check_csv_delimiter(file_path)

    with open(file_path, "r", newline="") as data:
        heading = next(data)
        reader = csv.reader(data, delimiter=delimiter)

        rows = []
        for row in reader:
            rows.append(row)

        return rows


def create_image(row, counter):
    image = row[0]
    text_1 = row[1]
    text_2 = row[2]

    if row[3]:
        color = row[3]
    else:
        if random_colors:
            color = bg_colors[randint(0, len(bg_colors) - 1)]
        else:
            color = bg_color
    if row[4]:
        page_border_color_loc = row[4]
        plane_border_color_loc = row[4]
        solid_border_color_loc = row[4]
    else:
        if random_border_colors:
            borders_color = border_colors[randint(0, len(border_colors) - 1)]
            page_border_color_loc = borders_color
            plane_border_color_loc = borders_color
            solid_border_color_loc = borders_color
        else:
            page_border_color_loc = page_border_color
            plane_border_color_loc = plane_border_color
            solid_border_color_loc = solid_border_color
    if row[5]:
        plane_color_loc = row[5]
    else:
        if plane_random_colors:
            plane_color_loc = plane_colors[randint(0, len(plane_colors) - 1)]
        else:
            if plane_as_border:
                plane_color_loc = page_border_color_loc
            else:
                plane_color_loc = plane_color
    if row[6]:
        top_text_fill_loc = row[6]
    else:
        top_text_fill_loc = top_text_fill
    if row[7]:
        bottom_text_fill_loc = row[7]
    else:
        bottom_text_fill_loc = bottom_text_fill
    if row[8]:
        solid_color_loc = row[8]
    else:
        if solid_random_colors:
            solid_color_loc = solid_colors[randint(0, len(solid_colors) - 1)]
        else:
            solid_color_loc = solid_color
    if row[9]:
        bg_image = row[9]
    else:
        bg_image = None

    if not image:
        raise Exception('Fill the paths to the images in the first column of the "data.csv" table.')
    if text_2 and not text_1:
        raise Exception('Enter the flashcard texts in the second column of the "data.csv" table')

    im = Image.new('RGBA', (page_width, page_height), (0, 0, 0, 0))
    width, height = im.size
    draw = ImageDraw.Draw(im)

    if image_background:
        if not bg_image:
            try:
                folder_dir = DATA / 'backgrounds'
                bg_images = []
                for i in os.listdir(folder_dir):
                    if (i.endswith(".png") or i.endswith(".jpg") or i.endswith(".jpeg")):
                        image_path = os.path.join(folder_dir, i)
                        bg_images.append(image_path)

                random_img = bg_images[randint(0, len(bg_images) - 1)]
                bg_img = Image.open(random_img).convert('RGBA')
            except:
                raise Exception("Ensure that there are images in the backgrounds folder")
        else:
            try:
                bg_img = Image.open(bg_image).convert('RGBA')
            except:
                raise Exception("Verify the correctness of the background image path")
        if resize_background:
            bg_img = resize_ratio(bg_img, resize_bg_width, resize_bg_height)

        im.alpha_composite(bg_img, (0, 0))
    else:
        draw.rounded_rectangle((0, 0, page_width, page_height), fill=color, radius=round_corners_radius,
                               outline=page_border_color_loc, width=page_border, corners=corners_page)

    try:
        image = Image.open(image).convert('RGBA')
    except:
        raise Exception("Check the correctness of the image path")

    if resize_image:
        resized_image = resize_ratio(image, image_width_resize, image_height_resize).convert('RGBA')
    else:
        resized_image = image

    offset_w = (width - resized_image.size[0]) // 2
    offset_h = (height - resized_image.size[1]) // 2

    size_multiline = get_font(font_top.path, font_top_size).getsize_multiline(text_1)
    size_multiline_2 = get_font(font_bottom.path, font_bottom_size).getsize_multiline(text_2)

    text_offset_w = (width - size_multiline[0]) // 2
    text_offset_h = (height - size_multiline[1]) // 2

    text_offset_w_2 = (width - size_multiline_2[0]) // 2
    text_offset_h_2 = (height - size_multiline_2[1]) // 2

    shape_top = (
        text_offset_w - padding_lr if top_text_center else top_text_margin_left - padding_lr,
        text_from_top - size_multiline[1] - padding_top,
        text_offset_w + size_multiline[0] + padding_lr if top_text_center else top_text_margin_left + size_multiline[0] + padding_lr,
        text_from_top + padding_bottom)

    shape_top_full = (
        page_border,
        page_border,
        page_width - page_border,
        text_from_top + padding_bottom)

    shape_bottom = (
        text_offset_w_2 - padding_lr if bottom_text_center else bottom_text_margin_left - padding_lr,
        height-text_from_bottom - size_multiline_2[1] - padding_top,
        text_offset_w_2 + size_multiline_2[0] + padding_lr if bottom_text_center else bottom_text_margin_left + size_multiline_2[0] + padding_lr,
        height-text_from_bottom + padding_bottom)

    shape_bottom_full = (
        page_border,
        height - text_from_bottom - size_multiline_2[1] - padding_top,
        page_width - page_border,
        height - page_border)

    shape_solid = (solid_margin_lr, solid_margin_top, page_width - solid_margin_lr, height - solid_margin_bottom)

    if not text_1 and not text_2:
        if solid_under_image:
            draw.rounded_rectangle(shape_solid, fill=solid_color_loc if not solid_as_bg else color,
                                   radius=solid_border_radius, outline=solid_border_color_loc,
                                   width=solid_border_width, corners=corners_solid_under_image)
            im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))
        else:
            im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))

    if not only_text_in_center:
        if text_1 and text_2:
            if solid_under_image:
                draw.rounded_rectangle(shape_solid, fill=solid_color_loc if not solid_as_bg else color,
                                       radius=solid_border_radius, outline=solid_border_color_loc,
                                       width=solid_border_width, corners=corners_solid_under_image)
                im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))
            else:
                im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))

            if plane_top:
                if plane_full_width:
                    shape_top_full_stripe = (
                        page_border,
                        text_from_top - size_multiline[1] - padding_top,
                        page_width - page_border,
                        text_from_top + padding_bottom)

                    draw.rounded_rectangle(shape_top_full if not plane_full_width_stripe else shape_top_full_stripe,
                                           fill=plane_color_loc if not plane_as_bg else color,
                                           radius=round_corners_radius-page_border if round_corners_radius > 0 and round_corners_radius >= page_border else round_corners_radius,
                                           outline=plane_border_color_loc, width=plane_border_width,
                                           corners=(True, True, False, False) if not plane_full_width_stripe else (False, False, False, False))
                else:
                    draw.rounded_rectangle(shape_top, fill=plane_color_loc if not plane_as_bg else color, radius=plane_border_radius,
                                           outline=plane_border_color_loc, width=plane_border_width, corners=corners_top_plane)

            draw.text((width // 2 if top_text_center else top_text_margin_left, text_from_top), text_1, align='center', anchor="ms" if top_text_center else 'ls',
                      font=get_font(font_top.path, font_top_size),
                      fill=top_text_fill_loc,
                      stroke_width=top_text_stroke_width, stroke_fill=top_text_stroke_color)

            if plane_bottom:
                if plane_full_width:
                    shape_bottom_full_stripe = (
                        page_border,
                        height - text_from_bottom - size_multiline_2[1] - padding_top,
                        page_width - page_border,
                        height - text_from_bottom + padding_bottom)

                    draw.rounded_rectangle(shape_bottom_full if not plane_full_width_stripe else shape_bottom_full_stripe,
                                           fill=plane_color_loc if not plane_as_bg else color,
                                           radius=round_corners_radius-page_border if round_corners_radius > 0 and round_corners_radius >= page_border else round_corners_radius,
                                           outline=plane_border_color_loc, width=plane_border_width,
                                           corners=(False, False, True, True) if not plane_full_width_stripe else (False, False, False, False))
                else:
                    draw.rounded_rectangle(shape_bottom, fill=plane_color_loc if not plane_as_bg else color, radius=plane_border_radius,
                                           outline=plane_border_color_loc, width=plane_border_width, corners=corners_bottom_plane)

            draw.text((width // 2 if bottom_text_center else bottom_text_margin_left, height-text_from_bottom), text_2, align='center', anchor="ms" if bottom_text_center else 'ls',
                      font=get_font(font_bottom.path, font_bottom_size),
                      fill=bottom_text_fill_loc,
                      stroke_width=bottom_text_stroke_width, stroke_fill=bottom_text_stroke_color)

        elif not text_to_bottom:
            if solid_under_image:
                draw.rounded_rectangle(shape_solid, fill=solid_color_loc if not solid_as_bg else color,
                                       radius=solid_border_radius,
                                       outline=solid_border_color_loc, width=solid_border_width, corners=corners_solid_under_image)
                im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))
            else:
                im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))

            if plane_top:
                if plane_full_width:
                    shape_top_full_stripe = (
                        page_border,
                        text_from_top - size_multiline[1] - padding_top,
                        page_width-page_border,
                        text_from_top + padding_bottom)

                    draw.rounded_rectangle(shape_top_full if not plane_full_width_stripe else shape_top_full_stripe, fill=plane_color_loc if not plane_as_bg else color,
                                           radius=round_corners_radius-page_border if round_corners_radius > 0 and round_corners_radius >= page_border else round_corners_radius,
                                           outline=plane_border_color_loc, width=plane_border_width,
                                           corners=(True, True, False, False) if not plane_full_width_stripe else (False, False, False, False))
                else:
                    draw.rounded_rectangle(shape_top, fill=plane_color_loc if not plane_as_bg else color,
                                           radius=plane_border_radius,
                                           outline=plane_border_color_loc, width=plane_border_width, corners=corners_top_plane)

            draw.text((width // 2 if top_text_center else top_text_margin_left, text_from_top), text_1, align='center', anchor="ms" if top_text_center else 'ls',
                      font=get_font(font_top.path, font_top_size),
                      fill=top_text_fill_loc,
                      stroke_width=top_text_stroke_width, stroke_fill=top_text_stroke_color)

        elif text_to_bottom:
            size_multiline_3 = get_font(font_bottom.path, font_bottom_size).getsize_multiline(text_1)

            text_offset_w = (width - size_multiline_3[0]) // 2
            text_offset_h = (height - size_multiline_3[1]) // 2

            shape_bottom = (
                text_offset_w - padding_lr if bottom_text_center else bottom_text_margin_left - padding_lr,
                height - text_from_bottom - size_multiline_3[1] - padding_top,
                text_offset_w + size_multiline_3[0] + padding_lr if bottom_text_center else bottom_text_margin_left +
                                                                                              size_multiline_3[
                                                                                                  0] + padding_lr,
                height - text_from_bottom + padding_bottom)

            shape_bottom_full = (
                page_border,
                height - text_from_bottom - size_multiline_3[1] - padding_top,
                page_width - page_border,
                height - page_border)

            shape_bottom_full_stripe = (
                page_border,
                height - text_from_bottom - size_multiline_3[1] - padding_top,
                page_width - page_border,
                height - text_from_bottom + padding_bottom)

            if solid_under_image:
                draw.rounded_rectangle(shape_solid, fill=solid_color_loc if not solid_as_bg else color,
                                       radius=solid_border_radius,
                                       outline=solid_border_color_loc, width=solid_border_width, corners=corners_solid_under_image)
                im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))
            else:
                im.alpha_composite(resized_image, (offset_w if center_image_width else image_from_left, offset_h if center_image_height else image_from_top))

            if plane_bottom:
                if plane_full_width:
                    draw.rounded_rectangle(shape_bottom_full if not plane_full_width_stripe else shape_bottom_full_stripe,
                                           fill=plane_color_loc if not plane_as_bg else color,
                                           radius=round_corners_radius - page_border if round_corners_radius > 0 and round_corners_radius >= page_border else round_corners_radius,
                                           outline=plane_border_color_loc, width=plane_border_width,
                                           corners=(False, False, True, True) if not plane_full_width_stripe else (
                                           False, False, False, False))

                else:
                    draw.rounded_rectangle(shape_bottom, fill=plane_color_loc if not plane_as_bg else color, radius=plane_border_radius,
                                           outline=plane_border_color_loc, width=plane_border_width, corners=corners_bottom_plane)

            draw.text((width // 2 if bottom_text_center else bottom_text_margin_left, height - text_from_bottom), text_1, align='center', anchor="ms" if top_text_center else 'ls',
                      font=get_font(font_bottom.path, font_bottom_size),
                      fill=bottom_text_fill_loc,
                      stroke_width=bottom_text_stroke_width, stroke_fill=bottom_text_stroke_color)

    else:
        if plane_top:
            shape = (text_offset_w - padding_lr,
                     text_offset_h - padding_top,
                     text_offset_w + size_multiline[0] + padding_lr,
                     text_offset_h + size_multiline[1] + padding_bottom)
            draw.rounded_rectangle(shape, fill=plane_color_loc if not plane_as_bg else color,
                                   radius=plane_border_radius,
                                   outline=plane_border_color_loc, width=plane_border_width, corners=corners_top_plane)

        draw.text((width // 2, height // 2), text_1, align='center',
                  anchor="mm",
                  font=get_font(font_top.path, font_top_size),
                  fill=top_text_fill_loc,
                  stroke_width=top_text_stroke_width, stroke_fill=top_text_stroke_color)

    if image_background and round_corners_radius > 0:
        round_corners(im, round_corners_radius*3)
    if round_corners_radius > 0 and not image_background:
        round_corners(im, round_corners_radius*3.05)

    if show:
        im.show()

    if save:
        ts = datetime.datetime.now()
        formatted_ts = ts.strftime("%d-%m-%Y_%H-%M-%S")

        filename = f'{counter}_{formatted_ts}.{save_format}'
        image_path = os.path.join(READY, filename)

        im.save(image_path, dpi=dpi)
        print(f'{counter} image saved')




