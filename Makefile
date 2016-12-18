all: tests

run:
	@python manage.py runserver 0.0.0.0:8000

data:
	@python manage.py migrate

setup:
	@pip install -U --process-dependency-links -e .\[tests\]

test: lint unit

unit:
	@coverage run --source='.' manage.py test -s
	@coverage report -m


focus:
	@python manage.py test --with-focus -s

clean:
	@rm -f *.log

publish:
	@python setup.py sdist upload

lint:
	@pycodestyle

static:
	@python manage.py collectstatic --noinput
