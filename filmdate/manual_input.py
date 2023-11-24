from typing import Union
import datetime as dt
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import cv2
from PIL import Image
import piexif
from IPython.display import clear_output
from . import impro, common_dataclass


def requier_int_input_again(description):
    # intデータについてinputさせ
    # castできない場合は再度inputさせる
    while True:
        try:
            value_txt = input(description)
            value = int(value_txt)
            return value
        except ValueError:
            print(f"{value_txt} cant cast to int, input again")


def record_memo(path_memo, path_dir):
    with open(path_memo, mode="a") as f:
        str_path = str(path_dir)
        f.write(f"{str_path}\n")


class ImageDateQuestioner:
    def __init__(self, path_dir: Path, path_memo: Path, sort_dir: str = "asc"):
        self.path_dir = Path(path_dir)
        path_file_list = list(self.path_dir.glob("*.jpg"))
        # フォルダ内のファイルについてファイル名でソートする
        self.path_file_list_sorted = sorted(path_file_list, key=lambda x: x.name)
        if sort_dir == "desc":
            self.path_file_list_sorted = self.path_file_list_sorted[::-1]
        self.file_date_list: list[common_dataclass.FileDate] = []
        self.path_memo = Path(path_memo)
        if not self.path_memo.exists():
            raise FileNotFoundError(f"{self.path_memo} dosn't exist")

    def ask_date(self) -> pd.Timestamp:
        # 日付を聞く
        year_abbr = requier_int_input_again("year?")
        month = requier_int_input_again("month?")
        day = requier_int_input_again("day?")
        if year_abbr > 50:
            year = 1900 + year_abbr
        else:
            year = 2000 + year_abbr
        date = pd.Timestamp(year, month, day)
        return date

    def ask_loop_date(
        self, path_file: Path, prev_date: Union[None, pd.Timestamp] = None
    ) -> common_dataclass.FileDate:
        # 日付を聞き、確認出来たらファイルパスと日付を格納した
        # dataclassを返す。
        while True:
            if prev_date is None:
                # 前の日が入力されていないなら、単純に日付を聞く
                date = self.ask_date()
                file_date = common_dataclass.FileDate(path_file, date)
            else:
                # 前の日が入力されていたら、日付が前の日と同じか聞く
                str_prev_date = prev_date.strftime("%Y-%m-%d")
                answer = input(f"is {str_prev_date}?")
                if "y" in answer:
                    file_date = common_dataclass.FileDate(path_file, prev_date)
                else:
                    date = self.ask_date()
                    file_date = common_dataclass.FileDate(path_file, date)

            str_date = file_date.date.strftime("%Y-%m-%d")
            answer = input(f"{str_date}, next?")
            if "y" in answer:
                return file_date

    def ask_recognizable(self) -> bool:
        answer = input("recognizable?")
        if "y" in answer:
            return True
        else:
            return False

    def ask_date_and_bfill(self, path_file: Path) -> common_dataclass.FileDate:
        # 判読可能なら、日付を入力し、
        # 後方穴埋めする
        file_date = self.ask_loop_date(path_file, prev_date=None)
        # 今までの判別不可能だったファイルについて、
        # 初めて判別可能だった日付をFileDateの日付に格納する
        for file_date_existing in self.file_date_list:
            file_date_existing.date = file_date.date
        self.bfilled = True
        return file_date

    def ask_yet_recognize(self, path_file: Path) -> Union[pd.Timestamp, None]:
        """今までのファイル一つも日付が判別可能ではなかった場合の処理"""
        # まず日付が判読可能か
        recognizable = self.ask_recognizable()
        # 判読可能なら、日付を入力し、
        # 後方穴埋めする
        if recognizable:
            file_date = self.ask_date_and_bfill(path_file)
        else:
            # 判読不可能なら、FileDateのdateはNoneとする
            file_date = common_dataclass.FileDate(path_file, None)
        self.file_date_list.append(file_date)
        prev_date = file_date.date
        return prev_date

    def ask_file_date_list(self) -> list[common_dataclass.FileDate]:
        prev_date = None
        # 日付について後方穴埋めしたかどうか
        self.bfilled = False
        num_file = len(self.path_file_list_sorted)
        count = 0
        while count < num_file:
            path_file = self.path_file_list_sorted[count]
            print(path_file)
            show_date_im(path_file)
            if not self.bfilled:
                # まだ後方穴埋めしていないなら
                # 判別可能か聞いてfile_dateを取得する
                prev_date = self.ask_yet_recognize(path_file)
                count = count + 1
            else:
                # もし、yを連打しすぎて、
                # 間違った入力をしてしまった場合は一つ戻る
                answer = input(f"back?")
                if "back" in answer:
                    self.file_date_list.pop(-1)
                    count = count - 1
                else:
                    # 後方穴埋め済みなら、
                    # 前の日付を引数として与え、日付を聞く
                    file_date = self.ask_loop_date(path_file, prev_date)
                    self.file_date_list.append(file_date)
                    prev_date = file_date.date
                    count = count + 1
            clear_output(True)

    def gen_folder_date(self):
        file_date_first = self.file_date_list[0]
        file_date_last = self.file_date_list[-1]
        folder_date_repr = common_dataclass.FolderDateRepresentative(
            path_folder=self.path_dir,
            date_first=file_date_first.date.floor("D"),
            date_last=file_date_last.date.floor("D"),
            file_date_list=self.file_date_list,
        )
        return folder_date_repr

    def ask_and_gen_folder_date(self):
        self.file_date_list: list[common_dataclass.FileDate] = []
        self.ask_file_date_list()
        folder_date_repr = self.gen_folder_date()
        record_memo(self.path_memo, self.path_dir)
        return folder_date_repr


def show_date_im(path_file):
    # ファイルパスの画像について、日付部分を表示する
    fig, axes = plt.subplots(2, 2, figsize=(15, 6))
    image = cv2.imread(str(path_file))
    date_im = image[1300:, 1650:]
    impro.imshow(date_im, ax=axes[0, 0])
    axes[0, 0].axis("off")
    date_im_np_reverse = cv2.bitwise_not(date_im)
    impro.imshow(date_im_np_reverse, ax=axes[0, 1])
    axes[0, 1].axis("off")

    image = cv2.rotate(image, cv2.ROTATE_180)
    date_im = image[1300:, 1650:]
    impro.imshow(date_im, ax=axes[1, 0])
    axes[1, 0].axis("off")
    date_im_np_reverse = cv2.bitwise_not(date_im)
    impro.imshow(date_im_np_reverse, ax=axes[1, 1])
    axes[1, 1].axis("off")
    plt.show()


def append_folder_date_list(
    folder_date_list: list[common_dataclass.FolderDateRepresentative],
    folder_date_repr: common_dataclass.FolderDateRepresentative,
):
    """すでにあるFolderDateRepresentativeのリストについて、
    追加したいFolderDateRepresentativeが
    そのリストに既に追加されていないか確認して追加する"""
    folder_date_dict = {}
    len_folder_list = len(folder_date_list)
    for i in range(len_folder_list):
        folder_date_in_list = folder_date_list[i]
        path_folder = folder_date_in_list.path_folder
        folder_date_dict[path_folder] = i

    path_folder_tg = folder_date_repr.path_folder
    if path_folder_tg not in folder_date_dict:
        folder_date_list.append(folder_date_repr)
    else:
        ask_str = f"{path_folder_tg} exists already in folder_date_list. replace it?"
        answer = input(ask_str)
        if "y" in answer:
            drop_no = folder_date_dict[path_folder_tg]
            del folder_date_list[drop_no]
            folder_date_list.append(folder_date_repr)


def update_exif(file_datetime_orig_list, path_rec_date_memo):
    for file_datetime in file_datetime_orig_list:
        path_file = file_datetime.path_file
        image = Image.open(path_file)
        exif_dict = piexif.load(image.info["exif"])

        # 撮影日情報をExifに格納
        str_datetime = file_datetime.datetime_orig.strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["Exif"][36867] = str_datetime.encode("utf8")

        # Exifを元ファイルに上書き
        exif_byte = piexif.dump(exif_dict)
        piexif.insert(exif_byte, str(path_file))
    path_file
    with open(path_rec_date_memo, mode="a") as f:
        str_parent = str(path_file.parent)
        f.write(f"{str_parent}\n")


def ext_orig_datetime_str(path_file):
    image = Image.open(str(path_file))
    exif_ifd = image.getexif().get_ifd(34665)
    datetime_original_str = exif_ifd[36867]
    return datetime_original_str


def ext_orig_datetime(path_file):
    datetime_original_str = ext_orig_datetime_str(path_file)
    if datetime_original_str == "    :  :     :  :  ":
        return None
    else:
        datetime = dt.datetime.strptime(datetime_original_str, "%Y:%m:%d %H:%M:%S")
        return datetime
