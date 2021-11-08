from django.template.loader import render_to_string

def make_result_explanation(submission):
    if not submission.graded():
        return ""
    testcases = submission.assignment.task.testcases
    results = zip(testcases,submission.results)
    return render_to_string(
        'lab/include/explained_results.html',
        { 
            'submission' : submission, 
            'results' : results,
        })


