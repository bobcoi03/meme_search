"""
	CODE FOR THE MAIN SITE
	ANYTHING WITH A / endpoint
"""
from flask import Blueprint, request, render_template, redirect
import search
import time

bp = Blueprint('site', __name__, url_prefix='/')

@bp.route('/', methods=['GET','POST'])
def home_page():
	if request.form.get('search_query'):
		search_query = request.form.get('search_query')
		return redirect(f"/search_query={search_query}")

	return render_template('home.html')

@bp.route('/search_query=<search_query>', methods=['POST','GET'])
def search_query(search_query):

	if request.form.get('search_query'):
		search_query = request.form.get('search_query')
		return redirect(f"/search_query={search_query}")

	start_time = time.time()

	index = search.index_documents(search.load_documents(), search.Index())

	search_results = index.search(f"{search_query}", search_type='OR')

	image_names = []
	for i in range(len(search_results)):
		if search_results[i] == 'None':
			continue
		image_names.append(f"{search_results[i][0].url}")

	number_of_results = len(image_names)

	end_time = time.time()

	run_time = str(end_time - start_time)

	image_names = image_names[:50]

	return render_template(
		'home.html',
		image_names = image_names,
		run_time = run_time,
		search_query = search_query,
		results_length = number_of_results)






