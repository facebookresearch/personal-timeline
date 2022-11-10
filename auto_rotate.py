import os
import sys
from glob import glob
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
register_heif_opener()

if __name__ == '__main__':
	rotate = len(sys.argv) > 1 and (sys.argv[1] == 'rotate')
	exts = ["HEIC", 'JPG', 'JPEG', 'png']

	for root, dirs, files in os.walk('personal-data/google_photos/'):
		for basename in files:
			if any([basename.lower().endswith(ext.lower()) for ext in exts]):
				filepath = os.path.join(root, basename)
				new_path = os.path.join('static/', basename + '.compressed.jpg')
				if not os.path.exists(new_path):
					continue

				# filepath = os.path.join('static/', fn)
				try:
					image = Image.open(filepath)
					new_image = Image.open(new_path)
					for orientation in ExifTags.TAGS.keys():
						if ExifTags.TAGS[orientation]=='Orientation':
							break
					exif=dict(image._getexif().items())

					rotated = True
					if exif[orientation] == 3:
						image = image.transpose(Image.ROTATE_180)
						new_image = new_image.transpose(Image.ROTATE_180)
					elif exif[orientation] == 6:
						image=image.transpose(Image.ROTATE_270)
						new_image = new_image.transpose(Image.ROTATE_270)
					elif exif[orientation] == 8:
						image = image.transpose(Image.ROTATE_90)
						new_image = new_image.transpose(Image.ROTATE_90)
					else:
						rotated = False
					if rotated:
						print('rotated:', os.path.join(root, basename))
						if rotate:
							image.save(filepath)
							new_image.save(new_path)
				except (AttributeError, KeyError, IndexError):
					# print('Cannot get exif:', basename)
					# cases: image don't have getexif
					pass
