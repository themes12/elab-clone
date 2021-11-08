from django_bootstrap import bootstrap
bootstrap()

import sys
from django.contrib.auth.models import User
import lab.models

##################################
def describe_user(user):
    print("User ID: %d" % (user.id))
    print("Username: %s" % (user.username))
    print("Firstname: %s" % (user.first_name))
    print("Lastname: %s" % (user.last_name))

##################################
def describe_submission(submission):
    print("Submission ID: %d" % (submission.id))
    print("By user: id=%d %s" % (submission.user.id,submission.user.username))
    print("Section: id=%d %s" % (submission.section.id,submission.section))
    print("Assignment: id=%d %s" % (submission.assignment.id,submission.assignment))
    print("Task: id=%d %s" % (submission.assignment.task_id,submission.assignment.task))
    print("Graded: %s" % submission.graded())
    print("Graded at: %s" % submission.graded_at)
    print("Submitted at: %s" % submission.submitted_at)
    print("Remote address: %s" % submission.remote_addr)
    print("Results: [%s]" % "".join([unicode(r) for r in submission.results]))

##################################
def describe_section(section):
    print("Section: id=%d %s" % (section.id,section))
    print("Instructor(s): %s" % ",".join([instr.username for instr in section.instructors.all()]))
    print("Notes: %s" % section.notes)

##################################
def describe_labinsec(labinsec):
    section = labinsec.section
    lab = labinsec.lab
    print("LabInSec (%d): %s" % (labinsec.id,labinsec))
    print("Section (%d): %s" % (section.id,section))
    print("Lab (%d): %s" % (lab.id,lab))
    print("Instructor(s): %s" % ",".join([instr.username for instr in section.instructors.all()]))
    print("Task-ID/Assignment-ID")
    print("---------------------")
    for assignment in lab.assignment_set.all():
        print("%d/%d - %s" % (assignment.task.id,assignment.id,assignment))

##################################
ROUTING = {
    "user-id" : {
        "value-filter" : int,
        "lookup-model" : User,
        "lookup-field" : "pk",
        "describe"     : describe_user,
    },
    "username" : {
        "value-filter" : str,
        "lookup-model" : User,
        "lookup-field" : "username",
        "describe"     : describe_user,
    },
    "submission-id" : {
        "value-filter" : int,
        "lookup-model" : lab.models.Submission,
        "lookup-field" : "pk",
        "describe"     : describe_submission,
    },
    "section-id" : {
        "value-filter" : int,
        "lookup-model" : lab.models.Section,
        "lookup-field" : "pk",
        "describe"     : describe_section,
    },
    "labinsec-id" : {
        "value-filter" : int,
        "lookup-model" : lab.models.LabInSection,
        "lookup-field" : "pk",
        "describe"     : describe_labinsec,
    },
}

if len(sys.argv) != 3:
    print("Usage: %s <key> <value>" % sys.argv[0])
    print("Available keys: %s" % ",".join(ROUTING.keys()))
    exit(1)

key = sys.argv[1]
value = sys.argv[2]

route = ROUTING[key]
val_filter = route["value-filter"]
model = route["lookup-model"]
field = route["lookup-field"]
describe = route["describe"]

kwarg = {field:val_filter(value)}
try:
    record = model.objects.get(**kwarg)
    describe(record)
except model.DoesNotExist:
    print("Object not found.")
