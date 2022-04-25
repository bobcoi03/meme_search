from dataclasses import dataclass
from lxml import etree
import gzip
import Stemmer
import re
import string
import time
from collections import Counter
import math
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

	def document_frequency(self, token):
	    return len(self.index.get(token, set()))

	def inverse_document_frequency(self, token):
	    # Manning, Hinrich and Schütze use log10, so we do too, even though it
	    # doesn't really matter which log we use anyway
	    # https://nlp.stanford.edu/IR-book/html/htmledition/inverse-document-frequency-1.html
	    return math.log10(len(self.documents) / self.document_frequency(token))


	def index_document(self, document):
		if document.ID not in self.documents:
			self.documents[document.ID] = document
			document.analyze()

		for token in analyze(document.fulltext):
			if token not in self.index:
				self.index[token] = set()
			self.index[token].add(document.ID)

	def _results(self, analyzed_query):
		return [self.index.get(token, set()) for token in analyzed_query]

	def rank(self, analyzed_query, documents):
	    results = []
	    if not documents:
	        return results
	    for document in documents:
	        score = 0.0
	        for token in analyzed_query:
	            tf = document.term_frequency(token)
	            idf = self.inverse_document_frequency(token)
	            score += tf * idf
	        results.append((document, score))
	    return sorted(results, key=lambda doc: doc[1], reverse=True)

	def search(self, query, search_type='AND', rank=True):
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
		if rank:
			return self.rank(analyzed_query, documents)

		print(f"{len(documents)} results")
		return documents

@dataclass
class Abstract:
	ID: int
	abstract: str
	_filename: str
	_url: str

	def analyze(self):
		# Counter will create a dictionary counting the unique values in an array:

        # {'london': 12, 'beer': 3, ...}
		self.term_frequencies = Counter(analyze(self.fulltext))

	def term_frequency(self, term):
		return self.term_frequencies.get(term, 0)

	@property
	def fulltext(self):
		return self.abstract

	@property
	def filename(self):
		return self._filename

	@property
	def url(self):
		return self._url
	

def load_documents():

	with gzip.open('data.xml.gz', 'rb') as f:
		doc_id = 1
		# iterate through doc element <doc></doc>
		for _, element in etree.iterparse(f, events=('end',), tag='doc'):
			abstract = element.findtext("./abstract")
			filename = element.findtext("./filename")
			url = element.findtext("./url")

			yield Abstract(ID=doc_id, abstract=abstract, _filename=filename, _url=url)

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
	start_time = time.time()
	index = index_documents(load_documents(), Index())
	print(f"Index contains {len(index.documents)} documents")

	search_results = index.search("hello girl", search_type='OR')

	image_names = []

	for i in range(len(search_results)):
		if search_results[i][0].url == 'None':
			continue
		image_names.append(search_results[i][0].url)

	print(image_names)

	end_time = time.time()

	print(f"{len(image_names)} results in {end_time - start_time} seconds")