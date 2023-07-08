from PIL import Image, ImageDraw


#  we assume webcam shot will be 1280 x 720 pixels
def merge_image(base: str, filters: str):
    image_base = Image.open(base)
    image_superposee = Image.open(filters)

    # Vérifier si les dimensions des images sont identiques
    if image_base.size != image_superposee.size:
        raise ValueError("Les dimensions des images ne correspondent pas.")

    # Superposer les images
    image_superposee = image_superposee.convert("RGBA")
    image_fusionnee = Image.alpha_composite(image_base.convert("RGBA"), image_superposee)

    
    image_fusionnee.show()


if __name__ == "__main__":
    merge_image("images/test.png", "images/frameok.png")
