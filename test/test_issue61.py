# -*- encoding: utf-8 -*-
"""Implementation of ``revs`` option

Tests issue #62
(https://github.com/vaab/gitchangelog/issues/62)

"""

from __future__ import unicode_literals

import difflib

from common import BaseGitReposTest, w, cmd, file_put_contents


class TestRevsBadFormat(BaseGitReposTest):

    def test_bad_revs_format(self):
        super(TestRevsBadFormat, self).setUp()

        file_put_contents(
            ".gitchangelog.rc",
            "revs = '1.2'"
        )

        out, err, errlvl = cmd('$tprog')
        self.assertContains(
            err, "'list' type is required",
            msg="There should be an error message containing "
            "\"'list' type is required\". "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 1,
            msg="Should fail")
        self.assertEqual(
            out, "",
            msg="No standard output is expected")

    def test_bad_revs_format_callable(self):
        super(TestRevsBadFormat, self).setUp()

        file_put_contents(
            ".gitchangelog.rc",
            "revs = lambda: '1.2'"
        )

        out, err, errlvl = cmd('$tprog')
        self.assertContains(
            err, "'list' type is required",
            msg="There should be an error message containing "
            "\"'list' type is required\". "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 1,
            msg="Should fail")
        self.assertEqual(
            out, "",
            msg="No output is expected since it errored... ")

    def test_bad_rev_in_revs_format(self):
        super(TestRevsBadFormat, self).setUp()

        file_put_contents(
            ".gitchangelog.rc",
            "revs = [[]]"
        )

        out, err, errlvl = cmd('$tprog')
        self.assertContains(
            err, "'str' type is required",
            msg="There should be an error message containing "
            "\"'str' type is required\". "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 1,
            msg="Should fail")
        self.assertEqual(
            out, "",
            msg="No output is expected since it errored... ")


class TestBasicRevs(BaseGitReposTest):

    REFERENCE = """\
None
  None:
    * c [The Committer]

"""

    REFERENCE2 = """\
Changelog
=========


%%version%% (unreleased)
------------------------
- C. [The Committer]


1.2 (2017-02-20)
----------------
- B. [The Committer]
- A. [The Committer]


"""

    def setUp(self):
        super(TestBasicRevs, self).setUp()

        w("""

            git commit -m 'a' --allow-empty --date "2017-02-20 11:00:00"
            git commit -m 'b' --allow-empty --date "2017-02-20 11:00:00"
            git tag 1.2
            git commit -m 'c' --allow-empty --date "2017-02-20 11:00:00"

        """)

    def test_matching_reference(self):
        """Test that only last commit is in the changelog"""

        changelog = self.simple_changelog(revlist=['^1.2'])
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of reference vs current:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))

    def test_command_line_overrights_config(self):
        """Test that all 3 commits are in the changelog"""

        out, err, errlvl = cmd('$tprog show HEAD')

        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertEqual(
            out, self.REFERENCE2,
            msg="Mako output should match our reference output... "
            "diff of changelogs:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE2.split("\n"),
                                             out.split("\n"),
                                             lineterm="")))
