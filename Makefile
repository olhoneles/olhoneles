all: tests

run:
	@python manage.py runserver 0.0.0.0:8000

data:
	@python manage.py migrate

setup:
	@pip install -U -e .\[tests\]

tests:
	@coverage run --source='.' manage.py test
	@coverage report -m

clean:
	@rm -f *.log

publish:
	@python setup.py sdist upload
