"""Check route geometry and pause behavior with no MAVLink or real waiting."""

import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autonomous_flight_Py"))

import route_tracking


class RouteTests(unittest.TestCase):
    def run_route(self, event):
        vehicle = object()
        barrier = Mock()
        send_position = Mock()
        with patch.object(route_tracking.time, "sleep") as sleep:
            with contextlib.redirect_stdout(io.StringIO()):
                route_tracking.infinity_flight(
                    barrier, event, vehicle, 15, send_position
                )
        barrier.wait.assert_called_once_with()
        return vehicle, send_position.call_args_list, sleep

    def test_route_closes_and_preserves_altitude(self):
        event = Mock()
        event.is_set.return_value = False
        vehicle, calls, _ = self.run_route(event)
        self.assertEqual(len(calls), route_tracking.N_SAMPLES)
        self.assertTrue(all(call.args[0] is vehicle for call in calls))
        points = np.array([call.args[1:] for call in calls])
        np.testing.assert_allclose(points[0], [0.0, 0.0, -15.0], atol=1e-9)
        np.testing.assert_allclose(points[-1], points[0], atol=1e-9)
        np.testing.assert_allclose(points[:, 2], -15.0)
        # Current 90-degree route should span twice each ellipse semi-axis.
        self.assertAlmostEqual(np.ptp(points[:, 0]), 130.0, delta=0.01)
        self.assertAlmostEqual(np.ptp(points[:, 1]), 260.0, delta=0.01)

    def test_pause_finishes_before_the_next_position_is_sent(self):
        event = Mock()
        event.is_set.side_effect = [True, True, False] + [False] * (
            route_tracking.N_SAMPLES - 1
        )
        barrier = Mock()
        send_position = Mock()

        def check_pause(delay):
            if delay == route_tracking.EVENT_CHECK_INTERVAL and not send_position.called:
                event.is_set.assert_called()
                self.assertEqual(event.is_set.call_count, 2)

        with patch.object(route_tracking.time, "sleep", side_effect=check_pause) as sleep:
            with contextlib.redirect_stdout(io.StringIO()):
                route_tracking.infinity_flight(
                    barrier, event, object(), 15, send_position
                )

        self.assertEqual(send_position.call_count, route_tracking.N_SAMPLES)
        self.assertEqual(event.is_set.call_count, route_tracking.N_SAMPLES + 2)
        self.assertEqual(sleep.call_args_list[0].args, (route_tracking.EVENT_CHECK_INTERVAL,))
        self.assertEqual(sleep.call_args_list[-1].args, (10,))


if __name__ == "__main__":
    unittest.main()
