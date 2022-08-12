"""
A Pillow loader for .vtf files (aka Valve Texture Format)
REDxEYE <med45c@gmail.com>

Documentation:
  https://developer.valvesoftware.com/wiki/Valve_Texture_Format

The contents of this file are hereby released in the public domain (CC0)
Full text of the CC0 license:
  https://creativecommons.org/publicdomain/zero/1.0/
"""

import struct
from enum import IntEnum, IntFlag
from io import BytesIO
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
    RGB565 = 4
    I8 = 5
    IA88 = 6
    P8 = 7
    A8 = 8
    RGB888_BLUESCREEN = 9
    BGR888_BLUESCREEN = 10
    ARGB8888 = 11
    BGRA8888 = 12
    DXT1 = 13
    DXT3 = 14
    DXT5 = 15
    BGRX8888 = 16
    BGR565 = 17
    BGRX5551 = 18
    BGRA4444 = 19
    DXT1_ONEBITALPHA = 20
    BGRA5551 = 21
    UV88 = 22
    UVWQ8888 = 23
    RGBA16161616F = 24
    RGBA16161616 = 25
    UVLX8888 = 26


VTFHeader = NamedTuple(
    "VTFHeader",
    [
        ("header_size", int),
        ("width", int),
        ("height", int),
        ("flags", int),
        ("frames", int),
        ("first_frames", int),
        ("reflectivity_r", float),
        ("reflectivity_g", float),
        ("reflectivity_b", float),
        ("bumpmap_scale", float),
        ("pixel_format", int),
        ("mipmap_count", int),
        ("low_pixel_format", int),
        ("low_width", int),
        ("low_height", int),
        # V 7.2+
        ("depth", int),
        # V 7.3+
        ("resource_count", int),
    ],
)
RGB_FORMATS = (VtfPF.RGB888,)
RGBA_FORMATS = (
    VtfPF.DXT1,
    VtfPF.DXT1_ONEBITALPHA,
    VtfPF.DXT3,
    VtfPF.DXT5,
    VtfPF.RGBA8888,
)
L_FORMATS = (
    VtfPF.A8,
    VtfPF.I8,
)
LA_FORMATS = (
    VtfPF.IA88,
    VtfPF.UV88,
)

BLOCK_COMPRESSED = (VtfPF.DXT1, VtfPF.DXT1_ONEBITALPHA, VtfPF.DXT3, VtfPF.DXT5)
SUPPORTED_FORMATS = RGBA_FORMATS + RGB_FORMATS + LA_FORMATS + L_FORMATS
HEADER_V70 = "<I2HI2H4x3f4xfIbI2b"
HEADER_V72 = "<I2HI2H4x3f4xfIbI2bH"
HEADER_V73 = "<I2HI2H4x3f4xfIbI2bH3xI8x"


def _get_texture_size(pixel_format: VtfPF, width, height):
    if pixel_format in (VtfPF.DXT1, VtfPF.DXT1_ONEBITALPHA):
        return width * height // 2
    elif (
        pixel_format
        in (
            VtfPF.DXT3,
            VtfPF.DXT5,
        )
        + L_FORMATS
    ):
        return width * height
    elif pixel_format in LA_FORMATS:
        return width * height * 2
    elif pixel_format in (VtfPF.RGB888,):
        return width * height * 3
    elif pixel_format in (VtfPF.RGBA8888,):
        return width * height * 4
    raise VTFException(f"Unsupported VTF pixel format: {pixel_format}")


def _get_mipmap_count(width: int, height: int):
    mip_count = 1
    while True:
        mip_width = width >> mip_count
        mip_height = height >> mip_count
        if mip_width < 1 or mip_height < 1:
            break
        mip_count += 1
    return mip_count


def closest_power(x):
    possible_results = round(log(x, 2)), ceil(log(x, 2))
    return 2 ** min(possible_results, key=lambda z: abs(x - 2**z))


class VtfImageFile(ImageFile.ImageFile):
    format = "VTF"
    format_description = "Valve Texture Format"

    def _open(self):
        if not _accept(self.fp.read(12)):
            raise SyntaxError("not a VTF file")
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
        elif (7, 2) <= version < (7, 3):
            header = VTFHeader(
                *struct.unpack(HEADER_V72, self.fp.read(struct.calcsize(HEADER_V72))),
                0,
                0,
                0,
                0,
            )
            self.fp.seek(header.header_size)
        elif (7, 3) <= version < (7, 5):
            header = VTFHeader(
                *struct.unpack(HEADER_V73, self.fp.read(struct.calcsize(HEADER_V73)))
            )
            self.fp.seek(header.header_size)
        else:
            raise VTFException(f"Unsupported VTF version: {version}")
        # flags = CompiledVtfFlags(header.flags)
        pixel_format = VtfPF(header.pixel_format)
        low_format = VtfPF(header.low_pixel_format)

        if pixel_format in RGB_FORMATS:
            self.mode = "RGB"
        elif pixel_format in RGBA_FORMATS:
            self.mode = "RGBA"
        elif pixel_format in L_FORMATS:
            self.mode = "L"
        elif pixel_format in LA_FORMATS:
            self.mode = "LA"
        else:
            raise VTFException(f"Unsupported VTF pixel format: {pixel_format}")

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
        elif pixel_format in (VtfPF.RGBA8888,):
            tile = ("raw", (0, 0) + self.size, data_start, ("RGBA", 0, 1))
        elif pixel_format in (VtfPF.RGB888,):
            tile = ("raw", (0, 0) + self.size, data_start, ("RGB", 0, 1))
        elif pixel_format in L_FORMATS:
            tile = ("raw", (0, 0) + self.size, data_start, ("L", 0, 1))
        elif pixel_format in LA_FORMATS:
            tile = ("raw", (0, 0) + self.size, data_start, ("LA", 0, 1))
        else:
            raise VTFException(f"Unsupported VTF pixel format: {pixel_format}")
        self.tile = [tile]


def _save(im, fp, filename):
    im: Image.Image
    if im.mode not in ("RGB", "RGBA"):
        raise OSError(f"cannot write mode {im.mode} as VTF")
    arguments = im.encoderinfo
    pixel_format = VtfPF(arguments.get("pixel_format", VtfPF.RGBA8888))
    version = arguments.get("version", (7, 4))
    flags = CompiledVtfFlags(0)
    if "A" in im.mode:
        if pixel_format == VtfPF.DXT1_ONEBITALPHA:
            flags |= CompiledVtfFlags.ONEBITALPHA
        elif pixel_format == VtfPF.DXT1:
            im = im.convert("RGB")
        else:
            flags |= CompiledVtfFlags.EIGHTBITALPHA

    im = im.resize((closest_power(im.width), closest_power(im.height)))
    width, height = im.size

    mipmap_count = _get_mipmap_count(width, height)

    thumb_buffer = BytesIO()
    thumb = im.convert("RGB")
    thumb.thumbnail(((min(16, width)), (min(16, height))))
    thumb = thumb.resize((closest_power(thumb.width), closest_power(thumb.height)))
    ImageFile._save(thumb, thumb_buffer, [("bcn", (0, 0) + thumb.size, 0, (1, "DXT1"))])

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
        raise VTFException(f"Unsupported version {version}")

    if version > (7, 2):
        fp.write(b"\x01\x00\x00\x00")
        fp.write(struct.pack("<I", header.header_size))
        fp.write(b"\x30\x00\x00\x00")
        fp.write(struct.pack("<I", header.header_size + len(thumb_buffer.getbuffer())))
    else:
        fp.write(b"\x00" * (16 - fp.tell() % 16))
    fp.write(thumb_buffer.getbuffer())

    for mip_id in range(mipmap_count - 1, 0, -1):
        mip_width = max(4, width >> mip_id)
        mip_height = max(4, height >> mip_id)
        mip = im.resize((mip_width, mip_height))
        buffer_size = mip_width * mip_height // 2
        extents = (0, 0) + mip.size
        ImageFile._save(
            mip, fp, [("bcn", extents, fp.tell(), (1, "DXT1"))], buffer_size
        )
    buffer_size = im.width * im.height // 2
    ImageFile._save(
        im, fp, [("bcn", (0, 0) + im.size, fp.tell(), (1, "DXT1"))], buffer_size
    )


def _accept(prefix):
    valid_header = prefix[:4] == b"VTF\x00"
    valid_version = struct.unpack_from("<2I", prefix, 4) >= (7, 0)
    return valid_header and valid_version


Image.register_open(VtfImageFile.format, VtfImageFile, _accept)
Image.register_save(VtfImageFile.format, _save)
Image.register_extension(VtfImageFile.format, ".vtf")
