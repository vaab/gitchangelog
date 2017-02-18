#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import locale
import re
import os
import os.path
import sys
import glob
import textwrap
import datetime
import collections
import traceback
import contextlib
import itertools

from subprocess import Popen, PIPE

try:
    import pystache
except ImportError:  ## pragma: no cover
    pystache = None

try:
    import mako
except ImportError:  ## pragma: no cover
    mako = None


__version__ = "%%version%%"  ## replaced by autogen.sh

DEBUG = None

PY_VERSION = float("%d.%d" % sys.version_info[0:2])
PY3 = PY_VERSION >= 3

WIN32 = sys.platform == 'win32'
if WIN32:
    PLT_CFG = {
        'close_fds': False,
    }
else:
    PLT_CFG = {
        'close_fds': True,
    }


usage_msg = """
  %(exname)s {-h|--help}
  %(exname)s {-v|--version}
  %(exname)s init               ## obsolete
  %(exname)s show [REVLIST]"""

description_msg = """\
Run this command in a git repository to output a formatted changelog
"""

epilog_msg = """\
%(exname)s uses a config file to filter meaningful commit or do some
formatting in commit messages thanks to a config file.

Config file location will be resolved in this order:
  - in shell environment variable GITCHANGELOG_CONFIG_FILENAME
  - in git configuration: ``git config gitchangelog.rc-path``
  - as '.%(exname)s.rc' in the root of the current git repository

"""

def stderr(msg):
    print(msg, file=sys.stderr)


def err(msg):
    stderr("Error: " + msg)


def warn(msg):
    stderr("Warning: " + msg)


class ShellError(Exception):

    def __init__(self, msg, errlvl=None, command=None, out=None, err=None):
        self.errlvl = errlvl
        self.command = command
        self.out = out
        self.err = err
        super(ShellError, self).__init__(msg)


def die(msg=None, errlvl=1):
    if msg:
        stderr(msg)
    sys.exit(errlvl)


@contextlib.contextmanager
def set_cwd(dir):
    curdir = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(curdir)


def format_last_exception(prefix="  | "):
    """Format the last exception for display it in tests.

    This allows to raise custom exception, without loosing the context of what
    caused the problem in the first place:

    >>> def f():
    ...     raise Exception("Something terrible happened")
    >>> try:  ## doctest: +ELLIPSIS
    ...     f()
    ... except Exception:
    ...     formated_exception = format_last_exception()
    ...     raise ValueError('Oups, an error occured:\\n%s' % formated_exception)
    Traceback (most recent call last):
    ...
    ValueError: Oups, an error occured:
      | Traceback (most recent call last):
    ...
      | Exception: Something terrible happened

    """

    return '\n'.join(
        str(prefix + line)
        for line in traceback.format_exc().strip().split('\n'))



##
## config file functions
##

_config_env = {}


def available_in_config(f):
    _config_env[f.__name__] = f
    return f


def load_config_file(filename, default_filename=None,
                     fail_if_not_present=True):
    """Loads data from a config file."""

    config = _config_env.copy()
    for fname in [default_filename, filename]:
        if fname and os.path.exists(fname):
            if not os.path.isfile(fname):
                die("config file path '%s' exists but is not a file !"
                    % (fname, ))
            try:
                with open(fname) as f:
                    code = compile(f.read(), fname, 'exec')
                    exec(code, config)
            except SyntaxError as e:
                die('Syntax error in config file: %s\n'
                    'Line %i offset %i\n'
                    % (fname, e.lineno, e.offset))
        else:
            if fail_if_not_present:
                die('%s config file is not found and is required.' % (fname, ))

    return config

##
## Text functions
##

@available_in_config
class TextProc(object):

    def __init__(self, fun):
        self.fun = fun
        if hasattr(fun, "__name__"):
            self.__name__ = fun.__name__

    def __call__(self, text):
        return self.fun(text)

    def __or__(self, value):
        if isinstance(value, TextProc):
            return TextProc(lambda text: value.fun(self.fun(text)))
        raise SyntaxError


@TextProc
def ucfirst(msg):
    return msg[0].upper() + msg[1:]


@TextProc
def final_dot(msg):
    if len(msg) == 0:
        return "No commit message."
    if msg[-1].isalnum():
        return msg + "."
    return msg


def indent(text, chars="  ", first=None):
    """Return text string indented with the given chars

    >>> string = 'This is first line.\\nThis is second line\\n'

    >>> print(indent(string, chars="| "))  # doctest: +NORMALIZE_WHITESPACE
    | This is first line.
    | This is second line
    |

    >>> print(indent(string, first="- "))  # doctest: +NORMALIZE_WHITESPACE
    - This is first line.
      This is second line


    >>> string = 'This is first line.\\n\\nThis is second line'
    >>> print(indent(string, first="- "))  # doctest: +NORMALIZE_WHITESPACE
    - This is first line.
    <BLANKLINE>
      This is second line

    """
    if first:
        first_line = text.split("\n")[0]
        rest = '\n'.join(text.split("\n")[1:])
        return '\n'.join([(first + first_line).rstrip(),
                          indent(rest, chars=chars)])
    return '\n'.join([(chars + line).rstrip()
                      for line in text.split('\n')])


def paragraph_wrap(text, regexp="\n\n"):
    r"""Wrap text by making sure that paragraph are separated correctly

        >>> string = 'This is first paragraph which is quite long don\'t you \
        ... think ? Well, I think so.\n\nThis is second paragraph\n'

        >>> print(paragraph_wrap(string)) # doctest: +NORMALIZE_WHITESPACE
        This is first paragraph which is quite long don't you think ? Well, I
        think so.
        This is second paragraph

    Notice that that each paragraph has been wrapped separately.

    """
    regexp = re.compile(regexp, re.MULTILINE)
    return "\n".join("\n".join(textwrap.wrap(paragraph.strip()))
                     for paragraph in regexp.split(text)).strip()


def curryfy(f):
    return lambda *a, **kw: TextProc(lambda txt: f(txt, *a, **kw))

## these are curryfied version of their lower case definition

Indent = curryfy(indent)
Wrap = curryfy(paragraph_wrap)
ReSub = lambda p, r, **k: TextProc(lambda txt: re.sub(p, r, txt, **k))
noop = TextProc(lambda txt: txt)
strip = TextProc(lambda txt: txt.strip())

for label in ("Indent", "Wrap", "ReSub", "noop", "final_dot",
              "ucfirst", "strip"):
    _config_env[label] = locals()[label]

##
## System functions
##

## Note that locale.getpreferredencoding() does NOT follow
## PYTHONIOENCODING by default. But ``sys.stdout.encoding``
## does. In PY2, however, if _preferred_encoding is not
## set to utf-8, it leads to encoding errors.
_preferred_encoding = os.environ.get("PYTHONIOENCODING") or \
                      locale.getpreferredencoding()
DEFAULT_GIT_LOG_ENCODING = 'utf-8'


class Phile(object):
    """File like API to read fields separated by any delimiters

    It'll take care of file decoding to unicode.

    This is an adaptor on a file object.

        >>> if PY3:
        ...     from io import BytesIO
        ...     def File(s):
        ...         _obj = BytesIO()
        ...         _obj.write(s.encode(_preferred_encoding))
        ...         _obj.seek(0)
        ...         return _obj
        ... else:
        ...     from cStringIO import StringIO as File

        >>> f = Phile(File("a-b-c-d"))

    Read provides an iterator:

        >>> def show(l):
        ...     print(", ".join(l))
        >>> show(f.read(delimiter="-"))
        a, b, c, d

    You can change the buffersize loaded into memory before outputing
    your changes. It should not change the iterator output:

        >>> f = Phile(File("é-à-ü-d"), buffersize=3)
        >>> len(list(f.read(delimiter="-")))
        4

        >>> f = Phile(File("foo-bang-yummy"), buffersize=3)
        >>> show(f.read(delimiter="-"))
        foo, bang, yummy

        >>> f = Phile(File("foo-bang-yummy"), buffersize=1)
        >>> show(f.read(delimiter="-"))
        foo, bang, yummy

    """

    def __init__(self, file, buffersize=4096, encoding=_preferred_encoding):
        self._file = file
        self._buffersize = buffersize
        self._encoding = encoding

    def read(self, delimiter="\n"):
        buf = ""
        if PY3:
            delimiter = delimiter.encode(_preferred_encoding)
            buf = buf.encode(_preferred_encoding)
        while True:
            chunk = self._file.read(self._buffersize)
            if not chunk:
                yield buf.decode(self._encoding)
                raise StopIteration
            records = chunk.split(delimiter)
            records[0] = buf + records[0]
            for record in records[:-1]:
                yield record.decode(self._encoding)
            buf = records[-1]

    def write(self, buf):
        if PY3:
            buf = buf.encode(self._encoding)
        return self._file.write(buf)

    def close(self):
        return self._file.close()


class Proc(Popen):

    def __init__(self, command, env=None, encoding=_preferred_encoding):
        super(Proc, self).__init__(
            command, shell=True,
            stdin=PIPE, stdout=PIPE, stderr=PIPE,
            close_fds=PLT_CFG['close_fds'], env=env,
            universal_newlines=False)

        self.stdin = Phile(self.stdin, encoding=encoding)
        self.stdout = Phile(self.stdout, encoding=encoding)
        self.stderr = Phile(self.stderr, encoding=encoding)


def cmd(command, env=None):
    p = Popen(command, shell=True,
              stdin=PIPE, stdout=PIPE, stderr=PIPE,
              close_fds=PLT_CFG['close_fds'], env=env,
              universal_newlines=False)
    stdout, stderr = p.communicate()
    return (stdout.decode(_preferred_encoding),
            stderr.decode(_preferred_encoding),
            p.returncode)


def wrap(command, ignore_errlvls=[0], env=None):
    """Wraps a shell command and casts an exception on unexpected errlvl

    >>> wrap('/tmp/lsdjflkjf') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ShellError: Wrapped command '/tmp/lsdjflkjf' exited with errorlevel 127.
      stderr:
      | /bin/sh: .../tmp/lsdjflkjf: not found

    >>> print(wrap('echo hello'),  end='')
    hello

    """

    out, err, errlvl = cmd(command, env=env)

    if errlvl not in ignore_errlvls:

        formatted = []
        if out:
            if out.endswith('\n'):
                out = out[:-1]
            formatted.append("stdout:\n%s" % indent(out, "| "))
        if err:
            if err.endswith('\n'):
                err = err[:-1]
            formatted.append("stderr:\n%s" % indent(err, "| "))
        formatted = '\n'.join(formatted)

        raise ShellError("Wrapped command %r exited with errorlevel %d.\n%s"
                         % (command, errlvl, indent(formatted, chars="  ")),
                         errlvl=errlvl, command=command, out=out, err=err)
    return out


def swrap(command, **kwargs):
    """Same as ``wrap(...)`` but strips the output."""

    return wrap(command, **kwargs).strip()


##
## git information access
##

class SubGitObjectMixin(object):

    def __init__(self, repos):
        self._repos = repos

    def swrap(self, *args, **kwargs):
        """Simple delegation to ``repos`` original method."""
        return self._repos.swrap(*args, **kwargs)


GIT_FORMAT_KEYS = {
    'sha1': "%H",
    'sha1_short': "%h",
    'subject': "%s",
    'author_name': "%an",
    'author_email': "%ae",
    'author_date': "%ad",
    'author_date_timestamp': "%at",
    'committer_name': "%cn",
    'committer_date_timestamp': "%ct",
    'raw_body': "%B",
    'body': "%b",
}

GIT_FULL_FORMAT_STRING = "%x00".join(GIT_FORMAT_KEYS.values())

REGEX_RFC822_KEY_VALUE = r'(^|\n)(?P<key>[A-Z]\w+(-\w+)*): (?P<value>[^\n]*(\n\s+[^\n]*)*)'
REGEX_RFC822_POSTFIX = r'(%s)+$' % REGEX_RFC822_KEY_VALUE


class GitCommit(SubGitObjectMixin):
    r"""Represent a Git Commit and expose through its attribute many information

    Let's create a fake GitRepos:

        >>> from minimock import Mock
        >>> repos = Mock("gitRepos")

    Initialization:

        >>> def mock_swrap(str):
        ...     global BODY, SUBJECT
        ...     print("Called gitRepos.swrap(%r)" % str)
        ...     if str.startswith("git rev-list"):
        ...         return "123456"  ## sha1 of first element of tree
        ...     elif str.startswith("git log"):
        ...         dct = {
        ...             'sha1': "000000",
        ...             'sha1_short': "000",
        ...             'subject': SUBJECT,
        ...             'author_name': "John Smith",
        ...             'author_date': "Tue Feb 14 20:31:22 2017 +0700",
        ...             'author_email': "john.smith@example.com",
        ...             'author_date_timestamp': "0",   ## epoch
        ...             'committer_name': "Alice Wang",
        ...             'committer_date_timestamp': "0", ## epoch
        ...             'raw_body': "my subject\n\n%s" % BODY,
        ...             'body': BODY,
        ...         }
        ...         return "\x00".join([dct[key] for key in GIT_FORMAT_KEYS.keys()])
        ...     raise NotImplementedError()
        ...
        >>> repos.swrap = mock_swrap

    Query, by attributes or items:

        >>> SUBJECT = "fee fie foh"
        >>> BODY = "foo foo foo"

        >>> head = GitCommit(repos, "HEAD")
        >>> head.subject
        Called gitRepos.swrap('git log -n 1 HEAD --pretty=format:...')
        'fee fie foh'
        >>> head.author_name
        'John Smith'

    Notice that on the second call, there's no need to call again git log as
    all the values have already been computed.

    Trailer
    =======

    ``GitCommit`` offers a simple direct API to trailer values. These
    are like RFC822's header value but are at the end of body:

        >>> BODY = '''\
        ... Stuff in the body
        ... Change-id: 1234
        ... Value-X: Supports multi
        ...   line values'''

        >>> head = GitCommit(repos, "HEAD")
        >>> head.trailer_change_id
        Called gitRepos.swrap('git log -n 1 HEAD --pretty=format:...')
        '1234'
        >>> head.trailer_value_x
        'Supports multi\nline values'

    Notice how the multi-line value was unindented.
    In case of multiple values, these are concatened in lists:

        >>> BODY = '''\
        ... Stuff in the body
        ... Co-Authored-By: Bob
        ... Co-Authored-By: Alice
        ... Co-Authored-By: Jack
        ... '''

        >>> head = GitCommit(repos, "HEAD")
        >>> head.trailer_co_authored_by
        Called gitRepos.swrap('git log -n 1 HEAD --pretty=format:...')
        ['Bob', 'Alice', 'Jack']

    Special values
    ==============

    Authors
    -------

        >>> BODY = '''\
        ... Stuff in the body
        ... Co-Authored-By: Bob
        ... Co-Authored-By: Alice
        ... Co-Authored-By: Jack
        ... '''

        >>> head = GitCommit(repos, "HEAD")
        >>> head.author_names
        Called gitRepos.swrap('git log -n 1 HEAD --pretty=format:...')
        ['Alice', 'Bob', 'Jack', 'John Smith']

    Notice that they are printed in alphabetical order.

    """

    def __init__(self, repos, identifier):
        super(GitCommit, self).__init__(repos)
        self.identifier = identifier
        self._trailer_parsed = False

    def __getattr__(self, label):
        """Completes commits attributes upon request."""
        attrs = GIT_FORMAT_KEYS.keys()
        if label not in attrs:
            try:
                return self.__dict__[label]
            except KeyError:
                if self._trailer_parsed:
                    raise AttributeError(label)
                ## let's force the reading of all data from the commit
                ## to look through body for additional RFC822's header keys
                pass

        identifier = self.identifier
        if identifier == "LAST":
            identifier = self.swrap(
                "git rev-list --first-parent --max-parents=0 HEAD")

        ## Compute only missing information
        missing_attrs = [l for l in attrs if not l in self.__dict__]
        ## some commit can be already fully specified (see ``mk_commit``)
        if missing_attrs:
            aformat = "%x00".join(GIT_FORMAT_KEYS[l]
                                  for l in missing_attrs)
            try:
                ret = self.swrap("git log -n 1 %s --pretty=format:%s --"
                                 % (identifier, aformat))
            except ShellError:
                raise ValueError("Given commit identifier %s doesn't exists"
                                 % self.identifier)
            attr_values = ret.split("\x00")
            for attr, value in zip(missing_attrs, attr_values):
                setattr(self, attr, value.strip())

        ## Let's interpret RFC822-like header keys that could be in the body
        match = re.search(REGEX_RFC822_POSTFIX, self.body)
        if match is not None:
            pos = match.start()
            postfix = self.body[pos:]
            self.body = self.body[:pos]
            if postfix:
                for match in re.finditer(REGEX_RFC822_KEY_VALUE, postfix):
                    dct = match.groupdict()
                    key = dct["key"].replace("-", "_").lower()
                    if "\n" in dct["value"]:
                        first_line, remaining = dct["value"].split('\n', 1)
                        value = "%s\n%s" % (first_line, textwrap.dedent(remaining))
                    else:
                        value = dct["value"]
                    try:
                        prev_value = self.__dict__["trailer_%s" % key]
                    except KeyError:
                        setattr(self, "trailer_%s" % key, value)
                    else:
                        setattr(self, "trailer_%s" % key,
                                prev_value + [value, ]
                                if isinstance(prev_value, list)
                                else [prev_value, value, ])
        self._trailer_parsed = True
        return getattr(self, label)

    @property
    def author_names(self):
        return [re.sub(r'^([^<]+)<[^>]+>\s*$', r'\1', author).strip()
                for author in self.authors]

    @property
    def authors(self):
        co_authors = getattr(self, 'trailer_co_authored_by', [])
        co_authors = co_authors if isinstance(co_authors, list) else [co_authors]
        return sorted(co_authors + ["%s <%s>" % (self.author_name, self.author_email)])

    @property
    def date(self):
        d = datetime.datetime.utcfromtimestamp(
            float(self.author_date_timestamp))
        return d.strftime('%Y-%m-%d')

    def __le__(self, value):
        if not isinstance(value, GitCommit):
            value = self._repos.commit(value)
        try:
            self.swrap("git merge-base --is-ancestor '%s' '%s'"
                       % (self.sha1, value.sha1))
            return True
        except ShellError:
            return False

    def __lt__(self, value):
        if not isinstance(value, GitCommit):
            value = self._repos.commit(value)
        return self <= value and not self == value

    def __eq__(self, value):
        if not isinstance(value, GitCommit):
            value = self._repos.commit(value)
        return self.sha1 == value.sha1

    def __hash__(self):
        return hash(self.sha1)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.identifier)


def normpath(path, cwd=None):
    """path can be absolute or relative, if relative it uses the cwd given as
    param.

    """
    if os.path.isabs(path):
        return path
    cwd = cwd if cwd else os.getcwd()
    return os.path.normpath(os.path.join(cwd, path))


class GitConfig(SubGitObjectMixin):
    """Interface to config values of git

    Let's create a fake GitRepos:

        >>> from minimock import Mock
        >>> repos = Mock("gitRepos")

    Initialization:

        >>> cfg = GitConfig(repos)

    Query, by attributes or items:

        >>> repos.swrap.mock_returns = "bar"
        >>> cfg.foo
        Called gitRepos.swrap("git config 'foo'")
        'bar'
        >>> cfg["foo"]
        Called gitRepos.swrap("git config 'foo'")
        'bar'
        >>> cfg.get("foo")
        Called gitRepos.swrap("git config 'foo'")
        'bar'
        >>> cfg["foo.wiz"]
        Called gitRepos.swrap("git config 'foo.wiz'")
        'bar'

    Notice that you can't use attribute search in subsection as ``cfg.foo.wiz``
    That's because in git config files, you can have a value attached to
    an element, and this element can also be a section.

    Nevertheless, you can do:

        >>> getattr(cfg, "foo.wiz")
        Called gitRepos.swrap("git config 'foo.wiz'")
        'bar'

    Default values
    --------------

    get item, and getattr default values can be used:

        >>> del repos.swrap.mock_returns
        >>> repos.swrap.mock_raises = ShellError('Key not found',
        ...                                      errlvl=1, out="", err="")

        >>> getattr(cfg, "foo", "default")
        Called gitRepos.swrap("git config 'foo'")
        'default'

        >>> cfg["foo"]  ## doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        KeyError: 'foo'

        >>> getattr(cfg, "foo")  ## doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError...

        >>> cfg.get("foo", "default")
        Called gitRepos.swrap("git config 'foo'")
        'default'

        >>> print("%r" % cfg.get("foo"))
        Called gitRepos.swrap("git config 'foo'")
        None

    """

    def __init__(self, repos):
        super(GitConfig, self).__init__(repos)

    def __getattr__(self, label):
        cmd = "git config %r" % str(label)
        try:
            res = self.swrap(cmd)
        except ShellError as e:
            if e.errlvl == 1 and e.out == "":
                raise AttributeError("key %r is not found in git config."
                                     % label)
            raise
        return res

    def get(self, label, default=None):
        return getattr(self, label, default)

    def __getitem__(self, label):
        try:
            return getattr(self, label)
        except AttributeError:
            raise KeyError(label)


class GitRepos(object):

    def __init__(self, path):

        ## Saving this original path to ensure all future git commands
        ## will be done from this location.
        self._orig_path = os.path.abspath(path)

        ## verify ``git`` command is accessible:
        try:
            self._git_version = self.swrap("git version")
        except ShellError:
            if DEBUG:
                raise
            raise EnvironmentError(
                "Required ``git`` command not found or broken in $PATH. "
                "(calling ``git version`` failed.)")

        ## verify that we are in a git repository
        try:
            self.swrap("git remote")
        except ShellError:
            if DEBUG:
                raise
            raise EnvironmentError(
                "Not in a git repository. (calling ``git remote`` failed.)")

        self.bare = self.swrap("git rev-parse --is-bare-repository") == "true"
        self.toplevel = None if self.bare else \
                        self.swrap("git rev-parse --show-toplevel")
        self.gitdir = normpath(
            os.path.join(self._orig_path,
                         self.swrap("git rev-parse --git-dir")))

    @classmethod
    def create(cls, dir, *args, **kwargs):
        os.mkdir(dir)
        return cls.init(dir, *args, **kwargs)

    @classmethod
    def init(cls, dir, user=None, email=None):
        with set_cwd(dir):
            wrap("git init .")
            if user:
                wrap("git config user.email '%s'" % user)
            if email:
                wrap("git config user.name '%s'" % user)
        return cls(dir)

    def commit(self, identifier):
        return GitCommit(self, identifier)

    @property
    def config(self):
        return GitConfig(self)

    def swrap(self, command, **kwargs):
        """Essential force the CWD of the command to be in self._orig_path"""
        old_dir = os.path.curdir
        os.chdir(self._orig_path)
        try:
            command = "%s" % (command,)
            return swrap(command, **kwargs)
        finally:
            os.chdir(old_dir)

    def tags(self, contains=None):
        """String list of repository's tag names

        Current tag order is committer date timestamp of tagged commit.
        No firm reason for that, and it could change in future version.

        """
        if contains:
            tags = self.swrap("git tag -l --contains '%s'" % contains).split("\n")
        else:
            tags = self.swrap('git tag -l').split("\n")
        ## Should we use new version name sorting ?  refering to :
        ## ``git tags --sort -v:refname`` in git version >2.0.
        ## Sorting and reversing with command line is not available on
        ## git version <2.0
        return sorted([self.commit(tag) for tag in tags if tag != ''],
                      key=lambda x: int(x.committer_date_timestamp))

    def log(self, includes=["HEAD", ], excludes=[], include_merge=True,
            encoding=_preferred_encoding):
        """Reverse chronological list of git repository's commits

        Note: rev lists can be GitCommit instance list or identifier list.

        """

        refs = {'includes': includes,
                'excludes': excludes}
        for ref_type in ('includes', 'excludes'):
            for idx, ref in enumerate(refs[ref_type]):
                if not isinstance(ref, GitCommit):
                    refs[ref_type][idx] = self.commit(ref)

        ## --topo-order: don't mix commits from separate branches.
        plog = Proc("git log --stdin -z --topo-order --pretty=format:%s %s --"
                    % (GIT_FULL_FORMAT_STRING,
                       '--no-merges' if not include_merge else ''),
                    encoding=encoding)
        for ref in refs["includes"]:
            plog.stdin.write("%s\n" % ref.sha1)

        for ref in refs["excludes"]:
            plog.stdin.write("^%s\n" % ref.sha1)
        plog.stdin.close()

        def mk_commit(dct):
            """Creates an already set commit from a dct"""
            c = self.commit(dct["sha1"])
            for k, v in dct.items():
                setattr(c, k, v)
            return c

        values = plog.stdout.read("\x00")

        try:
            while True:  ## next(values) will eventualy raise a StopIteration
                yield mk_commit(dict([(key, next(values))
                                      for key in GIT_FORMAT_KEYS]))
        finally:
            plog.stdout.close()
            plog.stderr.close()


def first_matching(section_regexps, string):
    for section, regexps in section_regexps:
        if regexps is None:
            return section
        for regexp in regexps:
            if re.search(regexp, string) is not None:
                return section


def ensure_template_file_exists(label, template_name):
    """Return template file path given a label hint and the template name

    Template name can be either a filename with full path,
    if this is the case, the label is of no use.

    If ``template_name`` does not refer to an existing file,
    then ``label`` is used to find a template file in the
    the bundled ones.

    """

    if os.path.isfile(template_name):
        return template_name

    template_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "templates", label)

    template_path = os.path.join(template_dir, "%s.tpl" % template_name)

    if not os.path.exists(template_path):
        templates = glob.glob(os.path.join(template_dir, "*.tpl"))
        if len(templates) > 0:
            msg = ("These are the available %s templates:" % label)
            msg += "\n - " + \
                   "\n - ".join(os.path.basename(f).split(".")[0]
                                for f in templates)
            msg += "\nTemplates are located in %r" % template_dir
        else:
            msg = "No available %s templates found in %r." \
                  % (label, template_dir)
        die("Error: Invalid %s template name %r.\n" % (label, template_name) +
            "%s" % msg)

    return template_path

##
## Output Engines
##

@available_in_config
def rest_py(data, opts={}):
    """Returns ReStructured Text changelog content from data"""

    def rest_title(label, char="="):
        return (label.strip() + "\n") + (char * len(label) + "\n")

    def render_version(version):
        title = "%s (%s)" % (version["tag"], version["date"]) \
                if version["tag"] else \
                opts["unreleased_version_label"]
        s = rest_title(title, char="-")

        sections = version["sections"]
        nb_sections = len(sections)
        for section in sections:

            section_label = section["label"] if section.get("label", None) \
                            else "Other"

            if not (section_label == "Other" and nb_sections == 1):
                s += "\n" + rest_title(section_label, "~")

            for commit in section["commits"]:
                s += render_commit(commit)
        return s

    def render_commit(commit, opts=opts):
        subject = commit["subject"]
        subject += " [%s]" % (", ".join(commit["authors"]), )

        entry = indent('\n'.join(textwrap.wrap(subject)),
                       first="- ").strip() + "\n"

        if commit["body"]:
            entry += "\n" + indent(commit["body"])
            entry += "\n"

        return entry

    if data["title"]:
        yield rest_title(data["title"], char="=") + "\n\n"

    for version in data["versions"]:
        if len(version["sections"]) > 0:
            yield render_version(version) + "\n\n"

## formatter engines

if pystache:

    @available_in_config
    def mustache(template_name):
        """Return a callable that will render a changelog data structure

        returned callable must take 2 arguments ``data`` and ``opts``.

        """
        template_path = ensure_template_file_exists("mustache", template_name)

        with open(template_path) as f:
            template = f.read()

        def stuffed_versions(versions, opts):
            for version in versions:
                title = "%s (%s)" % (version["tag"], version["date"]) \
                        if version["tag"] else \
                        opts["unreleased_version_label"]
                version["label"] = title
                version["label_chars"] = list(version["label"])
                for section in version["sections"]:
                    section["label_chars"] = list(section["label"])
                    section["display_label"] = \
                        not (section["label"] == "Other" and
                             len(version["sections"]) == 1)
                    for commit in section["commits"]:
                        commit["author_names_joined"] = ", ".join(
                            commit["authors"])
                        commit["body_indented"] = indent(commit["body"])
                yield version

        def renderer(data, opts):

            ## mustache is very simple so we need to add some intermediate
            ## values
            data["general_title"] = True if data["title"] else False
            data["title_chars"] = list(data["title"]) if data["title"] else []

            data["versions"] = stuffed_versions(data["versions"], opts)

            return pystache.render(template, data)

        return renderer

else:

    @available_in_config
    def mustache(template_name):
        die("Required 'pystache' python module not found.")


if mako:

    import mako.template

    mako_env = dict((f.__name__, f) for f in (ucfirst, indent, textwrap,
                                              paragraph_wrap))

    @available_in_config
    def makotemplate(template_name):
        """Return a callable that will render a changelog data structure

        returned callable must take 2 arguments ``data`` and ``opts``.

        """
        template_path = ensure_template_file_exists("mako", template_name)

        template = mako.template.Template(filename=template_path)

        def renderer(data, opts):
            kwargs = mako_env.copy()
            kwargs.update({"data": data,
                           "opts": opts})
            return template.render(**kwargs)

        return renderer

else:

    @available_in_config
    def makotemplate(template_name):
        die("Required 'mako' python module not found.")


##
## Data Structure
##

def versions_data_iter(repository, revlist=None,
                       ignore_regexps=[],
                       section_regexps=[(None,'')],
                       tag_filter_regexp=r"\d+\.\d+(\.\d+)?",
                       include_merge=True,
                       body_process=lambda x: x,
                       subject_process=lambda x: x,
                       log_encoding=DEFAULT_GIT_LOG_ENCODING,
                       warn=warn,        ## Mostly used for test
                       ):
    """Returns an iterator through versions data structures

    (see ``gitchangelog.rc.sample`` file for more info)

    :param repository: target ``GitRepos`` object
    :param revlist: list of strings that git log understands as revlist
    :param ignore_regexps: list of regexp identifying ignored commit messages
    :param section_regexps: regexps identifying sections
    :param tag_filter_regexp: regexp to match tags used as version
    :param include_merge: whether to include merge commits in the log or not
    :param body_process: text processing object to apply to body
    :param subject_process: text processing object to apply to subject
    :param log_encoding: the encoding used in git logs
    :param warn: callable to output warnings, mocked by tests

    :returns: iterator of versions data_structures

    """

    revlist = revlist or []

    ## Hash to speedup lookups
    versions_done = {}

    excludes = [rev[1:]
                for rev in swrap("git rev-parse --rev-only %s"
                                 % " ".join(revlist)).split("\n")
                if rev.startswith("^")] if revlist else []
    ## Note that ``--reverse -n 1`` still returns the first and not the last element
    contains = swrap("git rev-list %s"
                     % " ".join(revlist)).split("\n")[-1] if revlist else None

    tags = [tag
            for tag in repository.tags(contains=contains)
            if re.match(tag_filter_regexp, tag.identifier)]

    if not tags:
        warn("no tag %sname matching tag_filter_regexp %r."
             % ("contained in revlist %r with " % " ".join(revlist)
                if revlist else "",
                tag_filter_regexp))

    tags.append(repository.commit("HEAD"))

    if revlist:
        max_rev = repository.commit(swrap(
            "git rev-list -n 1 %s"
            % " ".join(revlist))) if revlist else None
        new_tags = []
        for tag in tags:
            if max_rev < tag:
                break
            new_tags.append(tag)
        tags = new_tags

    section_order = [k for k, _v in section_regexps]

    tags = list(reversed(tags))

    ## Get the changes between tags (releases)
    for idx, tag in enumerate(tags):

        ## New version
        current_version = {"date": tag.date}
        current_version["tag"] = tag.identifier \
                                 if tag.identifier != "HEAD" else \
                                 None

        sections = collections.defaultdict(list)
        commits = repository.log(
            includes=[tag],
            excludes=tags[idx + 1:] + excludes,
            include_merge=include_merge,
            encoding=log_encoding)

        for commit in commits:
            if any(re.search(pattern, commit.subject) is not None
                   for pattern in ignore_regexps):
                continue

            matched_section = first_matching(section_regexps, commit.subject)

            ## Finally storing the commit in the matching section

            sections[matched_section].append({
                "author": commit.author_name,
                "authors": commit.author_names,
                "subject": subject_process(commit.subject),
                "body": body_process(commit.body),
                "commit": commit,
            })

        ## Flush current version
        current_version["sections"] = [{"label": k, "commits": sections[k]}
                                       for k in section_order
                                       if k in sections]
        if len(current_version["sections"]) != 0:
            yield current_version
        versions_done[tag] = current_version


def changelog(output_engine=rest_py,
              unreleased_version_label="unreleased",
              warn=warn,        ## Mostly used for test
              **kwargs):
    """Returns a string containing the changelog of given repository

    This function returns a string corresponding to the template rendered with
    the changelog data tree.

    (see ``gitchangelog.rc.sample`` file for more info)

    For an exact list of arguments, see the arguments of
    ``versions_data_iter(..)``.

    :param unreleased_version_label: version label for untagged commits
    :param output_engine: callable to render the changelog data
    :param warn: callable to output warnings, mocked by tests

    :returns: content of changelog

    """

    opts = {
        'unreleased_version_label': unreleased_version_label,
    }

    ## Setting main container of changelog elements
    title = None if kwargs.get("revlist") else "Changelog"
    changelog = {"title": title,
                 "versions": []}

    versions = versions_data_iter(warn=warn, **kwargs)

    ## poke once in versions to know if there's at least one:
    try:
        first_version = next(versions)
    except StopIteration:
        warn("Empty changelog. No commits were elected to be used as entry.")
        changelog["versions"] = []
    else:
        changelog["versions"] = itertools.chain([first_version], versions)

    return output_engine(data=changelog, opts=opts)

##
## Manage obsolete options
##

_obsolete_options_managers = []


def obsolete_option_manager(fun):
    _obsolete_options_managers.append(fun)


@obsolete_option_manager
def obsolete_replace_regexps(config):
    """This option was superseeded by the ``subject_process`` option.

    Each regex replacement you had could be translated in a
    ``ReSub(pattern, replace)`` in the ``subject_process`` pipeline.

    """
    if "replace_regexps" in config:
        for pattern, replace in config["replace_regexps"].items():
            config["subject_process"] = \
                ReSub(pattern, replace) | \
                config.get("subject_process", ucfirst | final_dot)


@obsolete_option_manager
def obsolete_body_split_regexp(config):
    """This option was superseeded by the ``body_process`` option.

    The split regex can now be sent as a ``Wrap(regex)`` text process
    instruction in the ``body_process`` pipeline.

    """
    if "body_split_regex" in config:
        config["body_process"] = Wrap(config["body_split_regex"]) | \
                                 config.get("body_process", noop)


def manage_obsolete_options(config):
    for man in _obsolete_options_managers:
        man(config)


##
## Command line parsing
##

def parse_cmd_line(usage, description, epilog, exname, version):

    import argparse

    try:
        parser = argparse.ArgumentParser(
            usage=usage,
            description=description,
            epilog="\n" + epilog,
            prog=exname,
            formatter_class=argparse.RawTextHelpFormatter,
            version=version)
    except TypeError:  ## compat with argparse from python 3.4
        parser = argparse.ArgumentParser(
            usage=usage,
            description=description,
            epilog="\n" + epilog,
            prog=exname,
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-v', '--version',
                            help="show program's version number and exit",
                            action="version", version=version)

    parser.add_argument('-d', '--debug',
                        help="Enable debug mode (show full tracebacks).",
                        action="store_true", dest="debug")

    subparsers = parser.add_subparsers(help='commands', dest='action',
                                       prog=exname)
    _init_parser = subparsers.add_parser(
        'init', help='Create default config file in current repository.')
    show_parser = subparsers.add_parser(
        'show', help='Prints current changelog.',
        usage='%(exname)s show [REVLIST]' % {'exname': exname})
    show_parser.add_argument('revlist', nargs='*', action="store", default=[])

    ## Python argparse in 2.7 doesn't like --debug to be after
    ## positional argument.
    argv = sys.argv[1:]
    if "--debug" in argv:
        argv.remove("--debug")
        argv = ["--debug", ] + argv
    if "-d" in argv:
        argv.remove("-d")
        argv = ["-d", ] + argv
    if len([action for action in argv if not action.startswith("-")]) == 0:
        ## Then we don't have positional argument, and this won't be supported
        ## by argparse from python 2.7. See http://bugs.python.org/issue9253
        ## so let's cheat and add "show" if no action.
        argv += ["show", ]

    return parser.parse_args(argv)


##
## Main
##

def main():

    global DEBUG
    ## Basic environment infos

    reference_config = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "gitchangelog.rc.reference")

    basename = os.path.basename(sys.argv[0])
    if basename.endswith(".py"):
        basename = basename[:-3]

    debug_varname = "DEBUG_%s" % basename.upper()
    DEBUG = os.environ.get(debug_varname, False)

    ## Support legacy call of ``gitchangelog`` without arguments
    if len(sys.argv) == 1:
        sys.argv.append("show")

    i = lambda x: x % {'exname': basename}

    opts = parse_cmd_line(usage=i(usage_msg),
                          description=i(description_msg),
                          epilog=i(epilog_msg),
                          exname=basename,
                          version=__version__)
    DEBUG = DEBUG or opts.debug

    try:
        repository = GitRepos(".")
    except EnvironmentError as e:
        if DEBUG:
            raise
        try:
            die(str(e))
        except Exception as e2:
            die(repr(e2))

    repository_config = '%s/.%s.rc' % (repository.toplevel, basename) \
                        if not repository.bare else None

    if opts.action == "init":
        import shutil
        if repository_config is None:
            die("``init`` of bare repository not supported.")
        if os.path.exists(repository_config):
            die("File %r already exists." % repository_config)
        if not os.path.exists(reference_config):
            die("Reference file %r not found." % reference_config)
        shutil.copyfile(reference_config,
                        repository_config)
        print("File %r created." % repository_config)
        sys.exit(0)

    try:
        gc_rc = repository.config.get("gitchangelog.rc-path")
    except ShellError as e:
        stderr(
            "Error parsing git config: %s."
            " Won't be able to read 'rc-path' if defined."
            % (str(e)))
        gc_rc = None

    gc_rc = normpath(gc_rc, cwd=repository.toplevel) if gc_rc else None

    ## config file lookup resolution
    for enforce_file_existence, fun in [
        (True, lambda: os.environ.get('GITCHANGELOG_CONFIG_FILENAME')),
        (True, lambda: gc_rc),
        (False, lambda: ('%s/.%s.rc' % (repository.toplevel, basename)) \
                        if not repository.bare else None),
        ## Removed to enforce per-repository gitchangelog file.
        # (False, lambda: os.path.expanduser('~/.%s.rc' % basename)),
        # (False, lambda: '/etc/%s.rc' % basename),
        ]:
        changelogrc = fun()
        if changelogrc:
            if not os.path.exists(changelogrc):
                if enforce_file_existence:
                    die("File %r does not exists." % changelogrc)
                else:
                    continue  ## changelogrc valued, but file does not exists
            else:
                break

    if not os.path.exists(reference_config):
        die("Config reference file %r not found." % reference_config)

    ## config file may lookup for templates relative to the toplevel
    ## of git repository
    os.chdir(repository.toplevel)

    config = load_config_file(
        os.path.expanduser(changelogrc),
        default_filename=reference_config,
        fail_if_not_present=False)

    log_encoding = config.get("log_encoding", None)
    if log_encoding is None:
        try:
            log_encoding = repository.config.get("i18n.logOuputEncoding")
        except ShellError as e:
            stderr(
                "Error parsing git config: %s."
                " Won't be able to read 'rc-path' if defined."
                % (str(e)))
            gc_rc = None

    ## Final defaults coming from git defaults
    log_encoding = log_encoding or DEFAULT_GIT_LOG_ENCODING

    manage_obsolete_options(config)

    try:
        content = changelog(
            repository=repository, revlist=opts.revlist,
            ignore_regexps=config['ignore_regexps'],
            section_regexps=config['section_regexps'],
            unreleased_version_label=config['unreleased_version_label'],
            tag_filter_regexp=config['tag_filter_regexp'],
            output_engine=config.get("output_engine", rest_py),
            include_merge=config.get("include_merge", True),
            body_process=config.get("body_process", noop),
            subject_process=config.get("subject_process", noop),
            log_encoding=log_encoding,
        )
    except KeyboardInterrupt:
        if DEBUG:
            err("Keyboard interrupt received while running '%s':"
                % (basename, ))
            stderr(format_last_exception())
        else:
            err("Keyboard Interrupt. Bailing out.")
        exit(254)
    except Exception as e:  ## pylint: disable=broad-except
        if DEBUG:
            err("Exception while running '%s':"
                % (basename, ))
            stderr(format_last_exception())
        else:
            message = "%s" % e
            err(message)
            stderr("  (set %s environment variable, "
                   "or use ``--debug`` to see full traceback)" %
                   (debug_varname, ))
        exit(255)

    compat_encode = lambda str: str if PY3 else str.encode(_preferred_encoding)

    try:
        if isinstance(content, collections.Iterator):
            for chunk in content:
                print(compat_encode(chunk), end='')
        else:
            print(compat_encode(content), end='')
    except UnicodeEncodeError:
        if DEBUG:
            raise
        stderr("""\
UnicodeEncodeError:
  There was a problem outputing the resulting changelog to your console.

  This probably means that the changelog contains characters that can't
  be translated to characters in your current charset (%s).
""" % sys.stdout.encoding)
        if WIN32 and PY_VERSION < 3.6 and sys.stdout.encoding != 'utf-8':
            ## As of PY 3.6, encoding is now ``utf-8`` regardless of
            ## PYTHONIOENCODING
            ## https://www.python.org/dev/peps/pep-0528/
            stderr("  You might want to try to fix that by setting "
                   "PYTHONIOENCODING to 'utf-8'.")
        exit(1)

##
## Launch program
##

if __name__ == "__main__":
    main()
