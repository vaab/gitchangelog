#!/usr/bin/env ruby

require 'active_support/core_ext/string/output_safety'

def verifyPRTitle(jiraDomainUrl, jiraProjectKey)
    title = github.pr_title

    # 
    # Shortest acceptable title contains Jira key in brackets, 
    # a space and at least one char. For example:
    # 
    # `[jiraProjectKey-1] A`
    # 
    minTitleLength = jiraProjectKey.size + 6

    if title.size < minTitleLength
        warn("Title too short. It should fit '[#{jiraProjectKey}-JIRA_TICKET_NO] TITLE' template.")
        return
    end

    unless title =~ /\[#{jiraProjectKey}-[0-9]+\]\s\S+/
        warn "Invalid PR title. It should fit `[#{jiraProjectKey}-JIRA_TICKET_NO] TITLE` template"
        return
    end

    sanitizedTitle = title
    sanitizedTitle.slice! "[#{jiraProjectKey}-"
    indexOfClosingBracket = sanitizedTitle.index(']')

    if indexOfClosingBracket.nil? || indexOfClosingBracket == 0
        # As we're testing regexp before, this should not happen, but let's be sure
        warn "Invalid PR title. It should fit `[#{jiraProjectKey}-JIRA_TICKET_NO] TITLE` template"
        return
    end

    jiraTicketNumber = sanitizedTitle[0..indexOfClosingBracket-1]
    jiraTicketBaseString = "#{jiraDomainUrl}/browse/#{jiraProjectKey}-#{jiraTicketNumber}"
    jiraTicket = jiraTicketBaseString.gsub(URI.regexp, '<a href="\0">\0</a>').html_safe
    message "This PR is related to JIRA " + jiraTicket

    description = github.pr_body
    warn "JIRA link in the description does not match pull request title." unless description.include?(jiraTicketBaseString)
end

ENV_JIRA_DOMAIN_URL = "DANGER_JIRA_DOMAIN_URL"
ENV_JIRA_PROJECT_KEY = "DANGER_JIRA_PROJECT_KEY"

jiraDomainUrl = ENV[ENV_JIRA_DOMAIN_URL]
jiraProjectKey = ENV[ENV_JIRA_PROJECT_KEY]

fail "Jira domain URL has to be passed via `#{ENV_JIRA_DOMAIN_URL}` env variable. Check your configuration." if jiraDomainUrl.nil? or jiraDomainUrl.empty?
fail "Jira project key has to be passed via `#{ENV_JIRA_PROJECT_KEY}` env variable. Check your configuration." if jiraProjectKey.nil? or jiraProjectKey.empty?
fail "Jira domain URL (#{jiraDomainUrl}) cannot be blank" if jiraDomainUrl.nil?.! and jiraDomainUrl.empty?
fail "Jira project key (#{jiraProjectKey}) cannot be blank" if jiraProjectKey.nil?.! and jiraProjectKey.empty?

verifyPRTitle(jiraDomainUrl, jiraProjectKey) unless jiraDomainUrl.nil? or jiraProjectKey.nil? or jiraDomainUrl.empty? or jiraProjectKey.empty?
