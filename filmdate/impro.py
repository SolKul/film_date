from typing import Union
import numpy as np
import cv2
import matplotlib.pyplot as plt


def imshow(
    img: np.ndarray,
    ax: Union[None, plt.axes] = None,
    figsize: tuple[int, int] = (9, 6),
    isBGR: bool = True,
    show_mode: str = "as is",
    show_axis: bool = False,
    return_fig: bool = False,
) -> Union[None, plt.Figure]:
    """
    np.array形式の画像を表示する。カラーでもグレースケールでも対応。
    グレースケールの場合、そのまま、スケール、ログスケールで表示するかが選べる。
    show_modeが"as is"の場合そのまま、"sacale"の場合最小値が0、最大値が255になるようスケールして
    "log" :最小値が0、最大値が255になるようログでスケールして表示する。

    Args:
        img (np.ndarray): 表示したい画像
        figsize (tuple[int,int], optional): pltのfigsize. Defaults to (9,6).
        isBGR (bool, optional): opencvで読み込んだ場合、チャネルがBGRなので変換する必要がある. Defaults to True.
        show_mode (str, optional): 上の説明を参照. Defaults to "scale".
        show_axis (bool, optional): x軸、y軸の表示を消す. Defaults to False.
        return_fig (bool, optional): plt.figureで生成したfigを返すか. Defaults to False.

    Raises:
        ValueError: 画像の次元数が2か3でないの場合

    Returns:
        Union[None,plt.Figure]: figを返す場合、ax=fig.axes[0]とすれば、その後表示を付け足せる。
    """
    # ここで生成したfigがcurrent figureとなるので、
    # notebookでこのまま抜けるとこのfigが描写される
    if ax is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.gca()
    dim_num = len(img.shape)
    # 画像の次元数は2(グレースケール)か3(カラー)のどちらかに対応
    if dim_num < 2 or dim_num > 3:
        raise ValueError("dimenstion sholud be 2 or 3")
    if dim_num == 3:
        img = img.astype(np.uint8)
        if isBGR:
            img_cvt = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_cvt = img
        ax.imshow(img_cvt)
    else:
        if show_mode == "as is":
            img_show = img.astype(np.uint8)
            ax.imshow(img_show, cmap="gray", vmin=0, vmax=255)
        elif show_mode == "scale":
            min_intens = img.min()
            max_intens = img.max()
            img_show = ((img - min_intens) / (max_intens - min_intens) * 255).astype(np.uint8)
            ax.imshow(img_show, cmap="gray")
        elif show_mode == "log":
            min_intens = img.min()
            max_intens = img.max()
            img_show = (
                np.log(img - min_intens + 1e-5) / np.log(max_intens - min_intens) * 255
            ).astype(np.uint8)
            ax.imshow(img_show, cmap="gray")
    if not show_axis:
        plt.axis("off")
    if return_fig:
        return fig
