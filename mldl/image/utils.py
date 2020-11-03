import PIL.Image
from mldl.geometry import Rectangle


def crop_image(image: PIL.Image.Image, bounding_box: Rectangle) -> PIL.Image.Image:
	w, h = image.size
	return image.crop((
		int(bounding_box.p1.x * w),
		int(bounding_box.p1.y * h),
		int(bounding_box.p2.x * w),
		int(bounding_box.p2.y * h)
	))
