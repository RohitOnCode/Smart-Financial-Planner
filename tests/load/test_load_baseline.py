import time
import pytest

@pytest.mark.benchmark(group="planner")
def test_fake_planner_load(benchmark):
    # Replace this with a real call chain to your planner once available.
    def plan_once():
        # Simulate light compute to catch regressions in latency.
        s = 0
        for i in range(10000):
            s += i*i
        return s

    result = benchmark(plan_once)
    assert result >= 0