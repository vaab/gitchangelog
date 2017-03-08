# -*- encoding: utf-8 -*-
"""
Tests issue #52
(https://github.com/vaab/gitchangelog/issues/52)

"""

from __future__ import unicode_literals

from .common import BaseGitReposTest


class TestNoTagButCommitNoWarn(BaseGitReposTest):

    def setUp(self):
        super(TestNoTagButCommitNoWarn, self).setUp()

        self.git.commit(message="a", allow_empty=True)

    def test_no_tag_no_revlist(self):
        """if no tags are detected it should throw a warning"""

        warnings = []

        def warn(msg):
            warnings.append(msg)

        output = self.simple_changelog(warn=warn)
        self.assertEqual(
            output, 'None\n  None:\n    * a [The Committer]\n\n')
        self.assertTrue(
            len(warnings) == 0,
            msg="Should have outputed no warnings.")

    def test_no_tag_revlist(self):
        """if no tags are detected and revlist is provided, check warning"""

        warnings = []

        def warn(msg):
            warnings.append(msg)

        output = self.simple_changelog(revlist=["HEAD", ], warn=warn)
        self.assertEqual(
            output, 'None\n  None:\n    * a [The Committer]\n\n')
        self.assertTrue(
            len(warnings) == 0,
            msg="Should have outputed no warnings.")


class TestEmptyChangelogWarn(BaseGitReposTest):

    def setUp(self):
        super(TestEmptyChangelogWarn, self).setUp()
        self.git.commit(message='chg: dev: ignore !minor', allow_empty=True)

    def test_no_commit(self):
        """check warning about empty changelog"""

        warnings = []

        def warn(msg):
            if "empty changelog" in msg.lower():
                warnings.append(msg)

        self.simple_changelog(warn=warn, ignore_regexps=['!minor'])
        self.assertTrue(
            len(warnings) != 0,
            msg="Should have outputed at least one warning about "
            "'empty changelog'")

