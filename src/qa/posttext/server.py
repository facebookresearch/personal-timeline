import sys
import os
from flask import Flask, redirect, url_for, request, render_template, send_from_directory
from posttext import PostText
from configparser import ConfigParser

config_object = None
engine = None
    
app = Flask(__name__)

def create_app():
    global config_object
    global engine

    config_object = ConfigParser(comment_prefixes=None)
    config_object.read(app.config.get('data_dir')+"/config.ini")
    engine = PostText(config_object, app.config.get('data_dir'))

# # for profiling
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

@app.route('/test', methods=['GET'])
def test():
    """
    TODO: make calls to the appropriate python function
    TODO: we may want to change these API's to POST apis
    """
    # query = request.args.get('event')
    for key in request.args:
        print(key, request.args[key])
    return {'message': 'okay'}


@app.route('/query', methods=['GET'])
def query():
    """Query the posttext engine.
    """
    q = request.args.get('query')
    prompt, sql_before, sql_after, result = engine.query(q)
    return {'prompt': prompt,
            'sql_before': sql_before, 
            'sql_after': sql_after, 
            'result': result}


if __name__ == '__main__':
    app.config['data_dir'] = sys.argv[1]
    create_app()
    app.run(debug=True)
