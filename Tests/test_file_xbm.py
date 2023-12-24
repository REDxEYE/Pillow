from __future__ import annotations
from io import BytesIO

import pytest

from PIL import Image, XbmImagePlugin

from .helper import hopper

PIL151 = b"""
#define basic_width 32
#define basic_height 32
static char basic_bits[] = {
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00,
0x80, 0xff, 0xff, 0x01, 0x40, 0x00, 0x00, 0x02,
0x20, 0x00, 0x00, 0x04, 0x20, 0x00, 0x00, 0x04, 0x10, 0x00, 0x00, 0x08,
0x10, 0x00, 0x00, 0x08,
0x10, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08,
0x10, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08,
0x20, 0x00, 0x00, 0x04,
0x20, 0x00, 0x00, 0x04, 0x40, 0x00, 0x00, 0x02,
0x80, 0xff, 0xff, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00,
};
"""


def test_pil151():
    with Image.open(BytesIO(PIL151)) as im:
        im.load()
        assert im.mode == "1"
        assert im.size == (32, 32)


def test_open():
    # Arrange
    # Created with `convert hopper.png hopper.xbm`
    filename = "Tests/images/hopper.xbm"

    # Act
    with Image.open(filename) as im:
        # Assert
        assert im.mode == "1"
        assert im.size == (128, 128)


def test_open_filename_with_underscore():
    # Arrange
    # Created with `convert hopper.png hopper_underscore.xbm`
    filename = "Tests/images/hopper_underscore.xbm"

    # Act
    with Image.open(filename) as im:
        # Assert
        assert im.mode == "1"
        assert im.size == (128, 128)


def test_invalid_file():
    invalid_file = "Tests/images/flower.jpg"

    with pytest.raises(SyntaxError):
        XbmImagePlugin.XbmImageFile(invalid_file)


def test_save_wrong_mode(tmp_path):
    im = hopper()
    out = str(tmp_path / "temp.xbm")

    with pytest.raises(OSError):
        im.save(out)


def test_hotspot(tmp_path):
    im = hopper("1")
    out = str(tmp_path / "temp.xbm")

    hotspot = (0, 7)
    im.save(out, hotspot=hotspot)

    with Image.open(out) as reloaded:
        assert reloaded.info["hotspot"] == hotspot
