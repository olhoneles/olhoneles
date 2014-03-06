run:
	python manage.py runserver 0.0.0.0:8000

data:
	python manage.py syncdb --migrate

setup:
	pip install -r requirements.txt
