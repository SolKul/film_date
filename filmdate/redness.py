import numpy as np
import cv2


def extract_reder(img_ar, h_lower_thre=350, h_upper_thre=45):
    # hsvに変換する
    # np.float32なので、hは0から360になる
    im_hsv = cv2.cvtColor(img_ar.astype(np.float32), cv2.COLOR_BGR2HSV)
    # hだけ抜き出す
    im_h = im_hsv[:, :, 0]
    redness_ar = np.zeros_like(im_h, dtype=np.uint8)
    date_area = (h_lower_thre <= im_h) | (im_h < h_upper_thre)
    redness_ar[date_area] = 255
    return redness_ar


class RednessCalculatorOld:
    def __init__(
        self,
        img_ar,
        scan_size: int = 51,
        scan_exclude_size: int = 15,
        h_dis_lower_threshold=-0.1,
        h_dis_upper_threshold=0.15,
        red_frequency_threshold=0.01,
    ):
        # 高さと幅を記録
        im_hight, im_width = img_ar.shape[:2]

        # hsvに変換する
        # np.float32なので、hは0から360になる
        im_hsv = cv2.cvtColor(img_ar.astype(np.float32), cv2.COLOR_BGR2HSV)
        # hだけ抜き出す
        self.im_h = im_hsv[:, :, 0]

        # 赤さを計算するためのマスク
        self.scan_mask = np.ones([scan_size, scan_size], dtype=bool)

        self.scan_size_half = int((scan_size - 1) / 2)
        scan_exc_half = int((scan_exclude_size - 1) / 2)

        idx_start_exclude = self.scan_size_half - scan_exc_half
        idx_end_exclude = self.scan_size_half + scan_exc_half + 1

        self.scan_mask[idx_start_exclude:idx_end_exclude, idx_start_exclude:idx_end_exclude] = False

        # rednessの計算ができる範囲を求める
        self.idx_start_scan_vertical = self.scan_size_half
        self.idx_end_scan_vertical = im_hight - self.scan_size_half

        self.idx_start_scan_horizontal = self.scan_size_half
        self.idx_end_scan_horizontal = im_width - self.scan_size_half

        # rednessを記録する配列を用意
        self.redness_ar = np.zeros([im_hight, im_width], dtype=float)
        self.redness_bin = np.zeros([im_hight, im_width], dtype=np.uint8)

        self.h_red = 360
        self.h_dis_lower_threshold = h_dis_lower_threshold
        self.h_dis_upper_threshold = h_dis_upper_threshold
        self.red_frequency_threshold = red_frequency_threshold

    def calc_redness(self, idx_vertical, idx_horizontal):
        # 対象のHを取り出す
        h_tg = self.im_h[idx_vertical, idx_horizontal]
        h_tg_360 = h_tg.copy()
        if h_tg < 180:
            h_tg_360 = h_tg + 360

        # 周辺のHを取り出す
        idx_vertical_start = idx_vertical - self.scan_size_half
        idx_vertical_end = idx_vertical + self.scan_size_half
        #         print("vertical")
        #         print(idx_vertical_start,idx_vertical_end)

        idx_horizontal_start = idx_horizontal - self.scan_size_half
        idx_horizontal_end = idx_horizontal + self.scan_size_half
        #         print("horizontal")
        #         print(idx_horizontal_start,idx_horizontal_end)

        h_scan_area = self.im_h[
            idx_vertical_start : idx_vertical_end + 1, idx_horizontal_start : idx_horizontal_end + 1
        ]
        h_scan = h_scan_area[self.scan_mask]

        h_scan_360 = h_scan.copy()
        h_scan_360[h_scan < 180] = h_scan_360[h_scan < 180] + 360

        h_scan_tg = h_scan_360[h_scan_360 != self.h_red]

        redness_distance = (h_tg_360 - self.h_red) / (h_scan_tg - self.h_red)
        redness = (
            (self.h_dis_lower_threshold <= redness_distance)
            & (redness_distance < self.h_dis_upper_threshold)
        ).sum() / len(redness_distance)
        return redness

    def scan_redness(self):
        for idx_vertical in range(self.idx_start_scan_vertical, self.idx_end_scan_vertical):
            for idx_horizontal in range(
                self.idx_start_scan_horizontal, self.idx_end_scan_horizontal
            ):
                redness = self.calc_redness(idx_vertical, idx_horizontal)
                self.redness_ar[idx_vertical, idx_horizontal] = redness
        self.redness_bin[self.redness_ar > self.red_frequency_threshold] = 255

        return self.redness_bin


def binarize_date(image, h_lower_thre=350, h_upper_thre=45):
    redness_bin = extract_reder(image, h_lower_thre=h_lower_thre, h_upper_thre=h_upper_thre)
    # 城に囲まれた内部の黒を塗りつぶすクロージング処理
    kernel = np.ones((3, 3), np.uint8)
    redness_closed = cv2.morphologyEx(redness_bin, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 黒の中に孤立している白い点を消すオープニング処理
    kernel = np.ones((3, 3), np.uint8)
    date_neighbor = cv2.morphologyEx(redness_closed, cv2.MORPH_OPEN, kernel, iterations=1)
    return date_neighbor
