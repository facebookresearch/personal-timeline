## Installing dependencies

Create and activate a new conda env:
```
conda create -n digital_data python=3.10
conda activate digital_data
```

Install python packages:
```
pip install -r requirements.txt
```

## To start the Flask backend

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