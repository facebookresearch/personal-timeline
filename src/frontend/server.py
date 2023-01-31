from flask import Flask, request, render_template
from src.frontend.visualization import TimelineRenderer
from src.frontend.qa import QAEngine
import os

static_folder = os.path.join(os.environ['APP_DATA_DIR'],'static')

app = Flask(__name__, static_folder=static_folder)

# for profiling
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

renderer = TimelineRenderer()
qa_engine = QAEngine(summarizer=renderer.summarizer)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/timeline', methods=['GET'])
def get_timeline():
    # get the next level
    new_slides = renderer.split_slide(request.args['unique_id'])

    # don't drip down if nothing new
    if len(new_slides) == 1 and 'trip' not in request.args['unique_id']:
        new_slides = []

    # get the next/prev element at the same level
    new_slides += renderer.get_next_prev(request.args['unique_id'])

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
        if isinstance(qr, str):
            # a single uid
            new_slide = renderer.uid_to_slide(qr)
        else:
            new_slide = renderer.uid_to_slide(qr['unique_id'])
            for key in qr:
                if key != 'unique_id':
                    new_slide[key] = qr[key]

        new_slides.append(new_slide)
    return {'slides': new_slides}


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)