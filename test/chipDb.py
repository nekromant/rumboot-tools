from rumboot.chipDb import ChipDb


def smoke_test():
    db = ChipDb("rumboot.chips")
    c = db["basis"]
    assert c.chip_id == 3
    assert c.chip_rev == 1
