# tradecultivation

git clone https://github.com/daneri/tradecultivation.git
cd tradecultivation
virtualenv venv
pip install -r requirements.txt
# run celery worker and beat as daemon
python manage.py runserver (or just manage.py runserver)