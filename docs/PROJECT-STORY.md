# Project walkthrough

A short explanation for an interview. The wording describes the completed lab work and the role of AI assistance without claiming independent authorship of every script or design choice.

## About two minutes

I built a small Zabbix monitoring lab with two Ubuntu virtual machines. One runs the monitoring server, and the other is the host I monitor. I collect CPU, memory and disk metrics, check an HTTP health page, and show the main results on a dashboard.

I used an AI coding agent to help plan the work, troubleshoot problems, and prepare scripts and documentation. I did the manual VM setup, guest configuration and fault tests. It was a learning project with AI support, and it gave me practical experience with the tools.

I wanted to check how the monitoring would react when something went wrong. I stopped Nginx, shut down the target VM, created a controlled CPU load, and changed the content of the health page. That last test showed why checking HTTP 200 alone is not enough: the page can respond successfully and still return the wrong content.

I also used a small Python queue simulator prepared with the agent. It let me test a worker that stopped processing jobs, a growing queue, and a metrics file that stopped updating.

During a restart test, an unexpected worker warning appeared. We changed the heartbeat-age calculation to use timestamps from the same JSON sample. I repeated the restart test and then paused the worker again. In those tests, the extra restart warning disappeared, and the real worker problem was still detected.

The GitHub repository includes screenshots, observed timings, runbooks and configuration exports. The main fault tests are complete, but I have not tested importing the exports into a fresh Zabbix instance.

## If asked about AI assistance

The agent helped with planning, scripts, troubleshooting and documentation. I applied the settings and ran the manual lab tests. I would not claim that I wrote every line myself. The value for me was getting hands-on practice and working through the results, rather than just having a finished repository.

## Two useful results to mention

- In one Nginx stop test, Zabbix detected the problem about 24 seconds after the stop reference and recognized recovery about 7 seconds after the restart reference.
- In the worker-pause test after the correction, detection took about 36 seconds and recovery about 1 second relative to the recorded action timestamps.

These are observations from individual tests, not guaranteed timings. See [Validation](VALIDATION.md) for the evidence and measurement limits.
