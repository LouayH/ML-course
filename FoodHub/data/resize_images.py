import os
from PIL import Image, ImageOps

def resize_images(directory = None):
  for path in os.listdir(directory):
    relative_path = os.path.join(directory, path) if directory else path

    if os.path.isdir(relative_path):
      resize_images(relative_path)
      continue
    
    _, file_extension = os.path.splitext(relative_path)
    if file_extension == ".jpg":
      try:
        img = Image.open(relative_path)
      except:
        os.remove(relative_path)
        continue
      
      img = ImageOps.fit(img, (224, 224))
      try:
        img.save(relative_path)
      except:
        os.remove(relative_path)

resize_images()