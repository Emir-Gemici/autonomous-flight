"""Exercise image analysis with synthetic frames; never open a camera or vehicle."""

import contextlib
import io
from pathlib import Path
import sys
from threading import Event
import unittest

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autonomous_flight_Py"))

from main import image_process
from target_detection import _process_search_mode


class ColorMaskTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.rectangle(self.frame, (30, 50), (90, 110), (255, 0, 0), -1)
        cv2.rectangle(self.frame, (180, 50), (240, 110), (0, 0, 255), -1)

    def test_search_mask_keeps_red_and_blue(self):
        self.assertEqual(len(image_process(self.frame, 0)), 2)

    def test_selected_color_keeps_only_the_matching_region(self):
        for flag, expected_center in ((1, 60), (2, 210)):
            with self.subTest(flag=flag):
                contours = image_process(self.frame, flag)
                self.assertEqual(len(contours), 1)
                moments = cv2.moments(contours[0])
                self.assertAlmostEqual(moments["m10"] / moments["m00"], expected_center)

    def test_red_mask_covers_both_ends_of_hue_range(self):
        for hue in (5, 170):
            with self.subTest(hue=hue):
                hsv = np.zeros((80, 80, 3), dtype=np.uint8)
                hsv[20:60, 20:60] = (hue, 255, 255)
                frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                self.assertEqual(len(image_process(frame, 2)), 1)

    def test_small_contours_are_removed(self):
        frame = np.zeros((80, 80, 3), dtype=np.uint8)
        cv2.rectangle(frame, (10, 10), (15, 15), (255, 0, 0), -1)
        self.assertEqual(len(image_process(frame, 0)), 0)

    def test_unrelated_color_is_rejected(self):
        frame = np.full((80, 80, 3), (0, 255, 0), dtype=np.uint8)
        self.assertEqual(len(image_process(frame, 0)), 0)

    def test_empty_frame_and_unknown_flag_produce_no_contours(self):
        self.assertEqual(len(image_process(np.zeros_like(self.frame), 0)), 0)
        self.assertEqual(len(image_process(self.frame, 99)), 0)


class ShapeSearchTests(unittest.TestCase):
    resolution = (1280, 720)
    border = 128

    @staticmethod
    def contour(points):
        return np.array(points, dtype=np.int32).reshape((-1, 1, 2))

    def search(self, contours, flag=0):
        event = Event()
        with contextlib.redirect_stdout(io.StringIO()):
            result = _process_search_mode(
                contours, flag, event, self.resolution, self.border
            )
        return result, event.is_set()

    def test_centered_hexagon_selects_blue_mode(self):
        hexagon = self.contour(
            [(690, 360), (665, 403), (615, 403),
             (590, 360), (615, 317), (665, 317)]
        )
        self.assertEqual(self.search([hexagon]), (1, True))

    def test_centered_triangle_selects_red_mode(self):
        triangle = self.contour([(640, 300), (580, 400), (700, 400)])
        self.assertEqual(self.search([triangle]), (2, True))

    def test_border_target_does_not_pause_route(self):
        triangle = self.contour([(40, 300), (10, 400), (70, 400)])
        self.assertEqual(self.search([triangle]), (0, False))

    def test_degenerate_contour_does_not_pause_route(self):
        line = self.contour([(600, 360), (640, 360), (680, 360)])
        self.assertEqual(self.search([line]), (0, False))

    def test_other_shape_and_empty_input_do_not_pause_route(self):
        square = self.contour([(600, 320), (680, 320), (680, 400), (600, 400)])
        self.assertEqual(self.search([square]), (0, False))
        self.assertEqual(self.search([]), (0, False))

    def test_blue_mode_ignores_a_triangle(self):
        triangle = self.contour([(640, 300), (580, 400), (700, 400)])
        self.assertEqual(self.search([triangle], flag=1), (1, False))


if __name__ == "__main__":
    unittest.main()
