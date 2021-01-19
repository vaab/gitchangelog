# Change Generator
This script will generate a changelog from the git commits.
It will map the commits to jira tickets if possible from the commit message, or searching the PR description.

**NOTE: This is a pre-alpha implementation. Some things might not work as expected.**

Script uses GitHub and Jira API, which might reach the limit in case of long changelog.

## Configuration
You need to create:
* [Github Access Token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) with api access level.
* [Jira Access Token](https://confluence.atlassian.com/cloud/api-tokens-938839638.html) with access to the project.

```
# install the requirements
pip3 install -r requirements.txt
```

## How to use it
The script requires access to GitHub and Jira. Also the current directory needs to be the project.

```
 python3 generate_changelog.py \
     --title "App Changelog" \
     --start-tag "1.2.0" \
     --end-tag "1.2.1" \
     --jira-project "KLTB002" \
     --jira-username "mihai.georgescu@kolibree.com" \
     --jira-server "https://kolibree.atlassian.net/" \
     --repository "kolibree-git/iOS-monorepo"
```

`jira-access-token` and `github-access-token` can be passed as parameter. In case they are missing, a secure prompt will be presented to the user.

## Enhancements ideas
* Check for Jira ticket status to be Done or Closed. Do not add QA Stories.
* Use GitHub for the history instead of local git.
* Create changelog between multiple tags.
* Solve the API limit for GitHub. I didn't identified a way to specify the pull request numbers as a query, but we should make sure the request limit is not reached.
* Solve the API limit for Jira. Maybe make a search for the tickets instead of fetching them one by one.
* Make a configuration file instead of passing all the parameters.
* Migrate to OAuth for Jira instead of personal access token.