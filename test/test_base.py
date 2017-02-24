# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os.path
import glob
import textwrap

from .common import BaseGitReposTest, w, cmd, file_put_contents
from gitchangelog.gitchangelog import indent


class GitChangelogTest(BaseGitReposTest):
    """Base for all tests needing to start in a new git small repository"""

    REFERENCE = textwrap.dedent("""\
          Changelog
          =========


          %%version%% (unreleased)
          ------------------------

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
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(
            self.REFERENCE, out,
            msg="Should match our reference output... ")

    def test_simple_run_show_call_deprecated(self):
        out, err, errlvl = cmd('$tprog show')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertContains(
            err, "deprecated",
            msg="There should be a warning about deprecated calls. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.2",
            msg="At least one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(
            self.REFERENCE, out,
            msg="Should match our reference output... ")

    def test_simple_with_changelog_python_exception(self):
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
            msg="The exception message should NOT contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_simple_show_with_changelog_python_exception_deprecated(self):
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog show')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
            msg="The exception message should NOT contain traceback information... "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)

    def test_with_changelog_python_exc_in_cli_debug_mode(self):
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog --debug show')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog HEAD --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog show --debug')
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog', env={"DEBUG_GITCHANGELOG": "1"})
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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
        file_put_contents(
            ".gitchangelog.rc",
            textwrap.dedent("""
                def raise_exc(data, opts):
                    raise Exception('Test Exception XYZ')

                output_engine = raise_exc
                """))

        out, err, errlvl = cmd('$tprog show', env={"DEBUG_GITCHANGELOG": "1"})
        self.assertContains(
            err, "XYZ",
            msg="The exception message should be displayed and thus contain XYZ... "
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

    def test_incremental_call(self):
        out, err, errlvl = cmd('$tprog 0.0.2..0.0.3')
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
        self.assertNoDiff(
            self.INCR_REFERENCE_002_003, out,
            msg="Should match our reference output... ")

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
        self.assertNoDiff(
            self.INCR_REFERENCE_002_003, out,
            msg="Should match our reference output... ")

    def test_incremental_call_one_commit_unreleased(self):
        out, err, errlvl = cmd('$tprog "^HEAD^" HEAD')
        REFERENCE = textwrap.dedent("""\
            %%version%% (unreleased)
            ------------------------

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
        self.assertContains(
            out, "%%version%%",
            msg="The tag %%version%% should be displayed in stdout... "
            "Current stdout:\n%s" % out)
        self.assertNoDiff(
            REFERENCE, out,
            msg="Should match our reference output... ")

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
        self.assertNoDiff(
            REFERENCE, out,
            msg="Should match our reference output... ")

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
        self.assertNoDiff(
            self.INCR_REFERENCE_002_003, out,
            msg="Should match our reference output... ")

    def test_overriding_options(self):
        """We must be able to define a small gitchangelog.rc that override only
        one variable of all the builtin defaults."""

        file_put_contents(
            ".gitchangelog.rc",
            "tag_filter_regexp = r'^v[0-9]+\\.[0.9]$'")

        self.git.tag("v7.0", "HEAD^")
        self.git.tag("v8.0", "HEAD")

        changelog = w('$tprog')
        self.assertContains(
            changelog, "v8.0",
            msg="At least one of the tags should be displayed in changelog... "
            "content of changelog:\n%s" % changelog)

    def test_reuse_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        file_put_contents(
            ".gitchangelog.rc",
            "ignore_regexps += [r'XXX', ]")
        changelog = w('$tprog')
        self.assertNotContains(
            changelog, "XXX",
            msg="Should not contain commit with XXX in it... "
            "content of changelog:\n%s" % changelog)
        self.assertContains(
            changelog, "dd file ``e``",
            msg="Should contain at least a message of other commits... "
            "content of changelog:\n%s" % changelog)
        self.assertNotContains(
            changelog, "!minor",
            msg="Shouldn't contain !minor tagged commit neither... "
            "content of changelog:\n%s" % changelog)

    def test_provided_config_file(self):
        """Check provided reference with older name for perfect same result."""

        config_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..")
        configs = glob.glob(os.path.join(config_dir,
                                         "gitchangelog.rc.reference.v*"))
        for config in configs:
            out, err, errlvl = cmd(
                'GITCHANGELOG_CONFIG_FILENAME="%s" $tprog' % config)
            self.assertEqual(
                errlvl, 0,
                msg="Should not fail with config %r " % (config, ) +
                "Current stderr:\n%s" % indent(err))
            self.assertNoDiff(
                self.REFERENCE, out,
                msg="config %r output should match our reference output... ")

    def test_with_filename_same_as_tag(self):
        file_put_contents("0.0.1", "")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail even if filename same as tag name.")
        self.assertEqual(
            err, "",
            msg="No error message expected. "
            "Current stderr:\n%s" % err)
        self.assertNoDiff(
            self.REFERENCE, out,
            msg="Should match our reference output... ")

    def test_include_merge_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        file_put_contents(
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

    def test_same_output_with_different_engine(self):
        """Reference implementation should match mustache and mako implem"""

        file_put_contents(
            ".gitchangelog.rc",
            "output_engine = mustache('restructuredtext')")
        changelog = w('$tprog')
        self.assertNoDiff(
            self.REFERENCE, changelog,
            msg="Mustache output should match our reference output... ")

        file_put_contents(
            ".gitchangelog.rc",
            "output_engine = makotemplate('restructuredtext')")
        changelog = w('$tprog')
        self.assertNoDiff(
            self.REFERENCE, changelog,
            msg="Mako output should match our reference output... ")

    def test_same_output_with_different_engine_incr(self):
        """Reference implementation should match mustache and mako implem"""

        file_put_contents(".gitchangelog.rc",
                          "output_engine = mustache('restructuredtext')")
        changelog = w('$tprog 0.0.2..0.0.3')
        self.assertNoDiff(
            self.INCR_REFERENCE_002_003, changelog,
            msg="Mustache output should match our reference output... ")

        file_put_contents(".gitchangelog.rc",
                          "output_engine = makotemplate('restructuredtext')")
        changelog = w('$tprog 0.0.2..0.0.3')
        self.assertNoDiff(
            self.INCR_REFERENCE_002_003, changelog,
            msg="Mako output should match our reference output... ")

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
                file_put_contents(".gitchangelog.rc",
                                  "output_engine = %s(%r)" % (label, tpl))
                out, err, errlvl = cmd('$tprog')
                self.assertEqual(
                    errlvl, 0,
                    msg="Should not fail on %s(%r) " % (label, tpl) +
                    "Current stderr:\n%s" % indent(err))

    def test_unexistent_template_name(self):
        """Unexisting template should get a proper error message"""

        file_put_contents(".gitchangelog.rc",
                          "output_engine = mustache('doesnotexist')")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 1,
            msg="Should fail as template does not exist")
        self.assertEqual(
            out, "",
            msg="No stdout was expected since there was an error. "
            "Current stdout:\n%r" % out)
        self.assertContains(
            err, "doesnotexist",
            msg="There should be an error message mentioning 'doesnotexist'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "restructuredtext",
            msg="The error message should mention 'available'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "mustache",
            msg="The error message should mention 'mustache'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err, "restructuredtext",
            msg="The error message should mention 'restructuredtext'. "
            "Current stderr:\n%s" % err)

    def test_file_template_name(self):
        """Existing files should be accepted as valid templates"""

        file_put_contents("mytemplate.tpl",
                          "check: {{{title}}}")
        file_put_contents(".gitchangelog.rc",
                          "output_engine = mustache('mytemplate.tpl')")

        reference = """check: Changelog"""

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be no error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed to find template")
        self.assertNoDiff(
            reference, out,
            msg="Mako output should match our reference output... ")

    def test_template_as_access_to_full_commit(self):
        """Existing files should be accepted as valid templates"""

        file_put_contents(
            "mytemplate.tpl",
            textwrap.dedent("""
                % for version in data["versions"]:
                ${version["tag"]}
                % for section in version["sections"]:
                  ${section["label"]}:
                % for commit in section["commits"]:
                    - ${commit["commit"].subject}
                % endfor
                % endfor
                % endfor
                """))
        file_put_contents(".gitchangelog.rc",
                          "output_engine = makotemplate('mytemplate.tpl')")

        reference = textwrap.dedent("""
            None
              Changes:
                - chg: modified ``b`` XXX
            0.0.3
              New:
                - new: add file ``e``, modified ``b``
                - new: add file ``c``
            0.0.2
              Other:
                - add ``b`` with non-ascii chars \xe9\xe8\xe0\xe2\xa7\xb5 and HTML chars ``&<``
            """)

        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed to find template")
        self.assertNoDiff(
            reference, out,
            msg="Mako output should match our reference output... ")
