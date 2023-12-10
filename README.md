フィルム写真の右下の日付をもとに、画像データの撮影日(OriginalDate)を特定し、Exifを更新する

# 使い方

JupyterNotebook上で[filmdate/manual_input.py](filmdate/manual_input.py)の`ImageDateQuestioner`をインスタンス化し、`ask_and_gen_folder_date`を実行し、手作業で写真の日付を入力していくと、写真のパスと日付がセットになったデータクラストのリストである`FolderDateRepresentative`が得られる

```python
path_dir=Path("../dvd/No.2/002/")
path_memo=Path("check_date_dir_memo.txt")

img_dae_quest=manual_input.ImageDateQuestioner(path_dir=path_dir,path_memo=path_memo)

folder_date_repr=img_dae_quest.ask_and_gen_folder_date()
```