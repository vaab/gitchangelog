{{#general_title}}
# {{{title}}}


{{/general_title}}
{{#versions}}
## {{{label}}}

{{#sections}}
### {{{label}}}

{{#commits}}
* {{{subject}}} [{{{author}}}] [{{commit.sha1}}]({{project_commit_url}}{{commit.sha1}})
{{#body}}

{{{body_indented}}}
{{/body}}

{{/commits}}
{{/sections}}

{{/versions}}
