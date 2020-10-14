# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import glob
import os.path
import re
import textwrap

from gitchangelog.gitchangelog import indent

from .common import BaseGitReposTest, w, cmd, gitchangelog


class GitChangelogTest(BaseGitReposTest):
    """Base for all tests needing to start in a new git small repository"""

    REFERENCE = textwrap.dedent(
        """\
          Changelog
          =========


          (unreleased)
          ------------

          Changes
          ~~~~~~~
          - Modified ``b`` XXX. [Alice, Charly, Juliet]


          0.0.3 (2000-01-05)
          ------------------

          New
          ~~~
          - Add file ``e``, modified ``b`` [Bob]

            This is a message body.

            With multi-line content:
            - one
            - two
          - Add file ``c`` [Charly]


          0.0.2 (2000-01-02)
          ------------------
          - Add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<`` [Alice]


          """
    )

    MUSTACHE_REFERENCE = textwrap.dedent(
        """\
          Changelog
          =========

          (unreleased)
          ------------

          Changes
          ~~~~~~~
          - Modified ``b`` XXX. [Alice, Charly, Juliet] `[{co_authores_commits}] <{co_authores_commits}>`_


          0.0.3 (2000-01-05)
          ------------------

          New
          ~~~
          - Add file ``e``, modified ``b`` [Bob] `[{bob_commit}] <{bob_commit}>`_

            This is a message body.

            With multi-line content:
            - one
            - two
          - Add file ``c`` [Charly] `[{charly_commit}] <{charly_commit}>`_


          0.0.2 (2000-01-02)
          ------------------
          - Add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<`` [Alice] `[{alice_commit}] <{alice_commit}>`_


          """
    )

    MUSTACHE_INCR_REFERENCE_002_003 = textwrap.dedent(
        """\
        0.0.3 (2000-01-05)
        ------------------

        New
        ~~~
        - Add file ``e``, modified ``b`` [Bob] `[{bob_commit}] <{bob_commit}>`_

          This is a message body.

          With multi-line content:
          - one
          - two
        - Add file ``c`` [Charly] `[{charly_commit}] <{charly_commit}>`_


        """
    )

    INCR_REFERENCE_002_003 = textwrap.dedent(
        """\
        0.0.3 (2000-01-05)
        ------------------

        New
        ~~~
        - Add file ``e``, modified ``b`` [Bob]

          This is a message body.

          With multi-line content:
          - one
          - two
        - Add file ``c`` [Charly]


        """
    )

    def get_commits(self, username):
        return re.findall(
            r"commit\s(.*)\nAuthor: {}".format(username), self.git.log()
        )

    def setUp(self):
        super(GitChangelogTest, self).setUp()

        self.bob_commit_1 = self.git.commit(
            message="new: first commit",
            author="Bob <bob@example.com>",
            date="2000-01-01 10:00:00",
            allow_empty=True,
        )
        self.git.tag("0.0.1")
        self.alice_commit_2 = self.git.commit(
            message=textwrap.dedent(
                """
                add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<``

                Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b"""
            ),
            author="Alice <alice@example.com>",
            date="2000-01-02 11:00:00",
            allow_empty=True,
        )
        self.git.tag("0.0.2")
        self.charly_commit_3 = self.git.commit(
            message="new: add file ``c``",
            author="Charly <charly@example.com>",
            date="2000-01-03 12:00:00",
            allow_empty=True,
        )
        self.bob_commit_4 = self.git.commit(
            message=textwrap.dedent(
                """
                new: add file ``e``, modified ``b``

                This is a message body.

                With multi-line content:
                - one
                - two

                Bug: #42
                Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b
                Signed-off-by: A. U. Thor <author@example.com>
                CC: R. E. Viewer <reviewer@example.com>
                Subject: This is a fake subject spanning to several lines
                  as you can see
                """
            ),
            author="Bob <bob@example.com>",
            date="2000-01-04 13:00:00",
            allow_empty=True,
        )
        self.bob_commit_5 = self.git.commit(
            message="chg: modified ``b`` !minor",
            author="Bob <bob@example.com>",
            date="2000-01-05 13:00:00",
            allow_empty=True,
        )
        self.git.tag("0.0.3")
        self.alice_commit_6 = self.git.commit(
            message=textwrap.dedent(
                """
                chg: modified ``b`` XXX

                Co-Authored-By: Juliet <juliet@example.com>
                Co-Authored-By: Charly <charly@example.com>
                """
            ),
            author="Alice <alice@example.com>",
            date="2000-01-06 11:00:00",
            allow_empty=True,
        )

    def test_simple_run_no_args_legacy_call(self):
        out, err, errlvl = cmd("$tprog")
        self.assertEqual(
            err,
            "",
            msg="There should be no standard error outputed. "
                "Current stderr:\n%r" % err,
        )
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertContains(
            out,
            "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
                "Current stdout:\n%s" % out,
        )
        self.assertNoDiff(self.REFERENCE, out)

    def test_simple_run_show_call_deprecated(self):
        out, err, errlvl = cmd("$tprog show")
        self.assertContains(
            err,
            "deprecated",
            msg="There should be a warning about deprecated calls. "
                "Current stderr:\n%r" % err,
        )
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertContains(
            out,
            "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
                "Current stdout:\n%s" % out,
        )
        self.assertNoDiff(self.REFERENCE, out)

    def test_incremental_call(self):
        out, err, errlvl = cmd("$tprog 0.0.2..0.0.3")
        self.assertEqual(
            err,
            "",
            msg="There should be no standard error outputed. "
                "Current stderr:\n%r" % err,
        )
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertContains(
            out,
            "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
                "Current stdout:\n%s" % out,
        )
        self.assertNoDiff(self.INCR_REFERENCE_002_003, out)

    def test_incremental_call_multirev(self):
        out, err, errlvl = cmd('$tprog "^0.0.2" 0.0.3 0.0.3')
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertEqual(
            err,
            "",
            msg="There should be no standard error outputed. "
                "Current stderr:\n%r" % err,
        )
        self.assertContains(
            out,
            "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
                "Current stdout:\n%s" % out,
        )
        self.assertNoDiff(self.INCR_REFERENCE_002_003, out)

    def test_incremental_call_one_commit_unreleased(self):
        out, err, errlvl = cmd('$tprog "^HEAD^" HEAD')
        REFERENCE = textwrap.dedent(
            """\
            (unreleased)
            ------------

            Changes
            ~~~~~~~
            - Modified ``b`` XXX. [Alice, Charly, Juliet]


            """
        )
        self.assertEqual(
            err,
            "",
            msg="There should be no standard error outputed. "
                "Current stderr:\n%s" % err,
        )
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertNoDiff(REFERENCE, out)

    def test_incremental_call_one_commit_released(self):
        out, err, errlvl = cmd('$tprog "0.0.3^^^..0.0.3^^"')
        REFERENCE = textwrap.dedent(
            """\
            0.0.3 (2000-01-05)
            ------------------

            New
            ~~~
            - Add file ``c`` [Charly]


            """
        )
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertEqual(
            err,
            "",
            msg="There should be no standard error outputed. "
                "Current stderr:\n%r" % err,
        )
        self.assertContains(
            out,
            "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
                "Current stdout:\n%s" % out,
        )
        self.assertNoDiff(REFERENCE, out)

    def test_incremental_show_call_deprecated(self):
        out, err, errlvl = cmd("$tprog show 0.0.2..0.0.3")
        self.assertEqual(
            errlvl,
            0,
            msg="Should not fail on simple repo and without config file",
        )
        self.assertContains(
            err,
            "deprecated",
            msg="There should be a deprecated warning. "
                "Current stderr:\n%r" % err,
        )
        self.assertContains(
            out,
            "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
                "Current stdout:\n%s" % out,
        )
        self.assertNoDiff(self.INCR_REFERENCE_002_003, out)

    def test_provided_config_file(self):
        """Check provided reference with older name for perfect same result."""

        config_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "src",
            "gitchangelog",
        )
        configs = glob.glob(
            os.path.join(config_dir, "gitchangelog.rc.reference.v*")
        )
        self.assertNotEqual(len(configs), 0)
        for config in configs:
            out, err, errlvl = cmd(
                "$tprog", env={"GITCHANGELOG_CONFIG_FILENAME": config}
            )
            self.assertEqual(errlvl, 0)
            self.assertNoDiff(self.REFERENCE, out)

    def test_same_output_with_different_engine(self):
        """Reference implem should match mustache and mako implem"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc", "output_engine = mustache('restructuredtext')"
        )
        changelog = w("$tprog")

        # get first commit from Alice
        alice_commits = self.get_commits("Alice")
        alice_commit = alice_commits[1]
        # get second commit from Bob
        bob_commit = self.get_commits("Bob")[1]
        # get first commit
        charly_commit = self.get_commits("Charly")[0]
        # get first commit from Alice where has co-authores
        co_authores_commits = alice_commits[0]

        self.assertNoDiff(
            self.MUSTACHE_REFERENCE.format(
                **{
                    "alice_commit": alice_commit,
                    "charly_commit": charly_commit,
                    "bob_commit": bob_commit,
                    "co_authores_commits": co_authores_commits
                }
            ),
            changelog,
        )

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "output_engine = makotemplate('restructuredtext')",
        )
        changelog = w("$tprog")
        self.assertNoDiff(self.REFERENCE, changelog)

    def test_same_output_with_different_engine_incr(self):
        """Reference implem should match mustache and mako implem (incr)"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc", "output_engine = mustache('restructuredtext')"
        )
        changelog = w("$tprog 0.0.2..0.0.3")

        # get second commit from Bob
        bob_commit = self.get_commits("Bob")[1]
        # get first commit
        charly_commit = self.get_commits("Charly")[0]
        self.assertNoDiff(self.MUSTACHE_INCR_REFERENCE_002_003.format(**{
            "charly_commit": charly_commit,
            "bob_commit": bob_commit,
        }), changelog)

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "output_engine = makotemplate('restructuredtext')",
        )
        changelog = w("$tprog 0.0.2..0.0.3")
        self.assertNoDiff(self.INCR_REFERENCE_002_003, changelog)

    def test_provided_templates(self):
        """Run all provided templates at least once"""

        for label, directory in [
            ("makotemplate", "mako"),
            ("mustache", "mustache"),
        ]:
            template_dir = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "..",
                "templates",
                directory,
            )
            templates = glob.glob(os.path.join(template_dir, "*.tpl"))
            template_labels = [
                os.path.basename(f).split(".")[0] for f in templates
            ]
            for tpl in template_labels:
                gitchangelog.file_put_contents(
                    ".gitchangelog.rc", "output_engine = %s(%r)" % (label, tpl)
                )
                out, err, errlvl = cmd("$tprog")
                self.assertEqual(
                    errlvl,
                    0,
                    msg="Should not fail on %s(%r) " % (label, tpl)
                        + "Current stderr:\n%s" % indent(err),
                )
