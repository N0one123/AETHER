# AETHER

The Health page's default monitoring rule set is defined by
`DEFAULT_MONITORING_RULES` in `app/cores/health.py`. Adjust its measurement
boundaries, severities, and descriptions to match the mission's medical
protocols. Enabling defaults activates the rules and normal Health Core alert
processing; disabling them removes only rules still managed by defaults and
restores any custom rules they replaced.