"""

Each tests should start in an empty directory that will be destroyed at the end.



"""


import unittest
import tempfile
import os
import os.path
import shutil


import gitchangelog


def set_env(key, value):

    def decorator(f):

        def _wrapped(*args, **kwargs):
            kwargs["env"] = dict(kwargs.get("env") or os.environ)
            kwargs["env"][key] = value
            return f(*args, **kwargs)
        return _wrapped
    return decorator

tprog = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..", "gitchangelog.py")

w = set_env("tprog", tprog)(gitchangelog.wrap)
cmd = set_env("tprog", tprog)(gitchangelog.cmd)


class ExtendedTestCase(unittest.TestCase):

    def assertContains(self, haystack, needle, msg=None):
        if not msg:
            msg = "%r should contain %r." % (haystack, needle)
        self.assertTrue(needle in haystack, msg)


class BaseTmpDirTest(ExtendedTestCase):

    def setUp(self):
        ## put an empty tmp directory up
        self.old_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        ## put an empty tmp directory up
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)


class BaseGitReposTest(BaseTmpDirTest):
    """Base for all tests needing to start in a new git small repository"""

    def setUp(self):
        super(BaseGitReposTest, self).setUp()
        ## offer $tprog ENVIRON variable to call the test program

        w("""

            ## Creating repository
            mkdir repos
            cd repos
            git init .

            ## Adding first file
            echo 'Hello' > a
            git add a
            git commit -m 'first commit'
            git tag 0.0.1

            ## Adding second file
            echo 'Second file' > b
            git add b
            git commit -m 'new: added file \`\`b\`\`'
            git tag 0.0.2

            """)
        os.chdir("repos")


class GitChangelogTestCase(BaseGitReposTest, ExtendedTestCase):
    pass
