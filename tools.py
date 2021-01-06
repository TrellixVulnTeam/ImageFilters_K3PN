import cv2
import numpy as np
from functools import lru_cache
from scipy.interpolate import UnivariateSpline
from typing import Tuple

def spline_to_lookup_table(spline_breaks: list, break_values: list):
    spl = UnivariateSpline(spline_breaks, break_values)
    return spl(range(256))

def apply_rgb_filters(rgb_image, *,
                      red_filter=None, green_filter=None, blue_filter=None):
    c_r, c_g, c_b = cv2.split(rgb_image)

    if red_filter is not None:
        c_r = cv2.LUT(c_r, red_filter).astype(np.uint8)

    if green_filter is not None:
        c_g = cv2.LUT(c_g, green_filter).astype(np.uint8)

    if blue_filter is not None:
        c_b = cv2.LUT(c_b, blue_filter).astype(np.uint8)

    return cv2.merge((c_r, c_g, c_b))

def apply_hue_filter(rgb_image, hue_filter):
    c_h, c_s, c_v = cv2.split(cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV))
    c_s = cv2.LUT(c_s, hue_filter).astype(np.uint8)
    return cv2.cvtColor(cv2.merge((c_h, c_s, c_v)), cv2.COLOR_RGB2HSV)

def cartoonize(rgb_image, *, num_pyr_downs=2, num_bilaterals=7):
    # Apply a bilateral filter to reduce the color palette of the image
    downsampled_img = rgb_image

    for _ in range(num_pyr_downs):
        downsampled_img = cv2.pyrDown(downsampled_img)

    for _ in range(num_bilaterals):
        filterd_small_img = cv2.bilateralFilter(downsampled_img, 9, 9, 7)

    filtered_normal_img = filterd_small_img
    for _ in range(num_pyr_downs):
        filtered_normal_img = cv2.pyrUp(filtered_normal_img)

    # make sure resulting image has the same dims as original
    if filtered_normal_img.shape != rgb_image.shape:
        filtered_normal_img = cv2.resize(filtered_normal_img, rgb_image.shape[:2])

    # Convert the original color image into grayscale
    img_gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

    # Apply a median blur to reduce image noise
    img_blur = cv2.blur(img_gray, 7)

    # Use adaptive thresholding to detect and emphasize the edges in an edge mask
    gray_edges = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)



def convert_to_pencil_sketch(rgb_image):
    gray_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (21, 21), 0, 0)
    gray_sketch = cv2.divide(gray_image, 255 - blurred_image, scale=256)
    return cv2.cvtColor(gray_sketch, cv2.COLOR_RGB2GRAY)

def pencil_sketch_on_canvas(rgb_image, canvas=None):
    gray_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (21, 21), 0, 0)
    gray_sketch = cv2.divide(gray_image, 255 - blurred_image, scale=256)

    if canvas is not None:
        gray_sketch = cv2.multiply(gray_sketch, canvas, scale=1/ 256)
    return cv2.cvtColor(gray_sketch, cv2.COLOR_RGB2GRAY)


def dodge(image, mask):
    print(image.dtype, mask.dtype)
    return cv2.divide(image, 255 - mask, scale=256)


def dodge_naive(image, mask):
    # determine the shape of the input image
    width, height = image.shape[:2]

    # prepare output argument with same size as image
    blend = np.zeros((width, height), np.uint8)

    for c in range(width):
        for r in range(height):

            # shift image pixel value by 8 bits
            # divide by the inverse of the mask
            result = (image[c, r] << 8) / (255 - mask[c, r])

            # make sure resulting value stays within bounds
            blend[c, r] = min(255, result)
    return blend