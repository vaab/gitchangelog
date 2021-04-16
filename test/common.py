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
import sys

from gitchangelog import gitchangelog

WIN32 = gitchangelog.WIN32


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
        args[0] = args[0].replace("$tprog", tprog)
        return f(*args, **kwargs)

    return _wrapped


def set_env(**se_kwargs):
    def decorator(f):
        def _wrapped(*args, **kwargs):
            env = dict(os.environ)
            for key, value in se_kwargs.items():
                env[key] = value
            env.update(kwargs.get("env") or {})
            kwargs["env"] = env
            return f(*args, **kwargs)

        return _wrapped

    return decorator


BASE_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
tprog = os.path.join(BASE_PATH, "src", "gitchangelog", "gitchangelog.py")

WITH_COVERAGE = gitchangelog.cmd("coverage --version")[2] == 0
if WITH_COVERAGE:
    source = os.path.join(BASE_PATH, "src", "gitchangelog")
    tprog = (
        "coverage run -a --source=%(source)s "
        '--omit="%(omit)s" '
        '--rcfile="%(rcfile)s" "%(tprog)s"'
        % {
            "base_path": BASE_PATH,
            "python": sys.executable,
            "tprog": tprog,
            "source": source,
            "omit": ",".join(
                [
                    os.path.join(source, "__init__.py"),
                    os.path.join(BASE_PATH, "setup.py"),
                    os.path.join(source, "gitchangelog.rc.reference"),
                ]
            ),
            "rcfile": os.path.join(BASE_PATH, ".coveragerc"),
        }
    )
    tprog_set = set_env(COVERAGE_FILE=os.path.join(BASE_PATH, ".coverage.2"), PYTHONPATH=BASE_PATH, tprog=tprog)
else:
    tprog = '"%(python)s" "%(tprog)s"' % {"python": sys.executable, "tprog": tprog}
    if WIN32:
        ## For some reasons, even on 3.6, outputs in tests are in ``cp1252``.
        tprog_set = set_env(PYTHONIOENCODING="utf-8", tprog=tprog)
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

    def assertNoDiff(self, t1, t2, msg=None):
        if WIN32:
            t1 = t1.replace("\r\n", "\n")
            t2 = t2.replace("\r\n", "\n")
        self.assertEqual(t1, t2, msg)


class BaseTmpDirTest(ExtendedTest):
    def setUp(self):
        self.maxDiff = None
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
        self.repos = gitchangelog.GitRepos.create("repos", email="committer@example.com", user="The Committer")
        os.chdir("repos")

    @property
    def git(self):
        return self.repos.git

    @property
    def changelog(self):
        ## Currifyed main function
        return lambda **kw: gitchangelog.changelog(repository=self.repos, **kw)

    @property
    def raw_changelog(self):
        ## Currifyed main function
        return lambda **kw: gitchangelog.changelog(repository=self.repos, output_engine=raw_renderer, **kw)

    @property
    def simple_changelog(self):
        ## Currifyed main function
        return lambda **kw: gitchangelog.changelog(repository=self.repos, output_engine=simple_renderer, **kw)
