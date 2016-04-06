import os
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.utils import timezone

from django_dynamic_fixture import G

from benchmarks.models import Result, ResultData, TestJob, Manifest, Benchmark


MINIMAL_XML = '<?xml version="1.0" encoding="UTF-8"?><body></body>'
FULL_MANFIEST = open(os.path.join(os.path.dirname(__file__), 'manifest.xml')).read()


class ManifestTest(TestCase):

    def test_complete_1(self):
        manifest = Manifest.objects.create(manifest=FULL_MANFIEST)

        self.assertEqual(manifest.reduced.hash, '0efe8e2c8c680e488049abc8fd28941fb828bc95')


class ResultTestCase(TestCase):

    def test_complete_1(self):
        result = G(Result, manifest__manifest=MINIMAL_XML)

        self.assertEqual(result.completed, False)

        G(TestJob, result=result, completed=True)
        G(TestJob, result=result, completed=True)

        self.assertEqual(result.completed, True)

    def test_complete_2(self):
        result = G(Result, manifest__manifest=MINIMAL_XML)

        testjob = G(TestJob, result=result, completed=False)

        self.assertEqual(result.completed, False)
        testjob.completed = True
        self.assertEqual(result.completed, False)

class ResultManagerTestCase(TestCase):

    def test_compare_against_baseline_with_some_missing_benchmarks(self):
        new_build = G(
            Result,
            manifest__manifest=MINIMAL_XML,
            branch_name='master',
            gerrit_change_number=123,
        )

        baseline = G(
            Result,
            manifest__manifest=MINIMAL_XML,
            branch_name='master',
            gerrit_change_number=None,
        )

        benchmark1 = G(Benchmark)
        benchmark2 = G(Benchmark)

        G(ResultData,
          result=new_build,
          benchmark=benchmark1,
          name="load-avg",
          measurement=5)
        G(ResultData,
          result=new_build,
          benchmark=benchmark2,
          name="cpu-usage",
          measurement=5)

        # baseline missing result for benchmark2
        G(ResultData,
          result=baseline,
          benchmark=benchmark1,
          name="load-avg",
          measurement=5)

        # should just not crash
        Result.objects.compare(new_build, baseline)


class ResultDataTestCase(TestCase):

    def test_compare_progress_1(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1a = G(Result,
                      name="name1",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=now)

        result_1b = G(Result,
                      name="name2",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=now)

        result_2a = G(Result,
                      name="name1",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=then)

        result_2b = G(Result,
                      name="name1",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=then)

        G(ResultData,
          result=result_1a,
          benchmark__name="load-a",
          name="load-avg",
          measurement=5)

        G(ResultData,
          result=result_2a,
          benchmark__name="load-a",
          name="load-avg",
          measurement=10)

        G(ResultData,
          result=result_1b,
          benchmark__name="load-b",
          name="load-avg",
          measurement=5)

        G(ResultData,
          result=result_2b,
          benchmark__name="load-b",
          name="load-avg",
          measurement=10)

        compare = Result.objects.compare_progress(now, timedelta(days=7))

        self.assertEqual(compare['master'][0]['current'], 5)
        self.assertEqual(compare['master'][0]['previous'], 10)
        self.assertEqual(compare['master'][0]['change'], 50.0)

    def test_compare_progress_2(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1a = G(Result,
                      name="name1",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=now)

        result_1b = G(Result,
                      name="name2",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=now)

        result_2a = G(Result,
                      name="name1",
                      manifest__manifest=MINIMAL_XML,
                      branch_name="master",
                      gerrit_change_number=None,
                      created_at=then)

        G(ResultData,
          result=result_1a,
          benchmark__name="load-a",
          name="load-avg",
          measurement=5)

        G(ResultData,
          result=result_2a,
          benchmark__name="load-a",
          name="load-avg",
          measurement=10)

        G(ResultData,
          result=result_1b,
          benchmark__name="load-b",
          name="load-avg",
          measurement=5)

        compare = Result.objects.compare_progress(now, timedelta(days=7))

        master = [
            {'change': 50.0,
             'current': 5.0,
             'name': u'load-a / load-avg',
             'previous': 10.0},

            {'change': None,
             'current': 5.0,
             'name': u'load-b / load-avg',
             'previous': None}]

        self.assertEqual(compare['master'], master)

    def test_compare_progress_missing_past(self):
        now = timezone.now()

        result = G(Result,
                   manifest__manifest=MINIMAL_XML,
                   branch_name="master",
                   gerrit_change_number=None,
                   created_at=now)

        G(ResultData,
          result=result,
          benchmark__name="load",
          name="load-avg",
          measurement=5)

        compare = Result.objects.compare_progress(
            now, relativedelta(days=7))

        self.assertEqual(compare, {})

    def test_compare_progress_missing_current(self):
        now = timezone.now()
        then = now - timedelta(days=7)

        result = G(Result,
                   manifest__manifest=MINIMAL_XML,
                   branch_name="master",
                   gerrit_change_number=None,
                   created_at=then)

        G(ResultData,
          result=result,
          benchmark__name="load",
          name="load-avg",
          measurement=5)

        compare = Result.objects.compare_progress(
            now, relativedelta(days=7))

        self.assertEqual(compare, {})

    def test_compare_progress_missing_results_current(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=now)

        result_2 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=then)

        G(ResultData,
          result=result_2,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        compare = Result.objects.compare_progress(now, timedelta(days=7))
        self.assertEqual(compare, {})

    def test_compare_progress_missing_results_previous(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=now)

        result_2 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=then)

        G(ResultData,
          result=result_1,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        compare = Result.objects.compare_progress(now, timedelta(days=7))
        self.assertEqual(compare, {})

    def test_to_compare_missing_results_current(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=123,
                     created_at=now)

        result_2 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=then)

        G(ResultData,
          result=result_2,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        self.assertEqual(result_1.to_compare(), None)

    def test_to_compare_missing_results_previous(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=123,
                     created_at=now)

        result_2 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=then)

        G(ResultData,
          result=result_1,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        self.assertEqual(result_1.to_compare(), None)

    def test_to_compare(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        result_1 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=123,
                     created_at=now)

        result_2 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=then)

        result_3 = G(Result,
                     manifest__manifest=MINIMAL_XML,
                     branch_name="master",
                     gerrit_change_number=None,
                     created_at=then)

        G(ResultData,
          result=result_1,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        G(ResultData,
          result=result_3,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        self.assertEqual(result_1.to_compare(), result_3)

    def test_to_compare_for_baseline_builds(self):

        now = timezone.now()
        then = now - relativedelta(days=7)

        current_master = G(Result,
                           manifest__manifest=MINIMAL_XML,
                           branch_name="master",
                           gerrit_change_number=None,
                           created_at=now)

        previous_master = G(Result,
                            manifest__manifest=MINIMAL_XML,
                            branch_name="master",
                            gerrit_change_number=None,
                            created_at=then)

        G(ResultData,
          result=current_master,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        G(ResultData,
          result=previous_master,
          benchmark__name="load",
          name="load-avg",
          measurement=10)

        self.assertEqual(previous_master, current_master.to_compare())

class TestJobTestCase(TestCase):

    def test_metadata_is_empty_by_default(self):
        job = TestJob()
        self.assertEqual({}, job.metadata)

    def test_invalid_json(self):
        job = TestJob(definition='//')
        job.__extract_metadata__()
        self.assertEqual({}, job.metadata)

    def test_extract_metadata_from_empty_definition(self):
        job = TestJob(definition=None)
        job.__extract_metadata__() # just not crashing is good enough here

    def test_extract_metadata_from_json_definition(self):
        job = TestJob(definition='{ "metadata" : { "foo": "bar", "baz": "qux" } }')
        job.__extract_metadata__()

        self.assertEqual(job.metadata['foo'], 'bar')
        self.assertEqual(job.metadata['baz'], 'qux')

    def test_extract_metadata_from_nested_metadata(self):
        job = TestJob(definition='{ "something": { "name": "foobar", "metadata" : { "foo": "bar", "baz": "qux" } } }')
        job.__extract_metadata__()

        self.assertEqual(job.metadata['foo'], 'bar')
        self.assertEqual(job.metadata['baz'], 'qux')

    def test_extract_metadata_from_lava_job(self):
        job = TestJob(definition=u'{"actions": [{"command": "dummy_deploy", "metadata": {"foo": "bar"}}]}')
        job.__extract_metadata__()
        self.assertEqual(job.metadata['foo'], 'bar')

    def test_extracts_metadata_before_saving(self):
        result = G(Result, manifest__manifest=MINIMAL_XML)
        job = TestJob(result=result, definition='{"metadata": { "foo" : "bar"}}')
        job.save()
        self.assertEqual("bar", job.metadata['foo'])

    def test_remove_tag(self):
        result = G(Result, manifest__manifest=MINIMAL_XML)
        job = G(TestJob, result=result, definition='{"metadata": { "foo" : "bar"}}')
        self.assertEqual("bar", job.metadata['foo'])
        job.definition = "{}"
        job.save()
        self.assertFalse("foo" in job.metadata.keys())
