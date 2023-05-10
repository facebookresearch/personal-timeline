# Personal Timeline

Create and activate a new conda env:
```
conda create -n research_ui python=3.10
conda activate research_ui
```

Install nodejs and yarn:
```
conda install -c conda-forge nodejs==18.10.0 yarn
```

Install some react libraries:
```
yarn add primereact primeicons video-react react-timelines @react-google-maps/api @uiw/react-heat-map react-syntax-highlighter @babel/runtime
```

Install python packages (for backend):
```
pip install -r requirements.txt
```

## Data preparation

Data should be stored under `public/digital_data/`. Files under this directory are:
* `episodes.csv`: the csv table containing all episodes for rag-based QA
* `books.json`, `exercise.json`, `photos.json`, `places.json`, `purchase.json`, `streaming.json`, `trips.json`: these are episodes in JSON format for visualization.

Images (for serving) should be stored under `public/digital_data/images/`.

We also provide a sampled anonymized digital dataset (TODO: add dataset description).


## To build and start the React frontend

```
yarn
yarn start
```

The homepage should be available at `http://localhost:3000/`. The frontend code is at `frontend/src/App.js`.

### To build and serve the frontend:
```
yarn build
npx serve -s build
```

## To start the Flask backend (for QA)

```
python server.py
```

You can test the backend by curl
```
curl http://127.0.0.1:8085/test
```

You should get:
```
{
  "message": "okay"
}
```

