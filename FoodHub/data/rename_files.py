import os

id = 0

def rename_files(directory = None):
  global id

  for path in os.listdir(directory):
    relative_path = os.path.join(directory, path) if directory else path

    if os.path.isdir(relative_path):
      rename_files(relative_path)
      continue
    
    _, file_extension = os.path.splitext(relative_path)
    if file_extension == ".jpg":
      new_filename = f"img_{id}.jpg"
      new_relative_path = os.path.join(directory, new_filename) if directory else new_filename
      os.replace(relative_path, new_relative_path)
      id += 1

rename_files()