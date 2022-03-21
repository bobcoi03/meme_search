from dataclasses import dataclass
from lxml import etree
import gzip
import Stemmer
import re
import string
import time
"""
ensuring that different forms
of a word map to the same stem, 
like brewery and breweries
"""
STEMMER = Stemmer.Stemmer('english')

# top 25 most common words in English and "wikipedia":
# https://en.wikipedia.org/wiki/Most_common_words_in_English
STOPWORDS = set(['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
                 'I', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
                 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'wikipedia'])

PUNCTUATION = re.compile('[%s]' % re.escape(string.punctuation))

def tokenize(text):
	return text.split()

def lowercase_filter(tokens):
	return [token.lower() for token in tokens]

def stem_filter(tokens):
	return STEMMER.stemWords(tokens)

def punctuation_filter(tokens):
    return [PUNCTUATION.sub('', token) for token in tokens]

def stopword_filter(tokens):
    return [token for token in tokens if token not in STOPWORDS]

def analyze(text):
    tokens = tokenize(text)
    tokens = lowercase_filter(tokens)
    tokens = punctuation_filter(tokens)
    tokens = stopword_filter(tokens)
    tokens = stem_filter(tokens)

    return [token for token in tokens if token]

class Index:
	def __init__(self):
		self.index = {}
		self.documents = {}

	def index_document(self, document):
		if document.ID not in self.documents:
			self.documents[document.ID] = document

		for token in analyze(document.fulltext):
			if token not in self.index:
				self.index[token] = set()
			self.index[token].add(document.ID)

	def _results(self, analyzed_query):
		return [self.index.get(token, set()) for token in analyzed_query]

	def search(self, query, search_type='AND'):
		"""
		Still boolean search; this will return documents that contain either all words
		from the query or just one of them, depending on the search_type specified.
		We are still not ranking the results (sets are fast, but unordered).
		"""
		if query == "":
			return "Query is empty"

		if search_type not in ('AND','OR'):
			print('parameter (search_type) is invalid')
			return []

		print(f"Query: {query}")

		analyzed_query = analyze(query)
		results = self._results(analyzed_query)

		if search_type == 'AND':
		# all tokens must be in the document
			documents = [self.documents[doc_id] for doc_id in set.intersection(*results)]
		if search_type == 'OR':
		# only one token has to be in the document
			documents = [self.documents[doc_id] for doc_id in set.union(*results)]

		print(f"{len(documents)} results")
		return documents

@dataclass
class Abstract:
	ID: int
	abstract: str
	_filename: str

	@property
	def fulltext(self):
		return self.abstract

	@property
	def filename(self):
		return self._filename

def load_documents():

	with gzip.open('data.xml.gz', 'rb') as f:
		doc_id = 1

		# iterate through doc element <doc></doc>
		for _, element in etree.iterparse(f, events=('end',), tag='doc'):
			abstract = element.findtext("./abstract")
			filename = element.findtext("./filename")

			yield Abstract(ID=doc_id, abstract=abstract, _filename=filename)

			doc_id += 1
			# element.clear() call will explicitly free up memory
			element.clear()

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
def index_documents(documents, index):
    for i, document in enumerate(documents):
        index.index_document(document)
        if i % 5000 == 0:
            print(f'Indexed {i} documents', end='\r')
    return index

if __name__ == "__main__":
	index = index_documents(load_documents(), Index())
	print(f"Index contains {len(index.documents)} documents")

	search_results = index.search('chess', search_type='OR')
	
	image_names = []
	for i in range(len(search_results)):
		image_names.append(search_results[i].filename)

	print(image_names)



