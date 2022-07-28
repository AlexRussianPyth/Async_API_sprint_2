# DJANGO
run: 
	python service/manage.py runserver

migration:
	python service/manage.py makemigrations

migrate:
	python service/manage.py migrate

show:
	python service/manage.py showmigrations

superuser:
	DJANGO_SUPERUSER_USERNAME=admin \
	DJANGO_SUPERUSER_PASSWORD=123 \
	DJANGO_SUPERUSER_EMAIL=alexvkleschov@gmail.com \
	python service/manage.py createsuperuser --noinput || true

shell:
	python service/manage.py shell

# Docker
dev-compose:
	docker-compose -f docker-compose.dev.yml up --build