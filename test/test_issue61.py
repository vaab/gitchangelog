# -*- encoding: utf-8 -*-
"""Implementation of ``revs`` option

Tests issue #62
(https://github.com/vaab/gitchangelog/issues/62)

"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest, cmd, gitchangelog


class TestRevsBadFormat(BaseGitReposTest):

    def test_bad_revs_format(self):
        super(TestRevsBadFormat, self).setUp()

        gitchangelog.file_put_contents(
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

        gitchangelog.file_put_contents(
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

        gitchangelog.file_put_contents(
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

    REFERENCE = textwrap.dedent("""\
        None
          None:
            * c [The Committer]

        """)

    REFERENCE2 = textwrap.dedent("""\
        Changelog
        =========


        (unreleased)
        ------------
        - C. [The Committer]


        1.2 (2017-02-20)
        ----------------
        - B. [The Committer]
        - A. [The Committer]


        """)

    def setUp(self):
        super(TestBasicRevs, self).setUp()

        self.git.commit(message="a",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag("1.2")
        self.git.commit(message="c",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)

    def test_matching_reference(self):
        """Test that only last commit is in the changelog"""

        changelog = self.simple_changelog(revlist=['^1.2', 'HEAD'])
        self.assertNoDiff(
            self.REFERENCE, changelog)

    def test_cli_over_file_precedence(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(r"""
                revs = [
                    Caret(
                        FileFirstRegexMatch(
                        "CHANGELOG.rst",
                        r"(?P<rev>[0-9]+\.[0-9]+)\s+\([0-9]+-[0-9]{2}-[0-9]{2}\)\n--+\n")),
                    "HEAD"
                ]
                """))

        out, err, errlvl = cmd('$tprog HEAD')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(self.REFERENCE2, out)

    def test_callable_rev_file_first_regex_match_no_file(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(r"""
                revs = [
                    Caret(
                        FileFirstRegexMatch(
                        "CHANGELOG.rst",
                        r"(?P<rev>[0-9]+\.[0-9]+)\s+\([0-9]+-[0-9]{2}-[0-9]{2}\)\n--+\n\n")),
                    "HEAD"
                ]
                """))

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(errlvl, 1)
        self.assertContains(err, "CHANGELOG.rst")
        self.assertEqual("", out)

    def test_callable_rev_file_first_regex_match_fails(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(r"""
                revs = [
                    Caret(
                        FileFirstRegexMatch(
                            "CHANGELOG.rst",
                            r"XXX(?P<rev>[0-9]+\.[0-9]+)\s+\([0-9]+-[0-9]{2}-[0-9]{2}\)\n--+\n")),
                    "HEAD"
                ]
                """))
        gitchangelog.file_put_contents(
            "CHANGELOG.rst",
            textwrap.dedent("""\
                Changelog
                =========


                1.2 (2017-02-20)
                ----------------
                - B. [The Committer]
                - A. [The Committer]

                """))

        out, err, errlvl = cmd('$tprog')
        self.assertContains(err, "CHANGELOG.rst")
        self.assertEqual(errlvl, 1)
        self.assertContains(err, "match")
        self.assertEqual("", out)

    def test_callable_rev_file_first_regex_match_working(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(r"""
                revs = [
                    Caret(
                        FileFirstRegexMatch(
                            "CHANGELOG.rst",
                            r"(?P<rev>[0-9]+\.[0-9]+)\s+\([0-9]+-[0-9]{2}-[0-9]{2}\)\n--+\n")),
                    "HEAD"
                ]
                """))
        gitchangelog.file_put_contents(
            "CHANGELOG.rst",
            textwrap.dedent("""\
                Changelog
                =========


                1.2 (2017-02-20)
                ----------------
                - B. [The Committer]
                - A. [The Committer]

                """))

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(textwrap.dedent("""\
            (unreleased)
            ------------
            - C. [The Committer]


            """), out)

    def test_callable_rev_file_first_regex_reg_support(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(r"""
                import re
                REGEX = re.compile(r"(?P<rev>[0-9]+\.[0-9]+)\s+\([0-9]+-[0-9]{2}-[0-9]{2}\)\n--+\n")
                revs = [
                    Caret(
                        FileFirstRegexMatch(
                            "CHANGELOG.rst",
                            REGEX)),
                    "HEAD"
                ]
                """))
        gitchangelog.file_put_contents(
            "CHANGELOG.rst",
            textwrap.dedent("""\
                Changelog
                =========


                1.2 (2017-02-20)
                ----------------
                - B. [The Committer]
                - A. [The Committer]

                """))

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(textwrap.dedent("""\
            (unreleased)
            ------------
            - C. [The Committer]


            """), out)

    def test_callable_rev_file_first_regex_match_missing_pattern(self):

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(r"""
                revs = [
                    Caret(
                        FileFirstRegexMatch(
                            "CHANGELOG.rst",
                            r"[0-9]+\.[0-9]+")),
                    "HEAD"
                ]
                """))
        gitchangelog.file_put_contents(
            "CHANGELOG.rst",
            textwrap.dedent("""\
                Changelog
                =========


                1.2 (2017-02-20)
                ----------------
                - B. [The Committer]
                - A. [The Committer]

                """))

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(textwrap.dedent("""\
            (unreleased)
            ------------
            - C. [The Committer]


            """), out)

    def test_command_line_overrights_config(self):
        """Test that all 3 commits are in the changelog"""

        out, err, errlvl = cmd('$tprog HEAD')

        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(
            self.REFERENCE2, out)
