"""
A Pillow loader for .vtf files (aka Valve Texture Format)
REDxEYE <med45c@gmail.com>

Documentation:
  https://developer.valvesoftware.com/wiki/Valve_Texture_Format

The contents of this file are hereby released in the public domain (CC0)
Full text of the CC0 license:
  https://creativecommons.org/publicdomain/zero/1.0/
"""

from __future__ import annotations

import struct
from enum import IntEnum, IntFlag
from io import BufferedIOBase, BytesIO
from math import ceil, log
from typing import NamedTuple

from . import Image, ImageFile


class VTFException(Exception):
    pass


class CompiledVtfFlags(IntFlag):
    # Flags from the *.txt config file
    POINTSAMPLE = 0x00000001
    TRILINEAR = 0x00000002
    CLAMPS = 0x00000004
    CLAMPT = 0x00000008
    ANISOTROPIC = 0x00000010
    HINT_DXT5 = 0x00000020
    PWL_CORRECTED = 0x00000040
    NORMAL = 0x00000080
    NOMIP = 0x00000100
    NOLOD = 0x00000200
    ALL_MIPS = 0x00000400
    PROCEDURAL = 0x00000800

    # These are automatically generated by vtex from the texture data.
    ONEBITALPHA = 0x00001000
    EIGHTBITALPHA = 0x00002000

    # Newer flags from the *.txt config file
    ENVMAP = 0x00004000
    RENDERTARGET = 0x00008000
    DEPTHRENDERTARGET = 0x00010000
    NODEBUGOVERRIDE = 0x00020000
    SINGLECOPY = 0x00040000
    PRE_SRGB = 0x00080000

    UNUSED_00100000 = 0x00100000
    UNUSED_00200000 = 0x00200000
    UNUSED_00400000 = 0x00400000

    NODEPTHBUFFER = 0x00800000

    UNUSED_01000000 = 0x01000000

    CLAMPU = 0x02000000
    VERTEXTEXTURE = 0x04000000
    SSBUMP = 0x08000000

    UNUSED_10000000 = 0x10000000

    BORDER = 0x20000000

    UNUSED_40000000 = 0x40000000
    UNUSED_80000000 = 0x80000000


class VtfPF(IntEnum):
    NONE = -1
    RGBA8888 = 0
    ABGR8888 = 1
    RGB888 = 2
    BGR888 = 3
    # RGB565 = 4
    I8 = 5
    IA88 = 6
    # P8 = 7
    A8 = 8
    # RGB888_BLUESCREEN = 9
    # BGR888_BLUESCREEN = 10
    ARGB8888 = 11
    BGRA8888 = 12
    DXT1 = 13
    DXT3 = 14
    DXT5 = 15
    BGRX8888 = 16
    # BGR565 = 17
    # BGRX5551 = 18
    # BGRA4444 = 19
    DXT1_ONEBITALPHA = 20
    # BGRA5551 = 21
    UV88 = 22
    # UVWQ8888 = 23
    # RGBA16161616F = 24
    # RGBA16161616 = 25
    # UVLX8888 = 26


class VTFHeader(NamedTuple):
    header_size: int
    width: int
    height: int
    flags: int
    frames: int
    first_frames: int
    reflectivity_r: float
    reflectivity_g: float
    reflectivity_b: float
    bumpmap_scale: float
    pixel_format: int
    mipmap_count: int
    low_pixel_format: int
    low_width: int
    low_height: int
    depth: int
    resource_count: int


BLOCK_COMPRESSED = (VtfPF.DXT1, VtfPF.DXT1_ONEBITALPHA, VtfPF.DXT3, VtfPF.DXT5)
HEADER_V70 = "<I2HI2H4x3f4xfIbI2b"
HEADER_V72 = "<I2HI2H4x3f4xfIbI2bH"
HEADER_V73 = "<I2HI2H4x3f4xfIbI2bH3xI8x"


def _get_texture_size(pixel_format: VtfPF, width, height):
    if pixel_format in (VtfPF.DXT1, VtfPF.DXT1_ONEBITALPHA):
        return width * height // 2
    elif pixel_format in (VtfPF.DXT3, VtfPF.DXT5):
        return width * height
    elif pixel_format in (
        VtfPF.A8,
        VtfPF.I8,
    ):
        return width * height
    elif pixel_format in (VtfPF.UV88, VtfPF.IA88):
        return width * height * 2
    elif pixel_format in (VtfPF.RGB888, VtfPF.BGR888):
        return width * height * 3
    elif pixel_format == VtfPF.RGBA8888:
        return width * height * 4
    msg = f"Unsupported VTF pixel format: {pixel_format}"
    raise VTFException(msg)


def _get_mipmap_count(width: int, height: int):
    mip_count = 1
    while True:
        mip_width = width >> mip_count
        mip_height = height >> mip_count
        if mip_width == 0 and mip_height == 0:
            return mip_count
        mip_count += 1


def _write_image(fp: BufferedIOBase, im: Image.Image, pixel_format: VtfPF):
    extents = (0, 0) + im.size
    if pixel_format == VtfPF.DXT1:
        encoder = "bcn"
        encoder_args = (1, "DXT1")
        im = im.convert("RGBA")
    elif pixel_format == VtfPF.DXT1_ONEBITALPHA:
        encoder = "bcn"
        encoder_args = (1, "DXT1A")
    elif pixel_format == VtfPF.DXT3:
        encoder = "bcn"
        encoder_args = (3, "DXT3")
    elif pixel_format == VtfPF.DXT5:
        encoder = "bcn"
        encoder_args = (5, "DXT5")
    elif pixel_format == VtfPF.RGB888:
        encoder = "raw"
        encoder_args = ("RGB", 0, 0)
    elif pixel_format == VtfPF.BGR888:
        encoder = "raw"
        encoder_args = ("BGR", 0, 0)
    elif pixel_format == VtfPF.RGBA8888:
        encoder = "raw"
        encoder_args = ("RGBA", 0, 0)
    elif pixel_format == VtfPF.A8:
        encoder = "raw"
        encoder_args = ("A", 0, 0)
    elif pixel_format == VtfPF.I8:
        encoder = "raw"
        encoder_args = ("L", 0, 0)
        im = im.convert("L")
    elif pixel_format == VtfPF.IA88:
        encoder = "raw"
        encoder_args = ("LA", 0, 0)
        im = im.convert("LA")
    elif pixel_format == VtfPF.UV88:
        encoder = "raw"
        encoder_args = ("RG", 0, 0)
    else:
        msg = f"Unsupported pixel format: {pixel_format!r}"
        raise VTFException(msg)

    tile = [(encoder, extents, fp.tell(), encoder_args)]
    ImageFile._save(im, fp, tile, _get_texture_size(pixel_format, *im.size))


def _closest_power(x):
    possible_results = round(log(x, 2)), ceil(log(x, 2))
    return 2 ** min(possible_results, key=lambda z: abs(x - 2**z))


class VtfImageFile(ImageFile.ImageFile):
    format = "VTF"
    format_description = "Valve Texture Format"

    def _open(self):
        if not _accept(self.fp.read(12)):
            msg = "not a VTF file"
            raise SyntaxError(msg)
        self.fp.seek(4)
        version = struct.unpack("<2I", self.fp.read(8))
        if version <= (7, 2):
            header = VTFHeader(
                *struct.unpack(HEADER_V70, self.fp.read(struct.calcsize(HEADER_V70))),
                0,
                0,
                0,
                0,
                0,
            )
            self.fp.seek(header.header_size)
        elif version < (7, 3):
            header = VTFHeader(
                *struct.unpack(HEADER_V72, self.fp.read(struct.calcsize(HEADER_V72))),
                0,
                0,
                0,
                0,
            )
            self.fp.seek(header.header_size)
        elif version < (7, 5):
            header = VTFHeader(
                *struct.unpack(HEADER_V73, self.fp.read(struct.calcsize(HEADER_V73)))
            )
            self.fp.seek(header.header_size)
        else:
            msg = f"Unsupported VTF version: {version}"
            raise VTFException(msg)
        # flags = CompiledVtfFlags(header.flags)
        pixel_format = VtfPF(header.pixel_format)
        low_format = VtfPF(header.low_pixel_format)
        if pixel_format in (
            VtfPF.DXT1_ONEBITALPHA,
            VtfPF.DXT1,
            VtfPF.DXT3,
            VtfPF.DXT5,
            VtfPF.RGBA8888,
            VtfPF.BGRA8888,
            VtfPF.A8,
        ):
            self._mode = "RGBA"
        elif pixel_format in (VtfPF.RGB888, VtfPF.BGR888, VtfPF.UV88):
            self._mode = "RGB"
        elif pixel_format == VtfPF.I8:
            self._mode = "L"
        elif pixel_format == VtfPF.IA88:
            self._mode = "LA"
        else:
            msg = f"Unsupported VTF pixel format: {pixel_format}"
            raise VTFException(msg)

        self._size = (header.width, header.height)

        data_start = self.fp.tell()
        data_start += _get_texture_size(low_format, header.low_width, header.low_height)
        min_res = 4 if pixel_format in BLOCK_COMPRESSED else 1
        for mip_id in range(header.mipmap_count - 1, 0, -1):
            mip_width = max(header.width >> mip_id, min_res)
            mip_height = max(header.height >> mip_id, min_res)

            data_start += _get_texture_size(pixel_format, mip_width, mip_height)

        if pixel_format in (VtfPF.DXT1, VtfPF.DXT1_ONEBITALPHA):
            tile = ("bcn", (0, 0) + self.size, data_start, (1, "DXT1"))
        elif pixel_format == VtfPF.DXT3:
            tile = ("bcn", (0, 0) + self.size, data_start, (2, "DXT3"))
        elif pixel_format == VtfPF.DXT5:
            tile = ("bcn", (0, 0) + self.size, data_start, (3, "DXT5"))
        elif pixel_format == VtfPF.RGBA8888:
            tile = ("raw", (0, 0) + self.size, data_start, ("RGBA", 0, 1))
        elif pixel_format == VtfPF.RGB888:
            tile = ("raw", (0, 0) + self.size, data_start, ("RGB", 0, 1))
        elif pixel_format == VtfPF.BGR888:
            tile = ("raw", (0, 0) + self.size, data_start, ("BGR", 0, 1))
        elif pixel_format == VtfPF.BGRA8888:
            tile = ("raw", (0, 0) + self.size, data_start, ("BGRA", 0, 1))
        elif pixel_format == VtfPF.UV88:
            tile = ("raw", (0, 0) + self.size, data_start, ("RG", 0, 1))
        elif pixel_format == VtfPF.I8:
            tile = ("raw", (0, 0) + self.size, data_start, ("L", 0, 1))
        elif pixel_format == VtfPF.A8:
            tile = ("raw", (0, 0) + self.size, data_start, ("A", 0, 1))
        elif pixel_format == VtfPF.IA88:
            tile = ("raw", (0, 0) + self.size, data_start, ("LA", 0, 1))
        else:
            msg = f"Unsupported VTF pixel format: {pixel_format}"
            raise VTFException(msg)
        self.tile = [tile]


def _save(im, fp, filename):
    im: Image.Image
    if im.mode not in ("RGB", "RGBA", "L", "LA"):
        msg = f"cannot write mode {im.mode} as VTF"
        raise OSError(msg)
    encoderinfo = im.encoderinfo
    pixel_format = VtfPF(encoderinfo.get("pixel_format", VtfPF.RGBA8888))
    version = encoderinfo.get("version", (7, 4))
    generate_mips = encoderinfo.get("generate_mips", True)

    flags = CompiledVtfFlags(0)

    if pixel_format == VtfPF.DXT1_ONEBITALPHA:
        flags |= CompiledVtfFlags.ONEBITALPHA
    elif pixel_format in (
        VtfPF.DXT3,
        VtfPF.DXT5,
        VtfPF.RGBA8888,
        VtfPF.BGRA8888,
        VtfPF.A8,
        VtfPF.IA88,
    ):
        flags |= CompiledVtfFlags.EIGHTBITALPHA
    else:
        pass
    im = im.resize((_closest_power(im.width), _closest_power(im.height)))
    width, height = im.size

    mipmap_count = 0
    if generate_mips:
        mipmap_count = _get_mipmap_count(width, height)

    thumb_buffer = BytesIO()
    thumb = im.convert("RGB")
    thumb.thumbnail(((min(16, width)), (min(16, height))))
    thumb = thumb.resize((_closest_power(thumb.width), _closest_power(thumb.height)))
    _write_image(thumb_buffer, thumb, VtfPF.DXT1)

    header = VTFHeader(
        0,
        width,
        height,
        flags,
        1,
        0,
        1.0,
        1.0,
        1.0,
        1.0,
        pixel_format,
        mipmap_count,
        VtfPF.DXT1,
        thumb.width,
        thumb.height,
        1,
        2,
    )

    fp.write(b"VTF\x00" + struct.pack("<2I", *version))
    if version < (7, 2):
        size = struct.calcsize(HEADER_V70) + 12
        header = header._replace(header_size=size + (16 - size % 16))
        fp.write(struct.pack(HEADER_V70, *header[:15]))
    elif version == (7, 2):
        size = struct.calcsize(HEADER_V72) + 12
        header = header._replace(header_size=size + (16 - size % 16))
        fp.write(struct.pack(HEADER_V72, *header[:16]))
    elif version > (7, 2):
        size = struct.calcsize(HEADER_V73) + 12
        header = header._replace(header_size=size + (16 - size % 16))
        fp.write(struct.pack(HEADER_V73, *header))
    else:
        msg = f"Unsupported version {version}"
        raise VTFException(msg)

    if version > (7, 2):
        fp.write(b"\x01\x00\x00\x00")
        fp.write(struct.pack("<I", header.header_size))
        fp.write(b"\x30\x00\x00\x00")
        fp.write(struct.pack("<I", header.header_size + len(thumb_buffer.getbuffer())))
    else:
        fp.write(b"\x00" * (16 - fp.tell() % 16))
    fp.write(thumb_buffer.getbuffer())

    if pixel_format in BLOCK_COMPRESSED:
        min_size = 4
    else:
        min_size = 1

    for mip_id in range(mipmap_count - 1, 0, -1):
        mip_width = max(min_size, width >> mip_id)
        mip_height = max(min_size, height >> mip_id)
        mip = im.resize((mip_width, mip_height))
        _write_image(fp, mip, pixel_format)
    _write_image(fp, im, pixel_format)


def _accept(prefix):
    valid_header = prefix[:4] == b"VTF\x00"
    valid_version = struct.unpack_from("<2I", prefix, 4) >= (7, 0)
    return valid_header and valid_version


Image.register_open(VtfImageFile.format, VtfImageFile, _accept)
Image.register_save(VtfImageFile.format, _save)
Image.register_extension(VtfImageFile.format, ".vtf")