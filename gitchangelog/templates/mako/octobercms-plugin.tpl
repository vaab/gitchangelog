<%
import re
def quote(txt):
    if re.search(r"[\"`\[\]-]", txt):
        return "\"%s\"" % txt.replace('"', '\\"')
    return txt
%>
% for version in data["versions"]:
${version["tag"] or quote(opts["unreleased_version_label"])}:
% for section in version["sections"]:
% for commit in section["commits"]:
  - ${quote(commit["subject"])}
% endfor
% endfor
% endfor
