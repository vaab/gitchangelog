#!/usr/bin/env python

import re
import os
import os.path
import sys
import glob
import textwrap
import datetime
import collections

from subprocess import Popen, PIPE

try:
    import pystache
except ImportError:
    pystache = None

try:
    import mako
except ImportError:
    mako = None



usage_msg = """usage: %(exname)s [REPOS]"""
help_msg = """Run this command in a git repository to get a ReST changelog in stdout.

%(exname)s uses a config file to filter meaningfull commit or do some
 formatting in commit messages thanks to a config file.

Config file location will be resolved in this order:

  - in shell environment variable GITCHANGELOG_CONFIG_FILENAME
  - in git configuration: ``git config gitchangelog.rc-path``
  - as '.%(exname)s.rc' in the root of the current git repository
  - as '~/.%(exname)s.rc'
  - as '/etc/%(exname)s'

"""

full_help_msg = "%s\n\n%s" % (usage_msg, help_msg)


class ShellError(Exception):

    def __init__(self, msg, errlvl=None, command=None, out=None, err=None):
        self.errlvl = errlvl
        self.command = command
        self.out = out
        self.err = err
        super(ShellError, self).__init__(msg)


def die(msg=None):
    if msg:
        sys.stderr.write(msg + "\n")
    sys.exit(1)

##
## config file functions
##


_config_env = {}


def available_in_config(f):
    _config_env[f.__name__] = f
    return f


def load_config_file(filename, fail_if_not_present=True):
    """Loads data from a config file."""

    config = _config_env.copy()

    if os.path.exists(filename):
        try:
            execfile(filename, config)
        except SyntaxError, e:
            die('Syntax error in config file: %s\n'
                'Line %i offset %i\n' % (filename, e.lineno, e.offset))
    else:
        if fail_if_not_present:
            die('%r config file is not found and is required.' % (filename, ))

    return config


##
## Text functions
##


def ucfirst(msg):
    return msg[0].upper() + msg[1:]


def final_dot(msg):
    if len(msg) == 0:
        return "No commit message."
    if msg[-1].isalnum():
        return msg + "."
    return msg


def indent(text, chars="  ", first=None):
    """Return text string indented with the given chars

    >>> string = 'This is first line.\\nThis is second line\\n'

    >>> print indent(string, chars="| ") # doctest: +NORMALIZE_WHITESPACE
    | This is first line.
    | This is second line
    |

    >>> print indent(string, first="- ") # doctest: +NORMALIZE_WHITESPACE
    - This is first line.
      This is second line


    """
    if first:
        first_line = text.split("\n")[0]
        rest = '\n'.join(text.split("\n")[1:])
        return '\n'.join([first + first_line,
                          indent(rest, chars=chars)])
    return '\n'.join([chars + line
                      for line in text.split('\n')])


def paragraph_wrap(text, regexp="\n\n"):
    r"""Wrap text by making sure that paragraph are separated correctly

    >>> string = 'This is first paragraph which is quite long don\'t you \
    ... think ? Well, I think so.\n\nThis is second paragraph\n'

    >>> print paragraph_wrap(string) # doctest: +NORMALIZE_WHITESPACE
    This is first paragraph which is quite long don't you think ? Well, I
    think so.
    This is second paragraph

    Notice that that each paragraph has been wrapped separately.

    """
    regexp = re.compile(regexp, re.MULTILINE)
    return "\n".join("\n".join(textwrap.wrap(paragraph.strip()))
                     for paragraph in regexp.split(text)).strip()


##
## System functions
##


def cmd(command):

    p = Popen(command, shell=True,
              stdin=PIPE, stdout=PIPE, stderr=PIPE,
              close_fds=True)
    stdout, stderr = p.communicate()
    return stdout, stderr, p.returncode


def wrap(command, ignore_errlvls=[0]):
    """Wraps a shell command and casts an exception on unexpected errlvl

    >>> wrap('/tmp/lsdjflkjf') # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ShellError: Wrapped command '/tmp/lsdjflkjf' exited with errorlevel 127.
      stderr:
      | /bin/sh: .../tmp/lsdjflkjf: not found

    >>> wrap('echo hello') # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'hello\\n'

    """

    out, err, errlvl = cmd(command)

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


class GitCommit(SubGitObjectMixin):

    def __init__(self, identifier, repos):
        super(GitCommit, self).__init__(repos)

        self.identifier = identifier

        if identifier is "LAST":
            identifier = self.swrap(
                "git rev-list --first-parent --max-parents=0 HEAD")

        attrs = {'sha1': "%h",
                 'subject': "%s",
                 'author_name': "%an",
                 'author_date': "%ad",
                 'author_date_timestamp': "%at",
                 'committer_name': "%cn",
                 'committer_date_timestamp': "%ct",
                 'raw_body': "%B",
                 'body': "%b",
                 }
        aformat = "%x00".join(attrs.values())
        try:
            ret = self.swrap("git show -s %r --pretty=format:%s"
                             % (identifier, aformat))
        except ShellError:
            raise ValueError("Given commit identifier %r doesn't exists"
                             % identifier)
        attr_values = ret.split("\x00")
        for attr, value in zip(attrs.keys(), attr_values):
            setattr(self, attr, value.strip())

    @property
    def date(self):
        d = datetime.datetime.utcfromtimestamp(
            float(self.author_date_timestamp))
        return d.strftime('%Y-%m-%d')

    def __eq__(self, value):
        if not isinstance(value, GitCommit):
            return False
        return self.sha1 == value.sha1

    def __hash__(self):
        return hash(self.sha1)

    def __sub__(self, value):
        if not isinstance(value, GitCommit):
            raise TypeError("Invalid type for %r in operation" % value)
        if self.sha1 == value.sha1:
            return []
        commits = self.swrap('git rev-list --reverse %s..%s'
                             % (value.sha1, self.sha1))
        if not commits:
            raise ValueError('Seems that %r is earlier than %r'
                             % (self.identifier, value.identifier))
        return [GitCommit(commit, self._repos)
                for commit in commits.split('\n')]

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

        >>> print "%r" % cfg.get("foo")
        Called gitRepos.swrap("git config 'foo'")
        None

    """

    def __init__(self, repos):
        super(GitConfig, self).__init__(repos)

    def __getattr__(self, label):
        cmd = "git config %r" % str(label)
        try:
            res = self.swrap(cmd)
        except ShellError, e:
            if e.errlvl == 1 and e.out == "" and e.err == "":
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

        self.bare = self.swrap("git rev-parse --is-bare-repository") == "true"
        self.toplevel = None if self.bare else \
                        self.swrap("git rev-parse --show-toplevel")
        self.gitdir = os.path.normpath(
            os.path.join(self._orig_path,
                         self.swrap("git rev-parse --git-dir")))

    @property
    def config(self):
        return GitConfig(self)

    def swrap(self, command, **kwargs):
        """Essential force the CWD of the command to be in self._orig_path"""

        command = "cd %s; %s" % (self._orig_path, command)
        return swrap(command, **kwargs)

    @property
    def tags(self):
        tags = self.swrap('git tag -l').split("\n")
        while '' in tags:
            tags.remove('')
        return sorted([GitCommit(tag, self) for tag in tags],
                      key=lambda x: int(x.committer_date_timestamp))

    def __getitem__(self, key):

        if isinstance(key, basestring):
            return GitCommit(key, self)

        if isinstance(key, slice):
            start, stop = key.start, key.stop

            if start is None:
                start = GitCommit('LAST', self)

            if stop is None:
                stop = GitCommit('HEAD', self)

            return stop - start
        raise NotImplementedError("Unsupported getitem %r object." % key)


def first_matching(section_regexps, string):
    for section, regexps in section_regexps:
        if regexps is None:
            return section
        for regexp in regexps:
            if re.search(regexp, string) is not None:
                return section

##
## Output Engines
##

@available_in_config
def rest_py(data, opts={}):
    """Returns ReStructured Text changelog content from data"""

    def rest_title(label, char="="):
        return (label.strip() + "\n") + (char * len(label) + "\n")

    def render_version(title, sections):
        s = rest_title(title, char="-") + "\n"

        nb_sections = len(sections)
        for section in sections:

            section_label = section["label"] if section.get("label", None) \
                            else "Other"

            if not (section_label == "Other" and nb_sections == 1):
                s += rest_title(section_label, "~") + "\n"

            for commit in section["commits"]:
                s += render_commit(commit)
        return s

    def render_commit(commit, opts=opts):
        subject = commit["subject"]
        subject += " [%s]" % (commit["author"], )

        entry = indent('\n'.join(textwrap.wrap(ucfirst(subject))),
                       first="- ").strip() + "\n\n"

        if commit["body"]:
            entry += indent(paragraph_wrap(commit["body"],
                                           regexp=opts["body_split_regexp"]))
            entry += "\n\n"

        return entry


    return (rest_title(data["title"], char="=") + "\n" +
            "".join(render_version(title=version["label"],
                                   sections=version["sections"])
                    for version in data["versions"]
                    if len(version["sections"]) > 0))

## formatter engines

if pystache:

    @available_in_config
    def mustache(template_name):
        """Return a callable that will render a changelog data structure

        returned callable must take 2 arguments ``data`` and ``opts``.

        """
        template_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "templates", "mustache")

        template_path = os.path.join(template_dir, "%s.tpl" % template_name)

        if not os.path.exists(template_path):
            templates = glob.glob(os.path.join(template_dir, "*.tpl"))
            if len(templates) > 0:
                msg = "Available mustache templates:\n - " + \
                      " - ".join(os.path.basename(f).split(".")[-1]
                                 for f in templates)
            else:
                msg = "No available mustache templates found in %r." \
                      % template_dir
            die("%s\n" % msg +
                "Invalid mustache template name %s." % template_name)

        with open(template_path) as f:
            template = f.read()

        def renderer(data, opts):

            ## mustache is very simple so we need to add some intermediate
            ## values
            data["title_chars"] = list(data["title"])
            for version in data["versions"]:
                version["label_chars"] = list(version["label"])
                for section in version["sections"]:
                    section["label_chars"] = list(section["label"])
                    for commit in section["commits"]:
                        commit["body_indented"] = indent(
                            paragraph_wrap(commit["body"],
                                           regexp=opts["body_split_regexp"]),
                            chars="    ")

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
        template_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "templates", "mako")

        template_path = os.path.join(template_dir, "%s.tpl" % template_name)

        if not os.path.exists(template_path):
            print "Available mako templates:\n - " + \
                  " - ".join(os.path.basename(f).split(".")[-1]
                             for f in glob.glob(os.path.join(template_dir,
                                                             "*.tpl")))
            die("No %r a valid mako template name." % template_name)

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

def changelog(repository,
              ignore_regexps=[],
              replace_regexps={},
              section_regexps={},
              unreleased_version_label="unreleased",
              tag_filter_regexp=r"\d+\.\d+(\.\d+)?",
              body_split_regexp="\n\n",
              output_engine=rest_py,
              ):
    """Returns a string containing the changelog of given repository

    This function returns a string corresponding to the template rendered with
    the changelog data tree.

    (see ``gitchangelog.rc.sample`` file for more info)

    :param repository: target ``GitRepos`` object
    :param ignore_regexps: list of regexp identifying ignored commit messages
    :param replace_regexps: regexps used to replace elements in commit messages
    :param section_regexps: regexps identifying sections
    :param tag_filter_regexp: regexp to match tags used as version
    :param body_split_regexp: regexp identifying the body of a commit message
    :param unreleased_version_label: version label for untagged commits
    :param template_format: format of template to generate the changelog

    :returns: content of changelog

    """

    def new_version(tag, date, opts):
        title = "%s (%s)" % (tag, date) if tag else \
                opts["unreleased_version_label"]
        return {"label": title,
                "tag": tag,
                "date": date,
                }

    opts = {
        'unreleased_version_label': unreleased_version_label,
        'body_split_regexp': body_split_regexp,
        }

    # setting main container of changelog elements
    title = "Changelog"
    changelog = {"title": title,
                 "versions": []}

    ## Hash to speedup lookups
    versions_done = {}

    ## Create unreleased version
    current_version = new_version(tag=None, date=None, opts=opts)
    sections = collections.defaultdict(list)

    tags = [tag
            for tag in reversed(repository.tags)
            if re.match(tag_filter_regexp, tag.identifier)]

    section_order = [k for k, _v in section_regexps]

    for commit in reversed(repository[:]):

        tags_of_commit = [tag for tag in tags
                          if tag == commit]

        if len(tags_of_commit) > 0:
            tag = tags_of_commit[0]

            ## End of current version, let's flush current one.
            current_version["sections"] = [{"label": k, "commits": sections[k]}
                                           for k in section_order
                                           if k in sections]
            changelog["versions"].append(current_version)
            versions_done[tag] = current_version
            current_version = new_version(tag.identifier, commit.date, opts)
            sections = collections.defaultdict(list)

        if any(re.search(pattern, commit.subject) is not None
               for pattern in ignore_regexps):
            continue

        matched_section = first_matching(section_regexps, commit.subject)

        ## Replace content in commit subject

        subject = commit.subject
        for regexp, replacement in replace_regexps.iteritems():
            subject = re.sub(regexp, replacement, subject)

        ## Finally storing the commit in the matching section

        subject = final_dot(subject)

        sections[matched_section].append({
            "author": commit.author_name,
            "subject": subject,
            "body": commit.body,
            })

    ## Don't forget last commits:
    current_version["sections"] = [{"label": k, "commits": sections[k]}
                                   for k in section_order
                                   if k in sections]
    changelog["versions"].append(current_version)

    return output_engine(data=changelog, opts=opts)

##
## Main
##

def main():

    basename = os.path.basename(sys.argv[0])
    if basename.endswith(".py"):
        basename = basename[:-3]

    if len(sys.argv) == 1:
        repos = "."
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--help":
            print full_help_msg % {'exname': basename}
            sys.exit(0)
        repos = sys.argv[1]
    else:
        die(usage_msg % {'exname': basename})

    ## warning: not safe (repos is given by the user)
    repository = GitRepos(repos)

    try:
        gc_rc = repository.config.get("gitchangelog.rc-path")
    except ShellError, e:
        sys.stderr.write(
            "Error parsing git config: %s."
            " Won't be able to read 'rc-path' if defined.\n"
            % (str(e)))
        gc_rc = None

    gc_rc = normpath(gc_rc, cwd=repository.toplevel) if gc_rc else None

    ## config file lookup resolution
    for enforce_file_existence, fun in [
        (True, lambda: os.environ.get('GITCHANGELOG_CONFIG_FILENAME')),
        (True, lambda: gc_rc),
        (False, lambda: ('%s/.%s.rc' % (repository.toplevel, basename)) \
                 if not repository.bare else None),
        (False, lambda: os.path.expanduser('~/.%s.rc' % basename)),
        (False, lambda: '/etc/%s.rc' % basename),
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

    if not changelogrc or not os.path.exists(changelogrc):
        die("No %s config file found anywhere !\n"
            "Perhaps you should consult 'gitchangelog --help'." % basename)

    config = load_config_file(os.path.expanduser(changelogrc))

    print changelog(repository,
        ignore_regexps=config['ignore_regexps'],
        replace_regexps=config['replace_regexps'],
        section_regexps=config['section_regexps'],
        unreleased_version_label=config['unreleased_version_label'],
        tag_filter_regexp=config['tag_filter_regexp'],
        body_split_regexp=config['body_split_regexp'],
        output_engine=config.get("output_engine", rest_py),
    )

##
## Launch program
##

if __name__ == "__main__":

    # import doctest
    # doctest.testmod()
    # sys.exit(1)

    main()
