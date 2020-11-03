from mldl.importers.base import Mask
from PIL import Image
from skimage import measure
import numpy

import sys
import matplotlib.pyplot as plt

def vectorize_mask(mask: Image.Image, epsilon=0.005):
	# this converts input into a resolution of 100x100, otherwise slow
	mask = mask.convert("L").resize((100, 100), resample=Image.BOX)
	mask_array = numpy.array(mask.getdata()).reshape(mask.size[1], mask.size[0]).transpose(1, 0)
	contours = measure.find_contours(mask_array, 128)
	contours = [measure.approximate_polygon(c * 0.01, epsilon) for c in contours]
	contours = list(filter(lambda c: len(c) > 2, contours))
	return Mask.from_json(contours) if len(contours) else None

if __name__ == "__main__":
	img = Image.open(sys.argv[1])
	print(vectorize_mask(img))
