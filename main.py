# Import required packages
import cv2
import pytesseract
import time
from xml.etree import ElementTree as ET
import os
import gzip
import multiprocessing
import csv
"""
	This script loops through jpgs, pngs in static/memeImages/
	using pytesseract on each images. 
	the text output from the pytesseract orc is saved in
	a data.xml file and the filename is written to already
	downloaded.txt
"""
def timing(method):
    """
    Quick and dirty decorator to time functions: it will record the time when
    it's calling a function, record the time when it returns and compute the
    difference. There'll be some overhead, so it's not very precise, but'll
    suffice to illustrate the examples in the accompanying blog post.
    @timing
    def snore():
        print('zzzzz')
        time.sleep(5)
    snore()
    zzzzz
    snore took 5.0011749267578125 seconds
    """
    def timed(*args, **kwargs):
        start = time.time()
        result = method(*args, **kwargs)
        end = time.time()

        execution_time = end - start
        if execution_time < 0.001:
            print(f'{method.__name__} took {execution_time*1000} milliseconds')
        else:
            print(f'{method.__name__} took {execution_time} seconds')

        return result
    return timed

@timing
def get_text(path_to_img: str):
	"""
	Takes path to an image and returns text in that image Using pytesseract and opencv
	"""
	img = cv2.imread(path_to_img)
	# Convert the image to gray scale
	gray = 0

	start_time = time.time()
	end_time = 0
	timer = 0

	while timer < 100:
		timer = time.time() - start_time

		try:
			gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		except cv2.error:
			return False

		# Performing OTSU threshold
		ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

		# Specify structure shape and kernel size.
		# Kernel size increases or decreases the area
		# of the rectangle to be detected.
		# A smaller value like (10, 10) will detect
		# each word instead of a sentence.
		rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))
			 
		# Applying dilation on the threshold image
		dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)

		# Finding contours
		contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
	                                                 cv2.CHAIN_APPROX_NONE)
		# Creating a copy of image
		im2 = img.copy()
		# Looping through the identified contours
		# Then rectangular part is cropped and passed on
		# to pytesseract for extracting text from it
		# Extracted text is then written into the text file
		_text = ""
		for cnt in contours:
			x, y, w, h = cv2.boundingRect(cnt)
			# Drawing a rectangle on copied image
			rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)
			# Cropping the text block for giving input to OCR
			cropped = im2[y:y + h, x:x + w]
			# Apply OCR on the cropped image
			text = pytesseract.image_to_string(cropped)

			_text += text
		"""
		Get rid of illeal characters for xml file
		"""
		delete = [">", "<", "&" , "'", "\""]
		for illegal_char in range(len(delete)):
			_text = _text.replace(delete[illegal_char], "")

		return _text
	print("print false")
	return False

@timing
def add_encoding_to_xml_file():
	"""
	Add enconding to xml file and opening Div tag
	"""
	file = open("data_uncleaned.xml", "a")
	file.write("<?xml version = \"1.0\" encoding = \"UTF-8\" standalone = \"no\" ?>\n")
	file.write("<div>\n")
	file.close()

@timing
def add_closing_div_to_xml_file():
	file = open("data_uncleaned.xml", "a")
	file.write("</div>")
	file.close()

@timing
def add_to_xml_file(text: list, filename: list, url: list):
	"""
	Append 	
			<doc>
				<abstract>text</abstract>
				<filename>filename</filename>
			</doc> 
	to data.xml
	"""
	file = open("data_uncleaned.xml", "a")
	
	for i in range(len(text)):
		file.write(f"<doc><abstract>{text[i]}</abstract><filename>{filename[i]}</filename><url>{url[i]}</url></doc>\n")

	print(f"Successfully added {len(text)} image data to data.xml")
	file.close()

@timing
def if_filename_in_already_downloaded_txt_file(filename: str):
	"""
	Returns True if filename in already_downloaded_txt_file
	"""
	with open('already_downloaded.txt') as f:
		if filename in f.read():
			return True
		else:
			return False

@timing
def get_all_imgs_from_memeImages(extension=".jpg") -> list:
	files = []

	for file in os.listdir("static/memeImages"):
		if file.endswith(extension) and not if_filename_in_already_downloaded_txt_file(file):
			files.append(file)
			print(f"Added {file}")

	print(len(files))

	return files

@timing
def get_rid_of_0x0c():
	delete = ["\f"]
	with open("data_uncleaned.xml") as fin, open("data.xml", "w") as fout:
		
		for line in fin:
			for word in delete:
				line = line.replace(word, "")
			fout.write(line)

@timing
def add_to_already_downloaded_txt_file(filenames: list):
	file = open("already_downloaded.txt", "a")
	for i in filenames:
		file.write(f"{i}\n")
	file.close()

@timing
def handle_download(array, urls, batch_size):
	"""
	This function downloads text and filename to data.xml
	in batches of size batch_size 
	"""
	current_batch = []	# len(current_batch) = batch_size
	current_batch_urls = []
	length = len(array)
	break_points = length // batch_size

	list_of_break_points = []
	for i in range(0, break_points):
		list_of_break_points.append(batch_size * i + batch_size)
	list_of_break_points.append(length)

	for i in range(length):
		if i in list_of_break_points:
			"""
			Run Download Code here
			"""
			converted_text = []
			for i in range(len(current_batch)):
				text = get_text(f"static/memeImages/{current_batch[i]}")
				if text == False:
					continue
				else:
					converted_text.append(text)
				print(f"getting text from {current_batch[i]}")
			add_to_xml_file(converted_text, current_batch, current_batch_urls)
			add_to_already_downloaded_txt_file(current_batch)

			current_batch = []
			current_batch_urls = []

			current_batch_urls.append(urls[i])
			current_batch.append(array[i])
		else:
			current_batch.append(array[i])
			current_batch_urls.append(urls[i])

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def search_csv(filename):
	# given filename -- return url
	csv_file = csv.reader(open('filename_url.csv', 'r'), delimiter=',')

	for row in csv_file:
		if filename == row[0]:
			return row[1]

@timing
def main():

	jpegs = get_all_imgs_from_memeImages('.jpg')

	list_of_urls = []
	
	start_time = time.time()
	
	for i in range(len(jpegs)):
		list_of_urls.append(search_csv(jpegs[i]))
	print(len(list_of_urls))
	
	handle_download(jpegs, list_of_urls, 10)

	get_rid_of_0x0c()

	end_time = time.time()

	print(f"Ran in {round(end_time - start_time, 2)} seconds | Added {len(jpegs)} memes")


if __name__ == "__main__":
	main()