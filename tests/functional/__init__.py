"""The REST endpoint, over HTTP (functional layer)."""

#: Users created for the permission tests, by role.
USERS = {
    "Site Administrator": ("siteadmin", "siteadmin-password"),
    "Editor": ("editor", "editor-password"),
    "Member": ("member", "member-password"),
}

#: The keys a status response carries, at the top level.
STATUS_KEYS = ["active", "breaker", "functions", "server", "settings"]
