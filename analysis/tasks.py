from __future__ import absolute_import

from celery import shared_task
# from django.utils import timezone

# from .models import TodoList, Exchange, Offer
# from .utils import lend

@shared_task #(name='')
def prepare():
    return