"""
manual_inputで判別したファイルごとの日付について、
フォルダをまたいで、日付を最適化する。
具体的には2つのフォルダ中のファイルの日付が同じ場合、
どちらのフォルダが後かを判定し、時間を設定する
"""
from dataclasses import dataclass
from pathlib import Path
import datetime as dt
import pandas as pd

from . import common_dataclass


class FolderFileDatetimeCalculator:
    def calc_datetime_folder(
        self, folder_date_repr_list: list[common_dataclass.FolderDateRepresentative]
    ):
        # フォルダ内の日付が設定されたファイルについて、
        # フォルダをまたいで日付を最適化する

        # 代表日時に基づいてフォルダをソートする
        folder_date_repr_sorted = sorted(folder_date_repr_list)

        # ソート後に撮影日時を決定することで、
        # 撮影日時が重複しないようになる
        num_file = len(folder_date_repr_sorted)
        self.datetime_original_prev = None
        folder_date_orig_list = []
        for i in range(num_file):
            folder_date_repr = folder_date_repr_sorted[i]
            file_date_list = folder_date_repr.file_date_list
            # FileDateのリストそれぞれについて、撮影日時を決定する
            file_datetime_orig_list = self.calc_datetime_file_list(file_date_list)
            folder_date_orig_list.append(
                common_dataclass.FolderDatetimeOriginal(
                    folder_date_repr=folder_date_repr, file_date_orig_list=file_datetime_orig_list
                )
            )
        return folder_date_orig_list

    def calc_datetime_file_list(self, file_date_list: list[common_dataclass.FileDate]):
        num_file = len(file_date_list)
        file_datetime_orig_list = []
        for i in range(num_file):
            file_date = file_date_list[i]
            date_tmp_day = file_date.date.floor("D")
            datetime_original = self.decide_datetime_original(date_tmp_day)
            file_datetime = common_dataclass.FileDatetimeOriginal(file_date, datetime_original)
            file_datetime_orig_list.append(file_datetime)
        return file_datetime_orig_list

    def decide_datetime_original(self, day_inputed: pd.Timestamp) -> pd.Timestamp:
        """撮影日時を決定する"""
        if self.datetime_original_prev is None:
            # self.datetime_original_prevが設定されていなければ
            # day_inputedの12:00を撮影日時とする
            time_to_set = dt.time(12, 0)
            datetime_original: pd.Timestamp = pd.Timestamp.combine(day_inputed, time_to_set)
            self.datetime_original_prev = datetime_original
        else:
            # self.datetime_original_prevが設定されていれば
            day_prev = self.datetime_original_prev.floor("D")
            if day_inputed == day_prev:
                # day_inputedが
                # self.datetime_original_prevの日付と同日なら、
                # self.datetime_original_prevの1分後を撮影日時とする
                datetime_original = self.datetime_original_prev + pd.Timedelta(minutes=1)
                self.datetime_original_prev = datetime_original
            else:
                # day_inputedが
                # self.datetime_original_prevの日付と同日でないなら、
                # day_inputedの12:00を撮影日時とする
                time_to_set = dt.time(12, 0)
                datetime_original: pd.Timestamp = pd.Timestamp.combine(day_inputed, time_to_set)
                self.datetime_original_prev = datetime_original
        return datetime_original
