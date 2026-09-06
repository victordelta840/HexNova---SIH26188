from PIL import Image
from io import BytesIO


def decode_image(data: bytes) -> Image.Image:
    image = Image.open(BytesIO(data))
    image.load()
    return image.convert("RGB")


def preprocess_image(data: bytes):
    import cv2
    import numpy as np

    image = decode_image(data)
    pixels = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    pixels = cv2.resize(pixels, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    pixels = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(pixels)
    return cv2.fastNlMeansDenoising(pixels, None, 10, 7, 21)