from django.test import TestCase
from cms.models import Task,ChildTask,ChildTaskException,CachedChildTask
from textwrap import dedent

########################
class TestSuperTask(TestCase):

    ######################
    GENERATOR = dedent("""\
        def generate(seed,difficulty):
            x = seed+2
            y = seed*5
            output32 = x*32+y
            output79 = x*79+y
            return locals()
        """)

    ########################
    MARKDOWN = dedent("""\
        Test SuperTask
        ==============

        Child task generated with SEED=@seed@, DIFFICULTY=@difficulty@, x=@x@, y=@y@

        Your seed is {{@seed@}}.

        Read an integer input, r, then compute and print out the value of @x@*r+@y@.

        Examples
        --------
        <pre class="output">
        Enter r: <em>32</em>
        The output is @output32@
        </pre>

        <pre class="output">
        Enter r: <em>79</em>
        The output is @output79@
        </pre>

        Code
        ----
        ::elab:begincode blank=True
        r = int(input('Enter r: '))
        print(f"The output is {@x@*r+@y@}")
        ::elab:endcode

        ::elab:begintest
        10
        ::elab:endtest""")

    ########################
    HTML_TEMPLATE=dedent("""\
        <h1>Test SuperTask</h1><p>Child task generated with SEED=@seed@, DIFFICULTY=@difficulty@, x=@x@, y=@y@</p><p>Your seed is <input class="textblank" name="b2" size="9" type="text" value="{{b2}}" />.</p><p>Read an integer input, r, then compute and print out the value of @x@*r+@y@.</p><h2>Examples</h2><p><pre class="output">
        Enter r: <em>32</em>
        The output is @output32@
        </pre></p><pre class="output">
        Enter r: <em>79</em>
        The output is @output79@
        </pre>
        <h2>Code</h2><p><fieldset><pre><code class="source"><textarea class="codeblank" cols="42" name="b1" rows="2" wrap="off">{{b1}}</textarea></code></pre></fieldset></p>""")

    def setUp(self):
        task = Task(
                name="Test SuperTask",
                source=self.MARKDOWN,
                language="python3",
                generator=self.GENERATOR,
                )
        task.save()
        self.task_id = task.id

    def test_markdown(self):
        task = Task.objects.get(pk=self.task_id)
        #print(task.html_template)
        self.assertEqual(task.html_template, self.HTML_TEMPLATE)

    def generate_test_from_seed(self,seed,run_testcases):
        task = Task.objects.get(pk=self.task_id)
        task.make_concrete(seed,0)
        r = 10
        x = seed+2
        y = seed*5
        output = x*r + y
        self.assertEqual(len(task.testcases),1)
        self.assertEqual(task.testcases[0]['input'],str(r))
        if run_testcases:
            task.run_testcases()
            self.assertEqual(
                task.testcases[0]['output'].strip(),
                f"Enter r: The output is {output}"
            )
        else:
            self.assertEqual(task.testcases[0]['output'],None)

        # check text blank
        self.assertEqual(len(task.textblanks),1)
        self.assertEqual(task.textblanks[0]['solution'],str(seed))

    def test_childtask_withouttest_seed0(self):
        self.generate_test_from_seed(0,False)

    def test_childtask_withouttest_seed58(self):
        self.generate_test_from_seed(58,False)

    def test_childtask_withouttest_seed3339(self):
        self.generate_test_from_seed(3339,False)

    def test_childtask_withtest_seed0(self):
        self.generate_test_from_seed(0,True)

    def test_childtask_withtest_seed58(self):
        self.generate_test_from_seed(58,True)

    def test_childtask_withtest_seed3339(self):
        self.generate_test_from_seed(3339,True)

    def test_childtask_save_exception(self):
        task = Task.objects.get(pk=self.task_id)
        try:
            ChildTask.transform(task,10,0)
            task.save()
            self.fail('Child task must not be allowed to save')
        except ChildTaskException as e:
            pass

    def test_cache_childtask(self):
        task = Task.objects.get(pk=self.task_id)
        seed = 1234
        difficulty = 5
        key = ChildTask.generate_key(seed,difficulty)

        try:
            CachedChildTask.objects.get(parent_task=task,key=key)
            self.fail('Cached child task should not exist')
        except CachedChildTask.DoesNotExist:
            pass

        ChildTask.transform(task,seed=seed,difficulty=difficulty)
        try:
            cache = CachedChildTask.objects.get(parent_task=task,key=key)
            self.assertEqual(cache.source,task.source)
            self.assertEqual(cache.html_template,task.html_template)
            self.assertEqual(cache.code.dump_solution(),task.code.dump_solution())
            self.assertEqual(cache.testcases,task.testcases)
            self.assertEqual(cache.textblanks,task.textblanks)
            self.assertEqual(cache.testcases_evaluated,False)
        except CachedChildTask.DoesNotExist:
            self.fail('Cached child task should exist')


########################
class TestSuperTaskWithAdjustment(TestCase):

    ######################
    GENERATOR = dedent("""\
        def adjust_parameters(seed,difficulty):
            return seed%10, difficulty%5

        def generate(seed,difficulty):
            x = seed+2+difficulty
            y = seed*5+difficulty
            output32 = x*32+y
            output79 = x*79+y
            return locals()
        """)

    ########################
    MARKDOWN = dedent("""\
        Test SuperTask
        ==============

        Child task generated with SEED=@seed@, DIFFICULTY=@difficulty@, x=@x@, y=@y@

        Your seed is {{@seed@}}.

        Read an integer input, r, then compute and print out the value of @x@*r+@y@.

        Examples
        --------
        <pre class="output">
        Enter r: <em>32</em>
        The output is @output32@
        </pre>

        <pre class="output">
        Enter r: <em>79</em>
        The output is @output79@
        </pre>

        Code
        ----
        ::elab:begincode blank=True
        r = int(input('Enter r: '))
        print(f"The output is {@x@*r+@y@}")
        ::elab:endcode

        ::elab:begintest
        10
        ::elab:endtest""")

    ########################
    HTML_TEMPLATE=dedent("""\
        <h1>Test SuperTask</h1><p>Child task generated with SEED=@seed@, DIFFICULTY=@difficulty@, x=@x@, y=@y@</p><p>Your seed is <input class="textblank" name="b2" size="9" type="text" value="{{b2}}" />.</p><p>Read an integer input, r, then compute and print out the value of @x@*r+@y@.</p><h2>Examples</h2><p><pre class="output">
        Enter r: <em>32</em>
        The output is @output32@
        </pre></p><pre class="output">
        Enter r: <em>79</em>
        The output is @output79@
        </pre>
        <h2>Code</h2><p><fieldset><pre><code class="source"><textarea class="codeblank" cols="42" name="b1" rows="2" wrap="off">{{b1}}</textarea></code></pre></fieldset></p>""")

    def setUp(self):
        task = Task(
                name="Test SuperTask",
                source=self.MARKDOWN,
                language="python3",
                generator=self.GENERATOR,
                )
        task.save()
        self.task_id = task.id

    def test_markdown(self):
        task = Task.objects.get(pk=self.task_id)
        #print(task.html_template)
        self.assertEqual(task.html_template, self.HTML_TEMPLATE)

    def generate_test_from_seed_and_diff(self,seed,diff,run_testcases):
        task = Task.objects.get(pk=self.task_id)
        task.make_concrete(seed,diff)
        adjusted_seed = seed % 10
        adjusted_diff = diff % 5
        r = 10
        x = adjusted_seed+2+adjusted_diff
        y = adjusted_seed*5+adjusted_diff
        output = x*r + y
        self.assertEqual(len(task.testcases),1)
        self.assertEqual(task.testcases[0]['input'],str(r))
        if run_testcases:
            task.run_testcases()
            self.assertEqual(
                task.testcases[0]['output'].strip(),
                f"Enter r: The output is {output}"
            )
        else:
            self.assertEqual(task.testcases[0]['output'],None)

        # check text blank
        self.assertEqual(len(task.textblanks),1)
        self.assertEqual(task.textblanks[0]['solution'],str(adjusted_seed))

    def test_childtask_withouttest_0_0(self):
        self.generate_test_from_seed_and_diff(0,0,False)

    def test_childtask_withouttest_58_32(self):
        self.generate_test_from_seed_and_diff(58,32,False)

    def test_childtask_withouttest_3339_810(self):
        self.generate_test_from_seed_and_diff(3339,810,False)

    def test_childtask_withtest_0(self):
        self.generate_test_from_seed_and_diff(0,0,True)

    def test_childtask_withtest_58_32(self):
        self.generate_test_from_seed_and_diff(58,32,True)

    def test_childtask_withtest_3339_810(self):
        self.generate_test_from_seed_and_diff(3339,810,True)

    def test_childtask_save_exception(self):
        task = Task.objects.get(pk=self.task_id)
        try:
            ChildTask.transform(task,10,0)
            task.save()
            self.fail('Child task must not be allowed to save')
        except ChildTaskException as e:
            pass

    def test_cache_childtask(self):
        task = Task.objects.get(pk=self.task_id)
        seed = 1234
        difficulty = 5
        key = ChildTask.generate_key(seed%10,difficulty%5)

        try:
            CachedChildTask.objects.get(parent_task=task,key=key)
            self.fail('Cached child task should not exist')
        except CachedChildTask.DoesNotExist:
            pass

        ChildTask.transform(task,seed=seed,difficulty=difficulty)
        try:
            cache = CachedChildTask.objects.get(parent_task=task,key=key)
            self.assertEqual(cache.source,task.source)
            self.assertEqual(cache.html_template,task.html_template)
            self.assertEqual(cache.code.dump_solution(),task.code.dump_solution())
            self.assertEqual(cache.testcases,task.testcases)
            self.assertEqual(cache.textblanks,task.textblanks)
            self.assertEqual(cache.testcases_evaluated,False)
        except CachedChildTask.DoesNotExist:
            self.fail('Cached child task should exist')

