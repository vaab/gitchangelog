# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest, cmd, gitchangelog


class ExceptionHandlingTest(BaseGitReposTest):
    """Base for all tests needing to start in a new git small repository"""

    def setUp(self):
        super(ExceptionHandlingTest, self).setUp()

        self.git.commit(
            message='new: begin',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

    def test_simple_with_changelog_python_exception(self):

        out, err, errlvl = cmd('$tprog')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertContains(
            err, "--debug",
            msg="Message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "Traceback (most recent call last):",
            msg="The exception msg should NOT contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_simple_show_with_changelog_python_exception_deprecated(self):

        out, err, errlvl = cmd('$tprog show')
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertContains(
            err, "--debug",
            msg="Message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "Traceback (most recent call last):",
            msg="The exception msg should NOT contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_cli_debug_mode(self):

        out, err, errlvl = cmd('$tprog --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_show_with_changelog_python_exc_in_cli_debug_mode_deprecated(self):
        out, err, errlvl = cmd('$tprog --debug show')
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Should contain message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_cli_debug_mode_after(self):
        out, err, errlvl = cmd('$tprog HEAD --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_show_with_changelog_python_exc_in_cli_debug_mode_after_deprecated(self):
        out, err, errlvl = cmd('$tprog show --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Should contain message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_env_debug_mode(self):
        out, err, errlvl = cmd('$tprog', env={"DEBUG_GITCHANGELOG": "1"})
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_show_with_changelog_python_exc_in_env_debug_mode_deprecated(self):
        out, err, errlvl = cmd('$tprog show', env={"DEBUG_GITCHANGELOG": "1"})
        self.assertContains(
            err, "XYZ",
            msg="The exception msg should be displayed and thus contain XYZ... "
            "Current stderr:\n%s" % err)
        self.assertNotContains(
            err, "--debug",
            msg="Should not contain any message about ``--debug``... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "deprecated",
            msg="Should contain message about show being deprecated... "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "Traceback (most recent call last):",
            msg="The exception message should contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 255,
            msg="Should fail with errlvl 255 if exception in output_engine..."
            "Current errlvl: %s" % errlvl)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)
