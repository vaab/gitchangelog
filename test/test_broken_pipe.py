# -*- encoding: utf-8 -*-
"""Testing that we do not output confusing python gibberish message
upon SIGPIPE.


Unfortunately this tests is not correctly testable with coverage due
to a bug of coverage hitting python 2.7 (windows and linux).

Indeed, the function ``isolate_module`` is used to make local
copies of modules inside coverage and prevent nasty problems
when some central modules gets mocked by monkeypatching.

But on python 2.7, the copy of ``sys.__stdout__`` and ``sys.stdout``
will prevent the normal failing behavior upon SIGPIPE.

    def isolate_module(mod):
        if mod not in ISOLATED_MODULES:
            new_mod = types.ModuleType(mod.__name__)
            ISOLATED_MODULES[mod] = new_mod
            attributes = dir(mod)
            if mod.__name__ == "sys":
                attributes = set(attributes) - set(["__stdout__", "__stdin__",
                                                   "stdout", "stdin"])
            for name in attributes:
                value = getattr(mod, name)
                if isinstance(value, types.ModuleType):
                    value = isolate_module(value)
                setattr(new_mod, name, value)
        return ISOLATED_MODULES[mod]


"""


from __future__ import unicode_literals

from .common import BaseGitReposTest, cmd, WIN32


class BrokenPipeTest(BaseGitReposTest):

    def setUp(self):
        super(BrokenPipeTest, self).setUp()

        self.git.commit(
            message='foo',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)

    def test_break_pipe(self):
        out, err, errlvl = cmd(
            '$tprog | %s' % ("REM" if WIN32 else ":"))
        self.assertEqual(errlvl, 0)
        self.assertNoDiff("", err)
        self.assertNoDiff("", out)
