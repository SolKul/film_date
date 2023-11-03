import numpy as np
import cv2
from dataclasses import dataclass


class DotPositioner:
    def __init__(self, date_neighbor, dot_vertical_start=144, dot_horizontal_start=108):
        self.date_neighbor = date_neighbor
        self.date_neighbor_color = np.tile(date_neighbor[:, :, np.newaxis], (1, 1, 3))
        self.dot_vertical_start = dot_vertical_start
        self.dot_horizontal_start = dot_horizontal_start
        self.lenght_side = 13
        self.area_size = self.lenght_side**2

    def calc_dot_area(self, shift_v, shift_h):
        dot_ext_v_start = self.dot_vertical_start + shift_v
        dot_ext_h_start = self.dot_horizontal_start + shift_h
        return dot_ext_v_start, dot_ext_h_start

    def rect_dot(self, shift_v, shift_h):
        dot_ext_v_start, dot_ext_h_start = self.calc_dot_area(shift_v, shift_h)

        date_neighbor_rected = cv2.rectangle(
            self.date_neighbor_color,
            (dot_ext_h_start, dot_ext_v_start),
            (
                dot_ext_h_start + self.lenght_side,
                dot_ext_v_start + self.lenght_side,
            ),
            (255, 0, 0),
        )
        return date_neighbor_rected

    def ext_dot_area(self, shift_v, shift_h):
        dot_ext_v_start, dot_ext_h_start = self.calc_dot_area(shift_v, shift_h)
        dot_ext = self.date_neighbor[
            dot_ext_v_start : dot_ext_v_start + self.lenght_side,
            dot_ext_h_start : dot_ext_h_start + self.lenght_side,
        ]
        return dot_ext

    def count_dot_area(self):
        shift_ratio_map = {}
        for shift_v in range(-1, 2):
            for shift_h in range(-1, 2):
                shift_key = (shift_v, shift_h)
                dot_ext = self.ext_dot_area(shift_v, shift_h)
                dot_ratio = (dot_ext > 127).sum() / self.area_size
                shift_ratio_map[shift_key] = dot_ratio
        return shift_ratio_map

    def calc_shift_max_ratio(self):
        shift_ratio_map = self.count_dot_area()
        shift_arg_max, ratio_max = max(shift_ratio_map.items(), key=lambda x: x[1])
        if shift_ratio_map[(0, 0)] == ratio_max:
            return 0, 0
        else:
            return shift_arg_max

    def calc_dot_left_upper(self):
        shift_v, shift_h = self.calc_shift_max_ratio()
        return self.dot_vertical_start + shift_v, self.dot_horizontal_start + shift_h


class DigitsImageExtractor:
    def __init__(self, date_neighbor, dot_vertical_start=144, dot_horizontal_start=108):
        self.date_neighbor = date_neighbor
        self.date_neighbor_color = np.tile(date_neighbor[:, :, np.newaxis], (1, 1, 3))
        self.dot_vertical_start = dot_vertical_start
        self.dot_horizontal_start = dot_horizontal_start
        self.length_v_surrounding = 52
        self.length_h_surrounding = 35
        self.digit_height = 51
        self.digit_width = 32

    def calc_digit_surrounding(self, no_digit=1):
        surrounding_v_start = self.dot_vertical_start
        surrounding_h_start = self.dot_horizontal_start + 18
        return surrounding_v_start, surrounding_h_start

    def rect_surrounding(self, no_digit=1):
        surrounding_v_start, surrounding_h_start = self.calc_digit_surrounding(no_digit)
        date_neighbor_rected = cv2.rectangle(
            self.date_neighbor_color,
            (surrounding_h_start, surrounding_v_start),
            (
                surrounding_h_start + self.length_h_surrounding,
                surrounding_v_start + self.length_v_surrounding,
            ),
            (255, 0, 0),
        )
        return date_neighbor_rected

    def ext_surrounding(self, no_digit=1):
        surrounding_v_start, surrounding_h_start = self.calc_digit_surrounding(no_digit)
        surrounding_ext = self.date_neighbor[
            surrounding_v_start : surrounding_v_start + self.length_v_surrounding,
            surrounding_h_start : surrounding_h_start + self.length_h_surrounding,
        ]
        return surrounding_ext

    def ext_bouding(self, surrounding_ext):
        # 縦方向で、どこからどこまでか
        digit_hight_check = np.any(surrounding_ext, axis=1)
        if digit_hight_check[0]:
            digit_vertical_start = 0
        else:
            digit_vertical_start = 1
        if digit_hight_check[-1]:
            digit_vertical_end = self.length_v_surrounding
        else:
            digit_vertical_end = self.length_v_surrounding - 1

        # 横方向でどこからどこまでか
        digit_width_check = np.any(surrounding_ext, axis=0)
        if digit_width_check[0]:
            digit_horizontal_start = 0
        else:
            digit_horizontal_start = 1
        if digit_width_check[-1]:
            digit_horizontal_end = self.length_h_surrounding
        else:
            digit_horizontal_end = self.length_h_surrounding - 1

        return (
            digit_vertical_start,
            digit_vertical_end,
            digit_horizontal_start,
            digit_horizontal_end,
        )

    def ext_just_surrounding(self, no_digit=1):
        surrounding_ext = self.ext_surrounding(no_digit)
        (
            digit_vertical_start,
            digit_vertical_end,
            digit_horizontal_start,
            digit_horizontal_end,
        ) = self.ext_bouding(surrounding_ext)
        just_srd_ext = surrounding_ext[
            digit_vertical_start:digit_vertical_end, digit_horizontal_start:digit_horizontal_end
        ]
        return just_srd_ext

    def ext_digit_image(self, no_digit=1):
        just_srd_ext = self.ext_just_surrounding(no_digit)
        just_srd_ext_resized = cv2.resize(
            just_srd_ext, (self.digit_width, self.digit_height), interpolation=cv2.INTER_LINEAR
        )
        return just_srd_ext_resized


@dataclass
class SegArea:
    vertical_start: int
    vertical_end: int
    horizontal_start: int
    horizontal_end: int


SEVEN_SEG_AREAS = {
    "A": SegArea(0, 10, 4, 28),
    "B": SegArea(5, 23, 22, 32),
    "C": SegArea(28, 46, 22, 32),
    "D": SegArea(41, 51, 4, 28),
    "E": SegArea(28, 46, 0, 10),
    "F": SegArea(5, 23, 0, 10),
    "G": SegArea(20, 30, 4, 28),
}

SEVEN_SEG_DIGIT_MAP = {63: 0, 111: 9}


class SevenSegRecognizer:
    def __init__(self, seven_seg_im, ratio_threshold=0.43):
        self.seven_seg_im = seven_seg_im
        self.seven_seg_im_rect = np.tile(seven_seg_im[:, :, np.newaxis], (1, 1, 3))
        self.ratio_threshold = ratio_threshold

    def extract_seg(self, seg):
        area = SEVEN_SEG_AREAS[seg]
        seg_im = self.seven_seg_im[
            area.vertical_start : area.vertical_end, area.horizontal_start : area.horizontal_end
        ]
        return seg_im

    def judge_seg(self, seg):
        seg_im = self.extract_seg(seg)
        seg_ratio = seg_im.mean() / 255
        return seg_ratio > self.ratio_threshold

    def rect_seg(self, seg):
        area = SEVEN_SEG_AREAS[seg]
        seg_rected = cv2.rectangle(
            self.seven_seg_im_rect,
            (area.horizontal_start, area.vertical_start),
            (
                area.horizontal_end,
                area.vertical_end,
            ),
            (255, 0, 0),
        )
        return seg_rected

    def count_seg_on(self):
        segs_name = ["A", "B", "C", "D", "E", "F", "G"]
        binary_place = 1
        bin_digit_key = 0
        for seg in segs_name:
            if self.judge_seg(seg):
                bin_digit_key = bin_digit_key + binary_place
            binary_place = binary_place * 2

        return bin_digit_key

    def recoginize_digit(self):
        bin_digit_key = self.count_seg_on()
        if bin_digit_key in SEVEN_SEG_DIGIT_MAP:
            return SEVEN_SEG_DIGIT_MAP[bin_digit_key]
        else:
            return -1
