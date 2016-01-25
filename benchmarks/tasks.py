import os
import json
import urlparse
import subprocess

from crayonbox import celery_app
from django.conf import settings
from django.core.files.base import ContentFile
from celery.utils.log import get_task_logger
from benchmarks.models import Benchmark, ResultData

from . import testminer


logger = get_task_logger(__name__)


def _set_testjob_results(testjob):

    netloc = urlparse.urlsplit(testjob.testrunnerurl).netloc
    username, password = settings.CREDENTIALS[netloc]
    tester = getattr(testminer, testjob.testrunnerclass)(testjob.testrunnerurl, username, password)

    testjob.status = tester.get_test_job_status(testjob.id)
    testjob.url = tester.get_job_url(testjob.id)

    if not testjob.initialized:
        testjob.testrunnerclass = tester.get_result_class_name(testjob.id)
        testjob.initialized = True
        testjob.save()
        tester = getattr(testminer, testjob.testrunnerclass)(testjob.testrunnerurl, username, password)

    if testjob.status not in ["Complete", "Incomplete", "Canceled"]:
        testjob.save()
        return

    testjob.definition = tester.get_test_job_details(testjob.id)['definition']
    testjob.completed = True
    test_results = tester.get_test_job_results(testjob.id)

    if not test_results:
        testjob.status = "Results Missing"
        testjob.save()
        return

    datafile_name, datafile_content = tester.get_result_data(testjob.id)
    datafile = ContentFile(datafile_content)

    testjob.data.save(datafile_name, datafile, save=False)
    testjob.save()

    for result in test_results:
        benchmark, _ = Benchmark.objects.get_or_create(
            name=result['benchmark_name']
        )

        for subscore in result['subscore']:
            ResultData.objects.create(
                name=subscore['name'],
                measurement=subscore['measurement'],
                board=result['board'],
                result=testjob.result,
                benchmark=benchmark
            )

    testjob.save()
    tester.cleanup()

    # ToDo: not implemented yet. DO NOT REMOVE
    #for result in test_results['test']:
    #    name = result['testdef']
    #    if 'results' in result.keys():
    #        print "\t\tTest(%s): %s" % (name, result['result'])
    #    if 'parameters' in result.keys():
    #        print "\t\t\tParameters: %s" % (result['parameters'])
    #        print result['parameters'].__class__.__name__
    #    if 'results' in result.keys() and result['result'] == 'fail':
    #        print "\t\t\tReason: %s" % (result['reason'])
    #    version = ''
    #    if 'version' in result.keys():
    #        version = result['version']
    #    parameters = {}
    #    if 'parameters' in result.keys():
    #        parameters = result['parameters']


@celery_app.task(bind=True)
def set_testjob_results(self, testjob):

    logger.info("Fetch benchmark results for %s" % testjob)

    _set_testjob_results(testjob)

    if not testjob.completed:
        logger.info("Testjob for %s not completed, restarting" % testjob)
        set_testjob_results.apply_async(args=[testjob], countdown=300)
    else:
        logger.info("Testjob for %s completed" % testjob)



def _sync_external_repos():
    base = settings.EXTERNAL_DIR['BASE']
    for name, address in settings.EXTERNAL_DIR['REPOSITORIES']:

        logger.info("Repository: %s" % address)

        repo_path = os.path.join(base, name)
        if not os.path.exists(repo_path):
            subprocess.check_call(['git', 'clone', address, repo_path], cwd=base)
        else:
            subprocess.check_call(['git', 'pull'], cwd=repo_path)


@celery_app.task(bind=True)
def sync_external_repos(self):
    _sync_external_repos()
