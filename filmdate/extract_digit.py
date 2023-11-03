from . import redness, rec_digit


def recognize_date(image):
    # 2値化した日付周辺画像
    date_neighbor = redness.extract_date_neighbor(image)

    # 左上のドットの位置を特定する
    dot_positioner = rec_digit.DotPositioner(date_neighbor)
    dot_vertical_start, dot_horizontal_start = dot_positioner.calc_dot_left_upper()

    # 数値画像を抽出する
    digit_extractor = rec_digit.DigitsImageExtractor(
        date_neighbor, dot_vertical_start, dot_horizontal_start
    )
    just_srd_ext_resized = digit_extractor.ext_digit_image()

    # 数値を認識する
    seven_seg_recognizer = rec_digit.SevenSegRecognizer(just_srd_ext_resized)
    digit_recognized = seven_seg_recognizer.recoginize_digit()

    return digit_recognized
