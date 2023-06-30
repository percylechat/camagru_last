from PIL import Image, ImageDraw


#  we assume webcam shot will be 1280 x 720 pixels
def merge_image(base: str, filters: list):
    img = Image.open(base).convert("RGBA")
    x, y = img.size
    img2 = Image.open(filters[0]).convert("RGBA").resize((x, y))

    img.putalpha(255)
    img2.putalpha(199)

    img3 = Image.alpha_composite(img, img2)
    img3.show()


if __name__ == "__main__":
    merge_image("screenshot.png", ["catbis.png"])
