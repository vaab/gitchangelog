# -*- encoding: utf-8 -*-
"""

Each tests should start in an empty directory that will be destroyed at the end.



"""

from __future__ import unicode_literals

import unittest
import tempfile
import os
import os.path
import shutil
import re

from gitchangelog import gitchangelog

WIN32 = gitchangelog.WIN32


def file_put_contents(filename, string):
    """Write string to filename."""

    with open(filename, 'w') as f:
        f.write(string)


def raw_renderer(data, opts):
    return data


def simple_renderer(data, opts):
    """Provide a fixed template for tests.

    To use when checking what commits gets attributed to which
    versions/sections.

    Do not use if you want to check body contents as it is not printed.

    """
    s = ""
    for version in data["versions"]:
        s += "%s\n" % version["tag"]
        for section in version["sections"]:
            s += "  %s:\n" % section["label"]
            for commit in section["commits"]:
                s += "    * %(subject)s [%(author)s]\n" % commit
        s += "\n"
    return s


def replace_tprog(f):

    def _wrapped(*args, **kwargs):
        args = list(args)
        args[0] = args[0].replace('$tprog', tprog)
        return f(*args, **kwargs)
    return _wrapped


def set_env(**se_kwargs):

    def decorator(f):

        def _wrapped(*args, **kwargs):
            kwargs["env"] = dict(kwargs.get("env") or os.environ)
            for key, value in se_kwargs.items():
                kwargs["env"][key] = value
            return f(*args, **kwargs)
        return _wrapped
    return decorator

BASE_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    ".."))
tprog = os.path.join(BASE_PATH, "src", "gitchangelog", "gitchangelog.py")

WITH_COVERAGE = gitchangelog.cmd(
    "%s coverage" % ("where" if WIN32 else "type"))[2] == 0
if WITH_COVERAGE:
    tprog = ('coverage run -a --source=%(base_path)s '
             '--omit=%(base_path)s/setup.py,'
             '%(base_path)s/gitchangelog.rc* '
             '--rcfile="%(base_path)s/.coveragerc" %(tprog)s'
             % {'base_path': BASE_PATH,
                'tprog': tprog})
    tprog_set = set_env(
        COVERAGE_FILE="%s/.coverage.2" % BASE_PATH,
        PYTHONPATH="%s" % BASE_PATH,
        tprog=tprog)
else:
    tprog_set = set_env(tprog=tprog)

w = replace_tprog(tprog_set(gitchangelog.wrap))
cmd = replace_tprog(tprog_set(gitchangelog.cmd))


class ExtendedTest(unittest.TestCase):

    def assertContains(self, haystack, needle, msg=None):
        if not msg:
            msg = "%r should contain %r." % (haystack, needle)
        self.assertTrue(needle in haystack, msg)

    def assertNotContains(self, haystack, needle, msg=None):
        if not msg:
            msg = "%r should not contain %r." % (haystack, needle)
        self.assertTrue(needle not in haystack, msg)

    def assertRegex(self, text, regex, msg=None):
        if not msg:
            msg = "%r should match regex %r." % (text, regex)
        self.assertTrue(re.search(regex, text, re.MULTILINE) is not None, msg)


class BaseTmpDirTest(ExtendedTest):

    def setUp(self):
        ## put an empty tmp directory up
        self.old_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        ## put an empty tmp directory up
        os.chdir(self.old_cwd)

        ## This is due to windows having loads of read-only files
        ## in unexpected places.
        def onerror(func, path, exc_info):

            import stat
            if not os.access(path, os.W_OK):
                # Is the error an access error ?
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise
        shutil.rmtree(self.tmpdir, onerror=onerror)


class BaseGitReposTest(BaseTmpDirTest):

    def setUp(self):
        super(BaseGitReposTest, self).setUp()
        self.repos = gitchangelog.GitRepos.create(
            "repos",
            email="committer@example.com",
            user="The Committer")

    @property
    def git(self):
        return self.repos.cmd

    @property
    def raw_changelog(self):
        ## Currifyed main function
        return lambda **kw: gitchangelog.changelog(
            repository=self.repos, output_engine=raw_renderer, **kw)

    @property
    def simple_changelog(self):
        ## Currifyed main function
        return lambda **kw: gitchangelog.changelog(
            repository=self.repos, output_engine=simple_renderer, **kw)
