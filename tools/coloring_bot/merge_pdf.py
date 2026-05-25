import os
import datetime
from natsort import natsorted
from config import READY
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def create_pdf(image_folder, output_path, dpi=300, compression=0, reverse_sort=False, add_blank_page=True, author=None, title=None, subject=None, keywords=None, creator=None, producer=None):
    c = canvas.Canvas(output_path, pagesize=letter)

    if title:
        c.setTitle(title)
    if author:
        c.setAuthor(author)
    if subject:
        c.setSubject(subject)
    if keywords:
        c.setKeywords(keywords)
    if creator:
        c.setCreator(creator)
    if producer:
        c.setProducer(producer)

    image_files = [file for file in os.listdir(image_folder) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files = natsorted(image_files, reverse=reverse_sort)

    for file in image_files:
        image_path = os.path.join(image_folder, file)
        img = Image.open(image_path)

        img = img.rotate(0, expand=True)

        img_width, img_height = img.size

        pdf_width = img_width * 72 / dpi
        pdf_height = img_height * 72 / dpi
        c.setPageSize((pdf_width, pdf_height))

        img_reader = ImageReader(img)
        c.drawImage(img_reader, 0, 0, width=img_width * 72 / dpi, height=img_height * 72 / dpi)

        c.showPage()

        if add_blank_page:
            c.setPageSize(letter)
            c.showPage()

    c.setPageCompression(compression)

    c.save()


if __name__ == "__main__":
    image_folder = READY

    ts = datetime.datetime.now()
    formatted_ts = ts.strftime("%d-%m-%Y_%H-%M-%S")
    pdf_dir = READY / 'PDF'
    pdf_dir.mkdir(exist_ok=True)
    output_path = pdf_dir / f'{formatted_ts}.pdf'

    dpi = 300
    compression = 0  # 0 or 1
    reverse_sort = False
    add_blank_page = True

    author = "John Doe"
    title = "My PDF document"
    subject = "Document subject"
    keywords = "keywords, PDF"
    creator = ""
    producer = ""

    create_pdf(image_folder, str(output_path), dpi, compression, reverse_sort, add_blank_page,
               author, title, subject, keywords, creator, producer)
