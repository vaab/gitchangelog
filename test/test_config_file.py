# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os
import textwrap

from .common import BaseGitReposTest, w, cmd, gitchangelog


class BasicCallOnSimpleGit(BaseGitReposTest):

    def setUp(self):
        super(BasicCallOnSimpleGit, self).setUp()

        self.git.commit(
            message='new: begin',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)

    def test_overriding_options(self):
        """We must be able to define a small gitchangelog.rc that override only
        one variable of all the builtin defaults."""

        self.git.commit(
            message='new: first commit',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.tag("v7.0")
        self.git.commit(
            message='new: second commit',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.tag("v8.0")

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "tag_filter_regexp = r'^v[0-9]+\\.[0.9]$'")

        changelog = w('$tprog')
        self.assertContains(
            changelog, "v8.0",
            msg="At least one of the tags should be displayed in changelog... "
            "content of changelog:\n%s" % changelog)

    def test_reuse_options(self):
        """We must be able to define a small gitchangelog.rc that reuse only
        one variable of all the builtin defaults."""

        self.git.commit(
            message='new: XXX commit',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.commit(
            message='new: XYZ commit',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.commit(
            message='new: normal commit !minor',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "ignore_regexps += [r'XXX', ]")

        changelog = w('$tprog')
        self.assertNotContains(
            changelog, "XXX",
            msg="Should not contain commit with XXX in it... "
            "content of changelog:\n%s" % changelog)
        self.assertContains(
            changelog, "XYZ",
            msg="Should contain commit with XYZ in it... "
            "content of changelog:\n%s" % changelog)
        self.assertNotContains(
            changelog, "!minor",
            msg="Shouldn't contain !minor tagged commit neither... "
            "content of changelog:\n%s" % changelog)

    def test_with_filename_same_as_tag(self):
        gitchangelog.file_put_contents("0.0.1", "")
        self.git.tag("0.0.1")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail even if filename same as tag name.")
        self.assertEqual(
            err, "",
            msg="No error message expected. "
            "Current stderr:\n%s" % err)

    def test_include_merge_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "include_merge = False")
        self.git.checkout(b="develop")
        self.git.commit(message="made on develop branch",
                        allow_empty=True)
        self.git.checkout("master")
        self.git.merge("develop", no_ff=True)

        changelog = w('$tprog')
        self.assertNotContains(
            changelog, "Merge",
            msg="Should not contain commit with 'Merge' in it... "
            "content of changelog:\n%s" % changelog)

    def test_config_file_is_not_a_file(self):

        os.mkdir(".gitchangelog.rc")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(errlvl, 1)
        self.assertContains(err, "is not a file")

    def test_config_file_syntax_error(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "abc: ; test")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(errlvl, 1)
        self.assertContains(err.lower(), "syntax error")

    def test_subject_process_syntax_error(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "subject_process = ucfirst | False")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(errlvl, 1)
        self.assertContains(err.lower(), "syntax error")


class TestOnUnreleased(BaseGitReposTest):

    def setUp(self):
        super(TestOnUnreleased, self).setUp()

        self.git.commit(
            message='new: begin',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.tag("0.0.1")
        self.git.commit(
            message='new: begin',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)

    def test_unreleased_version_label_callable(self):
        """Using callable in unreleased_version_label should work"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "unreleased_version_label = lambda : 'foo'")
        changelog = w('$tprog "HEAD^..HEAD"')
        self.assertNoDiff(
            textwrap.dedent("""\
                foo
                ---

                New
                ~~~
                - Begin. [Bob]


                """),
            changelog)

    def test_unreleased_version_label_string(self):
        """Using string in unreleased_version_label should work"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "unreleased_version_label = 'bar'")
        changelog = w('$tprog "HEAD^..HEAD"')
        self.assertNoDiff(
            textwrap.dedent("""\
                bar
                ---

                New
                ~~~
                - Begin. [Bob]


                """),
            changelog)
