import os

from flask import Flask, redirect, render_template, url_for
from flask_ngrok import run_with_ngrok

application = Flask(__name__, instance_relative_config=True)

test_config = None

if test_config is None:
    # load the instance config, if it exists, when not testing
    application.config.from_pyfile('config.py', silent=True)
else:
    # load the test config if passed in
    application.config.from_mapping(test_config)

# ensure the instance folder exists
try:
    os.makedirs(application.instance_path)
except OSError:
    pass

import main_site
'''
    Register Blueprint from auth.py & site.py
'''
application.register_blueprint(main_site.bp)

if __name__ == '__main__':
	application.debug = True
	application.run()

	