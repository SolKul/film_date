from typing import Union
from dataclasses import dataclass
from pathlib import Path
import pandas as pd


@dataclass
class FileDate:
    path_file: Path
    date: Union[pd.Timestamp, None]


@dataclass
class FolderDateRepresentative:
    path_folder: Path
    date_first: pd.Timestamp
    date_last: pd.Timestamp
    file_date_list: list[FileDate]

    def __post_init__(self):
        """代表日時を計算する"""
        tmp_date_sz = pd.Series([self.date_first, self.date_last])
        self.date_representative = tmp_date_sz.mean()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.path_folder.name == other.path_folder.name) and (
            self.date_representative == other.date_representative
        )

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.date_representative == other.date_representative:
            return self.path_folder.name < other.path_folder.name
        else:
            return self.date_representative < other.date_representative

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)


@dataclass
class FileDatetimeOriginal:
    file_date: FileDate
    datetime_orig: pd.Timestamp
