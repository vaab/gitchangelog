# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os.path
import glob
import textwrap

from .common import BaseGitReposTest, w, cmd, gitchangelog
from gitchangelog.gitchangelog import indent


class GitChangelogTest(BaseGitReposTest):
    """Base for all tests needing to start in a new git small repository"""

    REFERENCE = textwrap.dedent("""\
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


          """)

    INCR_REFERENCE_002_003 = textwrap.dedent("""\
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


        """)

    def setUp(self):
        super(GitChangelogTest, self).setUp()

        self.git.commit(
            message='new: first commit',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.tag("0.0.1")
        self.git.commit(
            message=textwrap.dedent("""
                add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<``

                Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b"""),
            author='Alice <alice@example.com>',
            date='2000-01-02 11:00:00',
            allow_empty=True)
        self.git.tag("0.0.2")
        self.git.commit(
            message='new: add file ``c``',
            author='Charly <charly@example.com>',
            date='2000-01-03 12:00:00',
            allow_empty=True)
        self.git.commit(
            message=textwrap.dedent("""
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
                """),
            author='Bob <bob@example.com>',
            date='2000-01-04 13:00:00',
            allow_empty=True)
        self.git.commit(
            message='chg: modified ``b`` !minor',
            author='Bob <bob@example.com>',
            date='2000-01-05 13:00:00',
            allow_empty=True)
        self.git.tag("0.0.3")
        self.git.commit(
            message=textwrap.dedent("""
                chg: modified ``b`` XXX

                Co-Authored-By: Juliet <juliet@example.com>
                Co-Authored-By: Charly <charly@example.com>
                """),
            author='Alice <alice@example.com>',
            date='2000-01-06 11:00:00',
            allow_empty=True)

    def test_simple_run_no_args_legacy_call(self):
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            out, "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(self.REFERENCE, out)

    def test_simple_run_show_call_deprecated(self):
        out, err, errlvl = cmd('$tprog show')
        self.assertContains(
            err, "deprecated",
            msg="There should be a warning about deprecated calls. "
            "Current stderr:\n%r" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            out, "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(self.REFERENCE, out)

    def test_incremental_call(self):
        out, err, errlvl = cmd('$tprog 0.0.2..0.0.3')
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(self.INCR_REFERENCE_002_003, out)

    def test_incremental_call_multirev(self):
        out, err, errlvl = cmd('$tprog "^0.0.2" 0.0.3 0.0.3')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(self.INCR_REFERENCE_002_003, out)

    def test_incremental_call_one_commit_unreleased(self):
        out, err, errlvl = cmd('$tprog "^HEAD^" HEAD')
        REFERENCE = textwrap.dedent("""\
            (unreleased)
            ------------

            Changes
            ~~~~~~~
            - Modified ``b`` XXX. [Alice, Charly, Juliet]


            """)
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertNoDiff(
            REFERENCE, out)

    def test_incremental_call_one_commit_released(self):
        out, err, errlvl = cmd('$tprog "0.0.3^^^..0.0.3^^"')
        REFERENCE = textwrap.dedent("""\
            0.0.3 (2000-01-05)
            ------------------

            New
            ~~~
            - Add file ``c`` [Charly]


            """)
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(REFERENCE, out)

    def test_incremental_show_call_deprecated(self):
        out, err, errlvl = cmd('$tprog show 0.0.2..0.0.3')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            err, "deprecated",
            msg="There should be a deprecated warning. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.3",
            msg="The tag 0.0.3 should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(self.INCR_REFERENCE_002_003, out)

    def test_provided_config_file(self):
        """Check provided reference with older name for perfect same result."""

        config_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..", "src", "gitchangelog")
        configs = glob.glob(os.path.join(config_dir,
                                         "gitchangelog.rc.reference.v*"))
        self.assertNotEqual(len(configs), 0)
        for config in configs:
            out, err, errlvl = cmd(
                '$tprog', env={'GITCHANGELOG_CONFIG_FILENAME': config})
            self.assertEqual(errlvl, 0)
            self.assertNoDiff(self.REFERENCE, out)

    def test_same_output_with_different_engine(self):
        """Reference implem should match mustache and mako implem"""

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "output_engine = mustache('restructuredtext')")
        changelog = w('$tprog')
        self.assertNoDiff(
            self.REFERENCE, changelog)

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "output_engine = makotemplate('restructuredtext')")
        changelog = w('$tprog')
        self.assertNoDiff(self.REFERENCE, changelog)

    def test_same_output_with_different_engine_incr(self):
        """Reference implem should match mustache and mako implem (incr)"""

        gitchangelog.file_put_contents(".gitchangelog.rc",
                          "output_engine = mustache('restructuredtext')")
        changelog = w('$tprog 0.0.2..0.0.3')
        self.assertNoDiff(self.INCR_REFERENCE_002_003, changelog)

        gitchangelog.file_put_contents(".gitchangelog.rc",
                          "output_engine = makotemplate('restructuredtext')")
        changelog = w('$tprog 0.0.2..0.0.3')
        self.assertNoDiff(self.INCR_REFERENCE_002_003, changelog)

    def test_provided_templates(self):
        """Run all provided templates at least once"""

        for label, directory in [("makotemplate", "mako"),
                                 ("mustache", "mustache")]:
            template_dir = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "..", "templates", directory)
            templates = glob.glob(os.path.join(template_dir, "*.tpl"))
            template_labels = [os.path.basename(f).split(".")[0]
                               for f in templates]
            for tpl in template_labels:
                gitchangelog.file_put_contents(".gitchangelog.rc",
                                  "output_engine = %s(%r)" % (label, tpl))
                out, err, errlvl = cmd('$tprog')
                self.assertEqual(
                    errlvl, 0,
                    msg="Should not fail on %s(%r) " % (label, tpl) +
                    "Current stderr:\n%s" % indent(err))

