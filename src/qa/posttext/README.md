# PostText

Create and activate a new conda env:
```
conda create -n posttext python=3.10
conda activate posttext
```

Install nodejs and yarn:
```
conda install -c conda-forge nodejs==18.10.0 yarn
```

Install some react libraries:
```
npm install primereact primeicons
npm install react-syntax-highlighter
```

Install python packages (for backend):
```
conda install --file requirements.txt
```

### To build and start the React frontend

```
cd frontend/
yarn
yarn build
yarn start
```

The homepage should be available at `http://localhost:3000/`. 

The frontend code is at `frontend/src/App.js`.

## To start the Flask backend

To run the backend, you will need to set up an OpenAI API [here](https://openai.com/api/).

After that, add the API key to your env variables:

```
export OPENAI_API_KEY=<api_key_goes_here>
```

```
python server.py
```

You can test the backend by curl
```
curl http://127.0.0.1:5000/test
```

You should get:
```
{
  "message": "okay"
}
```

## To prepare a new dataset for querying by posttext, you need to set up a few things:

The following assumes you have a dataset (in csv) you wish to query and a number of views (in csv) over the dataset. 
All the files reside in the same directory. There should be a config.ini file in the same directory. 
You can copy the config.ini file from TimelineQA to this directory. If you do not have a config.ini file, execute the following command to create one.

```
python util/create_config_file.py
```

### Describe your views in a file:

Create a file that contains a description of your views so that posttext knows how to leverage the views. For example, the description of views for TimelineQA dataset is described in TimelineQA/views_metadata.txt

After you have completed the description, specify the path of your description file in config.ini under [input] --> "views_metadata".

### Create an index of the metadata:

Create an index of embeddings of your metadata description. To do this, execute:

```
python create_metadata_idx.py <views_description file from above> <your config.ini file> <output_file_name>
```

For example:

```
python create_metadata_idx.py views_metadata.txt config.ini views_idx.csv
```

This command only needs to be executed once. After the views_idx.csv file is created, PostText will read from the idx file. Specify the path of your index file in config.ini under [input] --> "views_metadata_idx".


### Create views db in sqlite from csv files:

Assuming your views are described in .csv files, update the script "create_db.sql" to import the views you have.
You will need to specify the schema before you execute import statements in create_db.sql. For SQLite, specify TEXT for date types. 

After this, execute:
```
```rm -f views_db.sqlite;sqlite3 views_db.sqlite ".read create_db.sql"```
```

This will create a views_db.sqlite file by importing data from your csv files. Once you have the file views_db.sqlite, you will not need to run this command again. PostText will read views_db.sqlite to access the views.

Specify the path of views_db.sqlite in config.ini under [input] --> "views_db".

### Create a vectorstore of embeddings of the dataset:

To do this execute:
```
python data2vectorstore.py <your dataset csv filename>
```

This command will generate a file called output.pkl. You can move this file to a suitable directory and specify the path of this file in config.ini under [input] --> "source_idx". Once you have this file, you do not need to execute this command again.

### Create a vectorstore of embeddings of the dataset:
Make sure your PYTHONPATH contains the root directory of posttext.
For example:

```
echo PYTHONPATH = "${PYTHONPATH}:<path to root of posttext dir where src and util are subdirectories>"
```
