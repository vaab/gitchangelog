# -*- encoding: utf-8 -*-
"""Testing Incremental Functionality and Recipes


"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest, BaseTmpDirTest, cmd, \
     gitchangelog


class FullIncrementalRecipeTest(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        Changelog
        =========


        (unreleased)
        ------------
        - C. [The Committer]


        1.2 (2017-02-20)
        ----------------
        - Previous content

        """)

    def setUp(self):
        super(FullIncrementalRecipeTest, self).setUp()

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

    def test_insert_changelog_recipe(self):
        """Full incremental recipe"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(
                r"""
                OUTPUT_FILE = "CHANGELOG.rst"
                INSERT_POINT = r"\b(?P<rev>[0-9]+\.[0-9]+)\s+\([0-9]+-[0-9]{2}-[0-9]{2}\)\n--+\n"
                revs = [
                        Caret(FileFirstRegexMatch(OUTPUT_FILE, INSERT_POINT)),
                        "HEAD"
                ]

                publish = FileInsertAtFirstRegexMatch(
                    OUTPUT_FILE, INSERT_POINT,
                    idx=lambda m: m.start(1)
                )
                """))
        gitchangelog.file_put_contents(
            "CHANGELOG.rst",
            textwrap.dedent("""\
                Changelog
                =========


                1.2 (2017-02-20)
                ----------------
                - Previous content

                """))

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(gitchangelog.file_get_contents("CHANGELOG.rst"),
                          self.REFERENCE)

    def test_insert_changelog_recipe2(self):
        """Full incremental recipe with subst"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent(
                r"""
                OUTPUT_FILE = "CHANGELOG.rst"
                REV_REGEX=r"[0-9]+\.[0-9]+(\.[0-9]+)?"
                INSERT_POINT_REGEX = r'''(?isxu)
                ^
                (
                  \s*Changelog\s*(\n|\r\n|\r)        ## ``Changelog`` line
                  ==+\s*(\n|\r\n|\r){2}              ## ``=========`` rest underline
                )

                (
                    (
                      (?!
                         (?<=(\n|\r))                ## look back for newline
                         %(rev)s                     ## revision
                         \s+
                         \([0-9]+-[0-9]{2}-[0-9]{2}\)(\n|\r\n|\r)   ## date
                           --+(\n|\r\n|\r)                          ## ``---`` underline
                      )
                      .
                    )*
                )

                (?P<rev>%(rev)s)
                ''' % {'rev': REV_REGEX}

                revs = [
                    Caret(FileFirstRegexMatch(OUTPUT_FILE, INSERT_POINT_REGEX)),
                    "HEAD"
                ]

                publish = FileRegexSubst(
                    OUTPUT_FILE, INSERT_POINT_REGEX, r"\1\o\g<rev>"
                )
                """))
        gitchangelog.file_put_contents(
            "CHANGELOG.rst",
            textwrap.dedent("""\
                Changelog
                =========


                XXX Garbage

                1.2 (2017-02-20)
                ----------------
                - Previous content

                """))

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed")
        self.assertNoDiff(
            self.REFERENCE,
            gitchangelog.file_get_contents("CHANGELOG.rst"))
        ## Re-applying will change nothing
        out, err, errlvl = cmd('$tprog')
        self.assertNoDiff(
            self.REFERENCE,
            gitchangelog.file_get_contents("CHANGELOG.rst"))


class FileInsertAtFirstRegexMatchTest(BaseTmpDirTest):

    def test_insertions(self):
        def make_insertion(string, pattern, insert, **kw):
            FILE = "testing.txt"
            gitchangelog.file_put_contents(FILE, string)
            gitchangelog.FileInsertAtFirstRegexMatch(FILE, pattern, **kw)(
                insert.splitlines(True))
            return gitchangelog.file_get_contents(FILE)

        self.assertEqual(make_insertion("", r"^", "B"), "B")
        self.assertEqual(make_insertion("AC", r"C", "B"), "ABC")
        self.assertEqual(make_insertion("BC", r"B", "A"), "ABC")
        self.assertEqual(make_insertion("AB", r"$", "C", idx=lambda m: m.end() + 1), "ABC")
        self.assertEqual(make_insertion("A\nC", r"C", "B\n"), "A\nB\nC")
        self.assertEqual(make_insertion("B\nC", r"B", "A\n"), "A\nB\nC")
        self.assertEqual(make_insertion("A\nB", r"$", "\nC", idx=lambda m: m.end() + 1), "A\nB\nC")
        self.assertEqual(make_insertion("A\nC\n", r"C", "B\n"), "A\nB\nC\n")
        self.assertEqual(make_insertion("B\nC\n", r"B", "A\n"), "A\nB\nC\n")
        self.assertEqual(make_insertion("A\nB\n", r"$", "C\n", idx=lambda m: m.end() + 1), "A\nB\nC\n")
