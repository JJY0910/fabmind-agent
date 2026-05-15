# Acceptance Checklist

## Foundation

- [ ] canonical folder structure only
- [ ] README run instructions verified
- [ ] Docker Compose starts PostgreSQL, Redis, MinIO
- [ ] API health endpoint returns 200
- [ ] Web app renders

## Data

- [ ] 30+ alarm codes
- [ ] 60+ I/O points
- [ ] 20+ scenarios
- [ ] all scenarios reference existing alarms/evidence
- [ ] deterministic seed

## Agent

- [ ] Scenario A returns sensor misalignment top cause
- [ ] Scenario B returns EtherCAT config/link issue top cause
- [ ] Scenario C blocks risky action
- [ ] insufficient evidence state works
- [ ] every hypothesis has evidence_ids

## UI

- [ ] Dashboard
- [ ] Equipment detail
- [ ] New diagnosis
- [ ] Agent analysis
- [ ] Evidence drawer
- [ ] Checklist runner
- [ ] Report builder
- [ ] Approval queue
- [ ] Audit console

## GitHub

- [ ] CI green
- [ ] PR template exists
- [ ] screenshots added
- [ ] demo script added
- [ ] no real confidential data
