# tradecultivation

Be sure to have installed Postgres:

`sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib`

Then set it up [like this](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04) with settings matching those in settings.py

Now you are ready to install and run the app:

```
git clone https://github.com/daneri/tradecultivation.git
cd tradecultivation
virtualenv venv
pip install -r requirements.txt
python manage.py runserver (or just manage.py runserver)
Make sure you have installed (RabbitMQ)[https://www.rabbitmq.com/install-debian.html]
In a new terminal screen, run celery -A tradecultivation worker -l info
In a new terminal screen, run celery -A tradecultivation beat -l info
# in production these will be run as daemon
```


## How to force functions to run
```
python manage.py shell
# import the functions you need
from analysis.tasks import prepare, preBuild, build
# run the function
prepare()
preBuild()
build()
```
