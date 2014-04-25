#!/bin/bash

exname="$(basename "$0")"

##
## Functions
##

function get_path() {
    local type

    type="$(type -t "$1")"
    case $type in
	("file")
	    type -p "$1"
	    return 0
	    ;;
	("function" | "builtin" )
	    echo "$1"
	    return 0
	    ;;
    esac
    return 1
}

function print_exit() {
    echo $@
    exit 1
}

function print_syntax_error() {
    [ "$*" ] ||	print_syntax_error "$FUNCNAME: no arguments"
    print_exit "${ERROR}script error:${NORMAL} $@" >&2
}

function print_syntax_warning() {
    [ "$*" ] || print_syntax_error "$FUNCNAME: no arguments."
    [ "$exname" ] || print_syntax_error "$FUNCNAME: 'exname' var is null or not defined."
    echo "$exname: ${WARNING}script warning:${NORMAL} $@" >&2
}

function print_error() {
    [ "$*" ] || print_syntax_warning "$FUNCNAME: no arguments."
    [ "$exname" ] || print_exit "$FUNCNAME: 'exname' var is null or not defined." >&2
    print_exit "$exname: ${ERROR}error:${NORMAL} $@" >&2
}

function depends() {

    local i tr path

    tr=$(get_path "tr")
    test "$tr" ||
	print_error "dependency check : couldn't find 'tr' command."

    for i in $@ ; do

      if ! path=$(get_path $i); then
	  new_name=$(echo $i | "$tr" '_' '-')
	  if [ "$new_name" != "$i" ]; then
	     depends "$new_name"
	  else
	     print_error "dependency check : couldn't find '$i' command."
	  fi
      else
	  if ! test -z "$path" ; then
	      export "$(echo $i | "$tr" '-' '_')"=$path
	  fi
      fi

    done
}

function die() {
    [ "$*" ] || print_syntax_warning "$FUNCNAME: no arguments."
    [ "$exname" ] || print_exit "$FUNCNAME: 'exname' var is null or not defined." >&2
    print_exit "$exname: ${ERROR}error:${NORMAL} $@" >&2
}

##
## Code
##

depends git grep date

## BSD / GNU sed compatibility layer
if (type -p sed) >/dev/null 2>&1; then
    sed="$(type -p sed)"
    sed_re_opt="-E"
else
    if (type -p gsed && gsed --version) >/dev/null 2>&1; then
        sed="$(type -p gsed)"
        sed_re_opt="-r"
    else
        print_error "$exname: required GNU sed not found"
    fi
fi

## BSD / GNU date compatibility layer
if (type -p date) >/dev/null 2>&1 ; then
    date="$(type -p date)"
    date_opts="-j -f %s "
else
    if (type -p gdate && gdate --version) >/dev/null 2>&1; then
        date="$(type -p gdate)"
        date_opts="-d @"
    else
        print_error "$exname: required GNU date not found"
    fi
fi


gitchangelog=./gitchangelog.py

if ! test -e "setup.py" >/dev/null 2>&1; then
    die "No 'setup.py'... this script is meant to work with a python project"
fi

if ! "$git" describe --tags >/dev/null 2>&1; then
    die "Didn't find a git repository. autogen.sh uses git to create changelog \
         and version information."
fi


function matches() {
   echo "$1" | "$grep" -E "^$2\$" >/dev/null 2>&1
}


long_tag="[0-9]+\.[0-9]+(\.[0-9]+)?-[0-9]+-[0-9a-f]+"
short_tag="[0-9]+\.[0-9]+(\.[0-9]+)?"

get_short_tag="s/^($short_tag).*\$/\1/g"


function get_current_git_date_timestamp() {
    "$git" show -s --pretty=format:%ct
}


function dev_version_tag() {
    "$date" ${date_opts}$(get_current_git_date_timestamp) +%Y%m%d%H%M
}


function get_current_version() {

    version=$("$git" describe --tags)
    if matches "$version" "$short_tag"; then
        echo "$version"
    else
        version=$(echo "$version" | "$sed" "$sed_re_opt" "$get_short_tag")
        echo "${version}.1dev_r$(dev_version_tag)"
    fi

}

function set_version_setup_py() {

    version=$(get_current_version)
    short_version=$(echo "$version" | cut -f 1,2,3 -d ".")

    "$sed" -i "$sed_re_opt" "s/%%version%%/$version/g" setup.py \
                                       CHANGELOG.rst &&
    "$sed" -i "$sed_re_opt" "s/%%short-version%%/${short_version}/g" \
                                       setup.py \
                                       CHANGELOG.rst &&
    echo "Version updated to $version."
}


GITCHANGELOG_CONFIG_FILENAME=./gitchangelog.rc.reference "$gitchangelog" > CHANGELOG.rst

if [ "$?" != 0 ]; then
    (echo -n "Changelog NOT generated. "
     echo "An error occured while running \`\`gitchangelog\`\`." )>&2
else
    echo "Changelog generated."
fi

set_version_setup_py
if [ "$?" != 0 ]; then
    print_error "Error while updating version information."
fi

