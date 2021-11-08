import time
from datetime import datetime
import os
import os.path
import sys

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from logger.models import Log
from django.db.models import Q

DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

class Command(BaseCommand):

    help = 'Dump logs between the specified time interval'

    def add_arguments(self, parser):
        parser.add_argument('start-time', type=str)
        parser.add_argument('stop-time', type=str)

    def handle(self, *args, **options):
        q = Q()
        if options['start-time'] != '-':
            start_time = timezone.make_aware(datetime.strptime(options['start-time'],DATETIME_FMT))
            q &= Q(created_at__gt=start_time)
        if options['stop-time'] != '-':
            end_time = timezone.make_aware(datetime.strptime(options['stop-time'],DATETIME_FMT))
            q &= Q(created_at__lt=end_time)

        for entry in Log.objects.filter(q):
            print(entry)

