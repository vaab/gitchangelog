# -*- encoding: utf-8 -*-
"""Testing on empty message

see: https://github.com/vaab/gitchangelog/issues/76

"""

from __future__ import unicode_literals

import textwrap

from .common import gitchangelog, BaseGitReposTest, cmd


class EmptyMessageTest(BaseGitReposTest):

    def setUp(self):
        super(EmptyMessageTest, self).setUp()

        self.git.commit(message="",
                        date="2017-02-20 11:00:00",
                        allow_empty=True,
                        allow_empty_message=True)

    def test_empty_message_accepted_commit(self):
        out = self.simple_changelog(ignore_regexps=[])
        self.assertNoDiff(textwrap.dedent("""\
            None
              None:
                *  [The Committer]

            """), out)

    def test_empty_message_not_accepted(self):
        out = self.simple_changelog(ignore_regexps=[r'^$', ])
        self.assertNoDiff("", out)

    def test_empty_message_default_changelog_accepted(self):
        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "ignore_regexps = []")
        out, err, errlvl = cmd('$tprog --debug')
        self.assertEqual(err, "")
        self.assertEqual(errlvl, 0)
        self.assertNoDiff(textwrap.dedent("""\
            Changelog
            =========


            (unreleased)
            ------------
            - No commit message. [The Committer]


            """), out)

    def test_empty_message_default_changelog(self):
        out, err, errlvl = cmd('$tprog --debug')
        self.assertEqual(errlvl, 0)
        self.assertNoDiff(textwrap.dedent("""\
            Changelog
            =========


            """), out)
