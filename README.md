# tradecultivation


`git clone https://github.com/daneri/tradecultivation.git
cd tradecultivation
virtualenv venv
pip install -r requirements.txt
python manage.py runserver (or just manage.py runserver)
Make sure you have installed (RabbitMQ)[https://www.rabbitmq.com/install-debian.html]
In a new terminal screen, run celery -A tradecultivation worker -l info
In a new terminal screen, run celery -A tradecultivation beat -l info
# in production these will be run as daemon`
