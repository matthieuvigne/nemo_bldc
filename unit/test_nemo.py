from nemo_bldc.nemo import nemo_main


def test_nemo_build_gui():
    # Simply test if GUI works ok
    nemo_main(is_unit_test=True)
