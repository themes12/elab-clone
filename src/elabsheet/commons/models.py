
class TestCaseResult:
    """
    encapsulate one grading result from the grader
    """
    
    RESULT_FAILED = 0
    RESULT_PASSED = 1
    RESULT_SPACEPROBLEM = 2
    RESULT_TIMEOUT = 3
    RESULT_CASEPROBLEM = 4

    def __init__(self, result):
        self.result = result

    @staticmethod
    def create_from_db(result):
        return TestCaseResult(result)
            
    def failed(self):
        return self.result == TestCaseResult.RESULT_FAILED

    def passed(self):
        return self.result == TestCaseResult.RESULT_PASSED

    def space_problem(self):
        return self.result == TestCaseResult.RESULT_SPACEPROBLEM

    def timeout(self):
        return self.result == TestCaseResult.RESULT_TIMEOUT

    def case_problem(self):
        return self.result == TestCaseResult.RESULT_CASEPROBLEM

    def to_db(self):
        return self.result

    def __str__(self):
        if self.passed():
            return 'P'
        elif self.space_problem():
            return 'S'
        elif self.timeout():
            return 'T'
        elif self.case_problem():
            return 'C'
        else:
            return '-'

    def meaning(self):
        if self.passed():
            return 'Passed'
        elif self.space_problem():
            return 'Incorrect spacing'
        elif self.timeout():
            return 'Time exceeded'
        elif self.case_problem():
            return 'Incorrect case'
        else:
            return 'Failed'

TestCaseResult.FAILED = TestCaseResult(TestCaseResult.RESULT_FAILED)
TestCaseResult.PASSED = TestCaseResult(TestCaseResult.RESULT_PASSED)
TestCaseResult.SPACEPROBLEM = TestCaseResult(TestCaseResult.RESULT_SPACEPROBLEM)
TestCaseResult.TIMEOUT = TestCaseResult(TestCaseResult.RESULT_TIMEOUT)
TestCaseResult.CASEPROBLEM = TestCaseResult(TestCaseResult.RESULT_CASEPROBLEM)

