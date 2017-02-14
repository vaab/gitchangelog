% for version in data["versions"]:
% if version["tag"]:
${version["date"]}  Release

	* ${version["tag"] or opts["unreleased_version_label"]} released.
%endif

% for section in version["sections"]:
% for commit in section["commits"]:


--------------------------------------------------
${version["date"]}  Release

	<%
title = "%s (%s)" % (version["tag"], version["date"]) if version["tag"] else opts["unreleased_version_label"]

%>${title}
${"-" * len(title)}

% for section in version["sections"]:
% if not (section["label"] == "Other" and nb_sections == 1):
${section["label"]}
${"~" * len(section["label"])}

% endif
% for commit in section["commits"]:
<%
subject = "%s [%s]" % (commit["subject"], commit["author"])
entry = indent('\n'.join(textwrap.wrap(subject)),
                       first="- ").strip()
%>${entry}

% if commit["body"]:
${indent(commit["body"])}

% endif
% endfor
% endfor
% endfor
% endfor
% endfor
