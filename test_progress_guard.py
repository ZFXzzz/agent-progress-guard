import unittest

from progress_guard import Decision, Observation, ProgressGuard


class ProgressGuardTests(unittest.TestCase):
    def guard(self, *, task_timeout=20):
        return ProgressGuard(now=100, no_progress_timeout=5, task_timeout=task_timeout)

    def test_empty_results_keep_consuming_the_stall_budget(self):
        guard = self.guard()
        self.assertIs(guard.update(102, Observation.EMPTY_RESULT), Decision.CONTINUE)
        self.assertIs(guard.update(104, Observation.EMPTY_RESULT), Decision.CONTINUE)
        self.assertIs(guard.update(105), Decision.NO_PROGRESS)

    def test_outage_pauses_budget_and_empty_result_resumes_it(self):
        guard = self.guard()
        self.assertIs(guard.update(102, Observation.DEPENDENCY_UNAVAILABLE), Decision.CONTINUE)
        self.assertIs(guard.update(107, Observation.DEPENDENCY_UNAVAILABLE), Decision.CONTINUE)
        self.assertIs(guard.update(110, Observation.EMPTY_RESULT), Decision.CONTINUE)
        self.assertIs(guard.update(112), Decision.CONTINUE)
        self.assertIs(guard.update(113), Decision.NO_PROGRESS)

    def test_meaningful_progress_resets_budget_after_outage(self):
        guard = self.guard()
        self.assertIs(guard.update(104, Observation.DEPENDENCY_UNAVAILABLE), Decision.CONTINUE)
        self.assertIs(guard.update(109, Observation.PROGRESS), Decision.CONTINUE)
        self.assertIs(guard.update(113), Decision.CONTINUE)
        self.assertIs(guard.update(114), Decision.NO_PROGRESS)

    def test_persistent_outage_does_not_extend_task_deadline(self):
        guard = self.guard(task_timeout=10)
        self.assertIs(guard.update(101, Observation.DEPENDENCY_UNAVAILABLE), Decision.CONTINUE)
        self.assertIs(guard.update(109), Decision.CONTINUE)
        self.assertIs(guard.update(110, Observation.COMPLETE), Decision.DEADLINE_EXCEEDED)

    def test_late_progress_cannot_resurrect_a_stalled_task(self):
        guard = self.guard()
        self.assertIs(guard.update(105, Observation.PROGRESS), Decision.NO_PROGRESS)
        self.assertIs(guard.update(106, Observation.COMPLETE), Decision.NO_PROGRESS)

    def test_deadline_takes_precedence_when_both_timers_expire_at_a_tick(self):
        guard = self.guard(task_timeout=5)
        self.assertIs(guard.update(105), Decision.DEADLINE_EXCEEDED)

    def test_completed_task_keeps_its_terminal_decision(self):
        guard = self.guard()
        self.assertIs(guard.update(101, Observation.COMPLETE), Decision.COMPLETE)
        self.assertIs(guard.update(121), Decision.COMPLETE)

    def test_invalid_timestamp_does_not_mutate_state(self):
        guard = self.guard()
        self.assertIs(guard.update(102), Decision.CONTINUE)
        for timestamp in (101, float("nan"), float("inf")):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                guard.update(timestamp, Observation.DEPENDENCY_UNAVAILABLE)
        self.assertIs(guard.update(105), Decision.NO_PROGRESS)


if __name__ == "__main__":
    unittest.main()
