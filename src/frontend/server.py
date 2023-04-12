import os
import sys
import inspect
import os.path as osp
from flask_cors import CORS

from flask import Flask, redirect, url_for, request, render_template, send_from_directory
from backend.qa_engine import QAEngine
from backend.chatgpt_engine import ChatGPTEngine
# from posttext import PostText

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


app = Flask(__name__)
CORS(app)

# # for profiling
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)


# create CLIP search engine
clip_search_engine = None

# the preprocessed aria video path in mp4 format
# if it is a symbolic link to a manifold bucket, it might create latency to display it
aria_video_path = "data/videos"

# the preprocessed aria thumbnail path in jpg format
# if it is a symbolic link to a manifold bucket, it might create latency to display all
aria_thumbnail_path = "data/clip_search/lifelog_thumbnails"

# asset_folder = "/Users/zhaoyang/develop/EgoQA/research_ui/public"
asset_folder = "public"

# Digital data QA engine
qa_engine = None

# ChatGPT Engine (for baseline purpose)
chatgpt_engine = ChatGPTEngine()

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

@app.route('/launch', methods=['GET'])
def launch():
    """Launch a query engine.
    """
    dataset = request.args.get('dataset')
    global qa_engine
    global clip_search_engine

    if dataset == 'Aria':
        from lib.clip_search_lifelog.clip_search_engine import ClipSearchEngine
        clip_search_engine = ClipSearchEngine(manifold_mount_path="public/data")
    elif dataset == 'Digital':
        qa_engine = QAEngine('public/digital_data')
    elif 'Aria Pilot' in dataset:
        # Aria Pilot User 0
        uid = int(dataset.split(' ')[-1])
        qa_engine = QAEngine('public/aria_pilot/aria_pilot_dataset_user_%d' % uid)

    return {'message': 'okay'}


@app.route('/query', methods=['GET'])
def query():
    """Query the posttext engine.
    """
    # return {'message': 'okay'}
    query = request.args.get('query')
    method = request.args.get('qa')
    print(method)

    if method == 'ChatGPT':
        return {"question": query, "method": method, "answer": chatgpt_engine.query(query), "sources": []}

    # embedding-based QA
    if qa_engine != None:
        res = qa_engine.query(query, method=method)
        res["method"] = method
        return res

    # CLIP search
    print(f"search recordings for {query}")
    (
        gaia_ids,
        frame_indices,
        sim_scores,
    ) = clip_search_engine.query_text2vid(query_text=query, top_k=10)

    clip_search_result = f"Found top-{len(gaia_ids)} matching recordings."

    # fetch the top-1 most relevant video that exists
    # fetch the top-K thumbnails
    video_url = None
    thumbnail_paths = []
    for idx, (gaia_id, frame_idx) in enumerate(zip(gaia_ids, frame_indices)):
        t_path = osp.join(aria_thumbnail_path, f"{gaia_id}", "thumbnails", "thumbnail_{:05d}.jpg".format(frame_idx))

        if video_url is None:
            video_url = osp.join(aria_video_path, f"movie_{gaia_ids[0]}.mp4")
            if not osp.exists(osp.join(asset_folder, video_url)):
                print(f"Did not find video for {video_url}. Seek the next top relevant video path.")
                video_url = None

        thumbnail_paths.append({
            "itemImageSrc": t_path,
            "thumbnailImageSrc": t_path,
            "alt": f"thumbnail_top_{idx}",
            "title": f"thumbnail_top_{idx}",
        })

    # fetch the worldstates
    worldstate = {
        "data": "",
        "gaia_ids": gaia_ids,
    }

#     prompt, sql_before, sql_after, result = engine.query(q)
#     return {'prompt': prompt,
#             'sql_before': sql_before,
#             'sql_after': sql_after,
#             'result': result}

    print(video_url)

    return {'gaia_ids': gaia_ids,
            'video_url': video_url,
            'image_paths': thumbnail_paths,
            "query": query,
            "world_state": worldstate}


if __name__ == '__main__':
    app.run(host="::", port=8085, debug=True)
