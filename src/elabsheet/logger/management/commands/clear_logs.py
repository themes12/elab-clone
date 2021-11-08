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

    help = 'Clear logs between the specified time interval'

    def add_arguments(self, parser):
        parser.add_argument('start-time', type=str)
        parser.add_argument('stop-time', type=str)

    def handle(self, *args, **options):
        q = Q()
        start_time_str = "the earliest log"
        end_time_str = "the last log"
        if options['start-time'] != '-':
            start_time = timezone.make_aware(datetime.strptime(options['start-time'],DATETIME_FMT))
            q &= Q(created_at__gt=start_time)
            start_time_str = start_time.strftime(DATETIME_FMT)
        if options['stop-time'] != '-':
            end_time = timezone.make_aware(datetime.strptime(options['stop-time'],DATETIME_FMT))
            q &= Q(created_at__lt=end_time)
            end_time_str = end_time.strftime(DATETIME_FMT)

        print("WANRING: All logs between {} and {} will be cleared.".format(
            start_time_str,
            end_time_str,
            ))
        confirm = input("Deleting {} logged entries.  Continue (y/N)? ".format(
            Log.objects.filter(q).count()))

        if confirm == 'y':
            print("Deleting logs...")
            count,_ = Log.objects.filter(q).delete()
            print("{} log(s) deleted.".format(count))
        else:
            print("Operation canceled")

