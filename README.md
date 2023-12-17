フィルム写真の右下の日付をもとに、画像データの撮影日(OriginalDate)を特定し、Exifを更新する

# 使い方

普通フィルム写真は、一連の写真を36枚程度を一つのフィルム上に撮影できる。  
フィルムごとの写真がフォルダごとに保存されているとし、  
そのフォルダごとに一連の写真について手動で撮影日を特定していく。  

JupyterNotebook上で[filmdate/manual_input.py](filmdate/manual_input.py)の`ImageDateQuestioner`をインスタンス化し、`ask_and_gen_folder_date`を実行し、手作業で写真の日付を入力していくと、写真のパスと日付がセットになったデータクラストのリストである`FolderDateRepresentative`が得られる  

例えば、あるフィルムの写真が、時系列順に`../dvd/No.2/002/`以下に`../dvd/No.2/002/001.jpg`、`../dvd/No.2/002/002.jpg`、...と保存されているときに、以下のようにして撮影日を特定する。  

```python
# フィルム写真の入ったフォルダを指定いする。
path_dir=Path("../dvd/No.2/002/")
path_memo=Path("check_date_dir_memo.txt")

# 写真の名前の順番と時系列の順番が一致している場合はasc(昇順)を指定
# 逆の場合は`desc`(降順)を指定
folder_date_repr=manual_input.ImageDateQuestioner.ask_gen_folder_date_cm(
    path_dir=path_dir,
    path_memo=path_memo,
    sort_dir="asc"
)
```

こうして得られたフォルダ内の写真と撮影日のデータについて、一旦リスト化してpickleで保存する。

```python
folder_date_repr_list=[]

folder_date_repr_list.append(folder_date_repr)

with open("folder_date_repr_list.pkl",mode="wb") as f:
    pickle.dump(folder_date_repr_list,f)
```

2回目以降このリストに追加する場合は、`append_folder_date_list`という関数を使い、同じフォルダに対して重複して写真と撮影日のデータを追加していないかをチェックする。

```python
# pickle保存した(FolderDateRepresentativeの)リストを開く
with open("folder_date_repr_list.pkl",mode="rb") as f:
    folder_date_repr_list=pickle.load(f)

# リストに新しく撮影日を特定したFolderDateRepresentativeを格納する
manual_input.append_folder_date_list(folder_date_repr_list,folder_date_repr)

# リストに追加したら、上書き保存する
with open("folder_date_repr_list.pkl",mode="wb") as f:
    pickle.dump(folder_date_repr_list,f)
```

撮影日時を特定したいフィルム写真全てについて撮影日の特定が終わったら、  
そのすべてについて、撮影日時を計算する  
できるだけ撮影日時の順番が整合性が取れるようにするため、フィルムフォルダごとに並び替えを行い、順番に撮影日時を決定する。

たとえばフォルダAの撮影日が`1990/1/1`で、フォルダBの最初の数枚が`1990/1/1`、残りは`1990/1/2`だった場合、  
もし同じ人がこの写真を撮ったとすると、フォルダA→フォルダBの順番で撮影したはずである。  
そうすると、撮影日時はフォルダA→フォルダBの順番になるはずである。


```python
# 日時を最適化する
# ファイルについて日付だけのデータ`folder_date_repr_list.pkl`から、  
# フォルダごとの代表日時を設定し、  
# 並び替えて、時間が被らないようにすることで、写真ごとの日時を計算する。 
ff_calc=trans_folder.FolderFileDatetimeCalculator()
folder_date_orig_list=ff_calc.calc_datetime_folder(folder_date_repr_list)
```

撮影日時が計算出来たら、最後にExifの撮影日時を更新して上書き保存する
```python
# すべてのファイルについて、撮影日時を更新
for flder_date_orig in folder_date_orig_list:
    for file_date_orig in flder_date_orig.file_date_orig_list:
        path_file=file_date_orig.file_date.path_file
        datetime_orig=file_date_orig.datetime_orig
        manual_input.update_exif(path_file,datetime_orig)
```