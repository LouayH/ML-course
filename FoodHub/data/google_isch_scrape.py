import os, requests, re, json
from bs4 import BeautifulSoup

ingredient = input("Enter ingredient name: ")

headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36",
  # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
  # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
  # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
}

params = {
  "q": ingredient,
  "tbm": "isch",
  "hl": "en",
  "ijn": "0",
  "tbs": "sur:publicdomain"
}

html = requests.get("https://www.google.com/search", params = params, headers = headers, timeout = 30)

soup = BeautifulSoup(html.text, "lxml")

def get_original_images():
  all_script_tags = soup.select("script")
  # print("all_script_tags", all_script_tags, "\n")

  images_raw_data = "".join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(all_script_tags)))
  # print("images_raw_data", images_raw_data, "\n")

  images_json_string = json.dumps(images_raw_data)
  # print("images_json_string", images_json_string, "\n")

  images_data_object = json.loads(images_json_string)
  # print("images_data_object", images_data_object, "\n")

  matched_images_data = re.findall(r"\"b-GRID_STATE0\"(.*)sideChannel:\s?{}}", images_data_object)
  # print("matched_images_data", matched_images_data, "\n")

  # exclude thumbnails
  images_data = re.sub(
    r"\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]",
    "",
    str(matched_images_data)
  )
  # print("images_data", images_data, "\n")

  full_res_images_data = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]", images_data)
  # print("full_res_images_data", full_res_images_data, "\n")

  full_res_images = [
    bytes(bytes(img, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape")
    for img in full_res_images_data
  ]
  
  return full_res_images

images = get_original_images()

id = 0
for img in images:
  try:
    data = requests.get(img, timeout = 5)
  except:
    data = None

  if data:
    if not os.path.exists(ingredient):
      os.mkdir(ingredient)

    data = data.content

    with open(f"{ingredient}{os.path.sep}{id}.jpg", "wb") as f:
      f.write(data)

    id += 1



