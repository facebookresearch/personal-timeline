from flask import Flask, redirect, url_for, request, render_template, send_from_directory
from src.visualization import TimelineRenderer
from src.qa import QAEngine


app = Flask(__name__)

# for profiling
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

renderer = TimelineRenderer(path='.')
qa_engine = QAEngine(summarizer=renderer.summarizer, path='.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/timeline', methods=['GET'])
def get_timeline():
    # print(request.args.keys)
    new_slides = renderer.split_slide(request.args['unique_id'])

    # don't drip down if nothing new
    if len(new_slides) == 1:
        new_slides = []
    return {'slides': new_slides}

@app.route('/init', methods=['GET'])
def new_timeline():
    return renderer.create_timeline()
    # new_slides = renderer.split_slide(request.args['unique_id'])
    # return {'slides': new_slides}

@app.route('/qa', methods=['GET'])
def qa():
    query = request.args.get('search')
    print(query)
    query_result = qa_engine.query(query, k=4)

    new_slides = []
    for qr in query_result:
        new_slides.append(renderer.uid_to_slide(qr))
    return {'slides': new_slides}


if __name__ == '__main__':
    app.run(debug=True)