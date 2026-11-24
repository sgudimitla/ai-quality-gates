"""Quality gate summary: separates real FAILURES from INCONCLUSIVE infra errors."""
MAX_INCONCLUSIVE_SHARE = 0.2  # more than 20% untested -> the run can't be trusted


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    stats = reporter.stats
    inconclusive = [r for r in stats.get("skipped", []) if "INCONCLUSIVE" in str(r.longrepr)]
    failed = stats.get("failed", [])
    total = session.testscollected or 1

    print("\n===== AI QUALITY GATE =====")
    print(f"passed: {len(stats.get('passed', []))}  quality failures: {len(failed)}  "
          f"known issues: {len(stats.get('xfailed', [])) + len(stats.get('xpassed', []))}  "
          f"inconclusive (infra): {len(inconclusive)}")
    if failed:
        print("RESULT: BLOCKED - real quality failures")
    elif len(inconclusive) / total > MAX_INCONCLUSIVE_SHARE:
        print("RESULT: INCONCLUSIVE - too many API errors to trust this run. Re-run later.")
        session.exitstatus = 1
    else:
        print("RESULT: PASSED")