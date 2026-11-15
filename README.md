# AETHER

The Health page's default monitoring rule set is defined by
`DEFAULT_MONITORING_RULES` in `app/cores/health.py`. Adjust its measurement
boundaries, severities, and descriptions to match the mission's medical
protocols. Enabling defaults activates the rules and normal Health Core alert
processing; disabling them removes only rules still managed by defaults and
restores any custom rules they replaced.

The Tracking page reads non-simulated Health records and simulated records
explicitly tagged with `source="sim_lab"` from `health_measurements`. It shows
real Health and Sim Lab data in separate astronaut timelines and calculates
separate timestamp-based linear projections for each measurement series after
three or more points. Forecasts use a fixed 24-hour requested horizon and are
capped at one observed series span beyond the latest sample to avoid extreme
extrapolations from short-term measurement changes. They are numeric
projections, not diagnoses or alerts.
Future Sim Lab integrations should set both `simulated=1` and
`source="sim_lab"`.