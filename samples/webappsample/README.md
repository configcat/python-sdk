# ConfigCat Django Sample App

To run the sample project you need [Django](https://www.djangoproject.com/) and [ConfigCatClient](https://pypi.org/project/configcat-client/) installed.
```
pip install Django
pip install configcat-client
```

### Start sample:
1. Apply migrations (Required for first time only)
```
python manage.py migrate
```
2. Run sample app
```
python manage.py runserver
```

3. Open browser at `http://127.0.0.1:8000/`
