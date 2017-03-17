# -*- encoding: utf-8 -*-
"""Testing tagger_date display

https://github.com/vaab/gitchangelog/issues/60

"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest


def simple_renderer_using_commit_internal(data, opts):
    s = ""
    for version in data["versions"]:
        s += "%s (%s)\n" % (version["tag"], version["commit"].tagger_date)
        for section in version["sections"]:
            s += "  %s:\n" % section["label"]
            for commit in section["commits"]:
                s += "    * %(subject)s [%(author)s]\n" % commit
        s += "\n"
    return s


def simple_renderer(data, opts):
    s = ""
    for version in data["versions"]:
        s += "%s (%s)\n" % (version["tag"], version["tagger_date"])
        for section in version["sections"]:
            s += "  %s:\n" % section["label"]
            for commit in section["commits"]:
                s += "    * %(subject)s [%(author)s]\n" % commit
        s += "\n"
    return s


def simple_renderer_auto_date(data, opts):
    s = ""
    for version in data["versions"]:
        s += "%s (%s)\n" % (version["tag"], version["date"])
        for section in version["sections"]:
            s += "  %s:\n" % section["label"]
            for commit in section["commits"]:
                s += "    * %(subject)s [%(author)s]\n" % commit
        s += "\n"
    return s


class TaggerDateTest(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        1.2 (2017-03-17)
          None:
            * b [The Committer]

        """)

    def setUp(self):
        super(TaggerDateTest, self).setUp()

        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag(['-a', "1.2", '--message="tag message"'],
                     env={'GIT_COMMITTER_DATE': "2017-03-17 11:00:00"})

    def test_checking_tagger_date_in_commit_object(self):
        out = self.changelog(
            output_engine=simple_renderer_using_commit_internal)
        self.assertNoDiff(self.REFERENCE, out)

    def test_checking_tagger_date(self):
        out = self.changelog(output_engine=simple_renderer)
        self.assertNoDiff(self.REFERENCE, out)


class TaggerDateNonAnnotatedTest(BaseGitReposTest):

    def setUp(self):
        super(TaggerDateNonAnnotatedTest, self).setUp()

        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag(["1.2"])

    def test_checking_tagger_date_in_non_tag_with_commit_object(self):
        with self.assertRaises(ValueError):
            self.changelog(output_engine=simple_renderer_using_commit_internal)


class TaggerDateAutoDateTest(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        1.3 (2017-02-20)
          None:
            * b [The Committer]

        1.2 (2017-03-17)
          None:
            * b [The Committer]

        """)

    def setUp(self):
        super(TaggerDateAutoDateTest, self).setUp()

        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag(['-a', "1.2", '--message="tag message"'],
                     env={'GIT_COMMITTER_DATE': "2017-03-17 11:00:00"})
        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag(["1.3"])

    def test_checking_tagger_date(self):
        out = self.changelog(output_engine=simple_renderer_auto_date)
        self.assertNoDiff(self.REFERENCE, out)
