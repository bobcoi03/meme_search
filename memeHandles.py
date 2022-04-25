import os
import requests
from bs4 import BeautifulSoup
import time
import PIL.Image
import datetime
import multiprocessing
import csv

def get_filename(url):
	"""
	if url == 'https://reddit.com/ambifj129.jpg'
	--> return 'ambifj129.jpg'
	"""
	return url.rsplit('/', 1)[1]

class GenerateMemes:
	"""
	Uses Meme_Api: https://github.com/D3vd/Meme_Api
	to scrape subreddits for Memes & download them as images
	"""
	def __init__(self):
		self.subreddits = [	"memes",
							"dankmemes",
							"me_irl",
							"wholesomememes",
							"ProgrammerHumor",
							"wallstreetbets",
							"AnarchyChess",
							"technicallythetruth",
							"funny",
							"MemeEconomy",
							"PrequelMemes",
							"terriblefacebookmemes",
							"HistoryMemes",
							"bonehurtingjuice",
							"trippinthroughtime",
							"2meirl4meirl",
							"starterpacks",
							"shitposting",
							]
		self.downloaded_memes = 0
		
	def generate_memes(self, amount=4) -> list: # max for amount is 50
		"""
		RETURN LIST OF IMAGE URLS OF
		RANDOM MEMES FROM SUBREDDITS
		"""
		lists_of_url_imgs = []
		for subreddit in range(len(self.subreddits)):
			print(f"Getting {amount} memes from {self.subreddits[subreddit]}")
			url = f"https://meme-api.herokuapp.com/gimme/{self.subreddits[subreddit]}/{amount}"
			data = requests.get(url)
			data_dict = data.json()
			for memes in range(len(data_dict["memes"])):
				lists_of_url_imgs.append(data_dict["memes"][memes]["url"])			
		return lists_of_url_imgs

	def save_from_url(self, url, folder="static/memeImages") -> None:
		"""
		url of an image can be string or list
		SAVE MEMES AS IMAGE
		FILES FROM URL, 
		returns a list of urls that were saved
		list<urls>	
		"""
		start_time = time.time()

		skipped_download = 0

		if not os.path.isdir(f"{folder}"):
			os.mkdir('memeImages')
			print(f"Created folder {folder}/")
		else:
			print(f"/{folder} already exists")
		''' 
		Loops through list of url
		images and downloads them
		if they aren't already downloaded
		'''
		downloaded_urls = []

		if type(url) == list:
			for i in range(len(url)):
				filename= get_filename(url[i])
				img_data = requests.get(url[i]).content
				if os.path.isfile(f'{folder}/{filename}'):
					print(f'Skipping Download, {folder}/{filename} already exists')
					skipped_download += 1
				else:
					with open(f'{folder}/{filename}', 'wb') as handler:
						handler.write(img_data)
						print(f"Dowloading {filename} to {folder}/")
						self.downloaded_memes += 1
						downloaded_urls.append(url[i])

		else:
			filename = get_filename(url)
			img_data = requests.get(url).content
			if os.path.isfile(f'{folder}/{filename}'):
				print(f'Skipping Download, {folder}/{filename} already exists')
			else:
				with open(f'{folder}/{filename}', 'wb') as handler:
					handler.write(img_data)
					print(f"Dowloading {filename} to {folder}/")
					self.downloaded_memes += 1
					downloaded_urls.append(url)

		end_time = time.time()

		run_time = end_time - start_time

		print(f"Downloaded {self.downloaded_memes} memes to {folder}/ in {run_time} seconds\n{run_time / self.downloaded_memes} seconds per meme download")

		return downloaded_urls

class MemeScraper:
	"""
	Scrapes the internet for memes
	"""
	def __init__(self, starting_url):
		self.starting_url = starting_url
		self.visited_urls = []
		self.indexed_urls = []

	def get_img_urls(self, url):
		"""
		Return a list of url images given url
		"""
		html_page = requests.get(url).text
		soup = BeautifulSoup(html_page, 'html.parser')
		image_urls = []

		for img in soup.findAll('img'):
			image_urls.append(img.get('src'))
		return image_urls

	def get_all_links(self, url):
		"""
		Returns list of hrefs given a url
		"""
		links = []
		html_page = requests.get(url).text
		soup = BeautifulSoup(html_page, 'html.parser')
		for link in soup.find_all('a'):
			href = link.get('href')
			if type(href) == str:
				if href[0] == '/':
					href = self.clean_up_url(url, href)
				links.append(href)
		return links

	def crawl(self, starting_url: str) -> list:
		'''
		Adds dictionary to list
		self.indexed_urls in the form -> 
		starting_url : ['urls1, url2, ...']
		'''
		_dict = {f"{starting_url}" : self.get_all_links(starting_url)}
		self.indexed_urls.append(_dict)

	def clean_up_url(self, url: str, href: str):
		"""
		Renames hrefs to appropriate url
		ie. href = '/view' & url = 'youtube.com'
		-> 'youtube.com/view'
		"""
		return f"{url}{href}"

def view_size_img(path_to_file):
	image = PIL.Image.open(path_to_file)
	
	return image.size

def split_list(a_list):
    half = len(a_list)//2
    return a_list[:half], a_list[half:]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def write_to_csv(filenames: list, urls: list):
	import csv

	with open('filename_url.csv','w',encoding='UTF8') as f:
		writer = csv.writer(f)

		for i in range(len(filenames)):
			data = [filenames[i],urls[i]]
			writer.writerow(data)

if __name__ == "__main__":
	start_time = time.time()

	g = GenerateMemes()
	g_memes = g.generate_memes(50)

	list_of_downloaded_urls = g.save_from_url(g_memes)

	list_of_filenames = []
	for i in range(len(list_of_downloaded_urls)):
		# convert url to filename
		list_of_filenames.append(get_filename(list_of_downloaded_urls[i]))

	write_to_csv(list_of_filenames, list_of_downloaded_urls)

	end_time = time.time()