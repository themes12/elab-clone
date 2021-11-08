import time
import datetime 
import os
import os.path
import sys

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from elabsheet import settings
from lab.models import Submission

SLEEP_INTERVAL = 1

def get_stop_filename(pid):
    return os.path.join(settings.BASE_DIR, 'grader', 'stop.%d' % pid)

def check_stop_file(pid):
    return os.path.exists(get_stop_filename(pid))

def delete_stop_file(pid):
    os.remove(get_stop_filename(pid))


def save_grading_result(submission, 
                        grading_results, 
                        manual_grading_results, 
                        compiler_messages,
                        start_time):
    result_list = [r['passed'] for r in grading_results]
            
    submission.compiler_messages = compiler_messages
    submission.results = result_list
    submission.manual_scores = manual_grading_results
    submission.start_grading_at = start_time
    submission.graded_at = timezone.now()
    submission.code_grading_status = Submission.CODE_STATUS_GRADED
    
    submission.save()



class Command(BaseCommand):

    help = 'Run a grader'

    @property
    def now(self):
        return timezone.localtime(
                timezone.now()).strftime("[%Y-%m-%d %H:%M:%S.%f]")

    def log(self, msg, style=lambda x:x):
        print(self.now,msg,file=self.log_file)
        self.log_file.flush()
        if self.isatty:
            self.stdout.write(self.now + " " + style(msg))

    def log_output(self, submission, compiler_messages, output_buffer):
        print("Submission: %d\n"
              "User: %d\n"
              "Graded at: %s" %
              (submission.id,
               submission.user_id,
               submission.graded_at),
              file=self.output_log_file)
        print("Compiler messages: %s" % compiler_messages, file=self.output_log_file)
        case_num = 1
        for output in output_buffer:
            case_num += 1
            print("#%d:" % case_num, file=self.output_log_file)
            print(output, file=self.output_log_file)
        print("---", file=self.output_log_file)
        self.output_log_file.flush()


    def handle(self, *args, **options):
        # TODO: when called with 'stop' argument, stop other graders
        #if (len(sys.argv)>1) and (sys.argv[1]=='stop'):
        #    # stop other graders
        #    for pid_str in sys.argv[2:]:
        #        open(get_stop_filename(int(pid_str)),'w')
        #    return

        self.isatty = sys.stdout.isatty()

        # get my pid, will keep logs in log/{pid}.log and log/output.{pid}.log
        my_pid = os.getpid()
        log_filename = os.path.join(settings.GRADER_LOG_DIR, '%d.log' % my_pid)
        self.log_file = open(log_filename,'a+')

        self.log("Grader started with PID {}".format(my_pid), style=self.style.SUCCESS)
        self.log("Log file: {}".format(log_filename), style=self.style.WARNING)

        if settings.GRADER_OUTPUT_LOG:
            self.output_log_file = open(os.path.join(settings.GRADER_LOG_DIR,
                                                ('output.%d.log' % my_pid)),
                                   'a+')

        while True:
            if check_stop_file(my_pid):
                delete_stop_file(my_pid)
                break

            submission = Submission.fetch_one_inqueue_submission()

            if submission != None:
                self.log("Grading (submission:{} task:{} user:{} section:{})"
                         " submitted at {}".format(
                    submission.id, 
                    submission.assignment.task_id, 
                    submission.user, 
                    submission.section_id,
                    timezone.localtime(submission.submitted_at).strftime("%Y-%m-%d %H:%M:%S"),
                    ), style=self.style.WARNING)
                submission.make_task_concrete()
                task = submission.assignment.task
                if settings.GRADER_OUTPUT_LOG:
                    output_buffer = []
                else:
                    output_buffer = None
                start_time = timezone.now()

                os.putenv("SUBMITTER",submission.user.username)

                # XXX get into codeSeg.sequence to get the list of blanks

                grading_results, messages = task.verify_with_messages(submission.answer,output_buffer)
                manual_grading_results = task.verify_manual_auto_gradable_fields(submission.answer)
                save_grading_result(submission, 
                                    grading_results, 
                                    manual_grading_results,
                                    messages,
                                    start_time)

                self.log("result [{}]".format(
                    "".join(str(r) for r in submission.results),
                    ), style=self.style.SUCCESS)

                if settings.GRADER_OUTPUT_LOG:
                    log_output(output_log_file, submission, 
                               messages, output_buffer)
            else:
                time.sleep(SLEEP_INTERVAL)

        self.log_file.close()
        if settings.GRADER_OUTPUT_LOG:
            self.output_log_file.close()

