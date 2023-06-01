# Personal Timeline UI

Create and activate a new conda env:
```
conda create -n digital_data python=3.10
conda activate digital_data
```

Install nodejs and yarn:
```
conda install -c conda-forge nodejs==18.10.0 yarn
```

Install some react libraries:
```
yarn add primereact primeicons video-react react-timelines @react-google-maps/api @uiw/react-heat-map react-syntax-highlighter @babel/runtime
```


## Data preparation

Data should be stored under `public/digital_data/`. For testing, you can copy the anonymized sample [data](../../sample_data/) from the main directory by running:
```
cp -r ../../sample_data public/digital_data/
```

Files under this directory are:
* `episodes.csv`: the csv table containing all episodes for rag-based QA
* `books.json`, `exercise.json`, `photos.json`, `places.json`, `purchase.json`, `streaming.json`, `trips.json`: these are episodes in JSON format for visualization.

Images (for serving) should be stored under `public/digital_data/images/`.


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

