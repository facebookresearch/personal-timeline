from flask import Flask, redirect, url_for, request, render_template, send_from_directory
from src.visualization import TimelineRenderer


app = Flask(__name__)

renderer = TimelineRenderer('.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/timeline', methods=['GET'])
def get_timeline():
    print(request.args.keys)
    new_slides = renderer.split_slide(request.args['unique_id'])
    return {'slides': new_slides}

@app.route('/init', methods=['GET'])
def new_timeline():
    return renderer.create_timeline()
    # new_slides = renderer.split_slide(request.args['unique_id'])
    # return {'slides': new_slides}

if __name__ == '__main__':
    app.run(debug=True)
