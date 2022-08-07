"""
A Pillow loader for .dds files (S3TC-compressed aka DXTC)
Jerome Leclanche <jerome@leclan.ch>

Documentation:
  https://web.archive.org/web/20170802060935/http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_compression_s3tc.txt

The contents of this file are hereby released in the public domain (CC0)
Full text of the CC0 license:
  https://creativecommons.org/publicdomain/zero/1.0/
"""

import struct
from enum import IntEnum, IntFlag
from io import BytesIO

from . import Image, ImageFile
from ._binary import o32le as o32

# Magic ("DDS ")
DDS_MAGIC = 0x20534444


# DDS flags
class DDSD(IntFlag):
    CAPS = 0x1
    HEIGHT = 0x2
    WIDTH = 0x4
    PITCH = 0x8
    PIXELFORMAT = 0x1000
    MIPMAPCOUNT = 0x20000
    LINEARSIZE = 0x80000
    DEPTH = 0x800000


# DDS caps
class DDSCAPS(IntFlag):
    COMPLEX = 0x8
    TEXTURE = 0x1000
    MIPMAP = 0x400000


class DDSCAPS2(IntFlag):
    CUBEMAP = 0x200
    CUBEMAP_POSITIVEX = 0x400
    CUBEMAP_NEGATIVEX = 0x800
    CUBEMAP_POSITIVEY = 0x1000
    CUBEMAP_NEGATIVEY = 0x2000
    CUBEMAP_POSITIVEZ = 0x4000
    CUBEMAP_NEGATIVEZ = 0x8000
    VOLUME = 0x200000


# Pixel Format
class DDPF(IntFlag):
    ALPHAPIXELS = 0x1
    ALPHA = 0x2
    FOURCC = 0x4
    PALETTEINDEXED8 = 0x20
    RGB = 0x40
    LUMINANCE = 0x20000


# dxgiformat.h
class DXGI_FORMAT(IntEnum):
    UNKNOWN = 0
    R32G32B32A32_TYPELESS = 1
    R32G32B32A32_FLOAT = 2
    R32G32B32A32_UINT = 3
    R32G32B32A32_SINT = 4
    R32G32B32_TYPELESS = 5
    R32G32B32_FLOAT = 6
    R32G32B32_UINT = 7
    R32G32B32_SINT = 8
    R16G16B16A16_TYPELESS = 9
    R16G16B16A16_FLOAT = 10
    R16G16B16A16_UNORM = 11
    R16G16B16A16_UINT = 12
    R16G16B16A16_SNORM = 13
    R16G16B16A16_SINT = 14
    R32G32_TYPELESS = 15
    R32G32_FLOAT = 16
    R32G32_UINT = 17
    R32G32_SINT = 18
    R32G8X24_TYPELESS = 19
    D32_FLOAT_S8X24_UINT = 20
    R32_FLOAT_X8X24_TYPELESS = 21
    X32_TYPELESS_G8X24_UINT = 22
    R10G10B10A2_TYPELESS = 23
    R10G10B10A2_UNORM = 24
    R10G10B10A2_UINT = 25
    R11G11B10_FLOAT = 26
    R8G8B8A8_TYPELESS = 27
    R8G8B8A8_UNORM = 28
    R8G8B8A8_UNORM_SRGB = 29
    R8G8B8A8_UINT = 30
    R8G8B8A8_SNORM = 31
    R8G8B8A8_SINT = 32
    R16G16_TYPELESS = 33
    R16G16_FLOAT = 34
    R16G16_UNORM = 35
    R16G16_UINT = 36
    R16G16_SNORM = 37
    R16G16_SINT = 38
    R32_TYPELESS = 39
    D32_FLOAT = 40
    R32_FLOAT = 41
    R32_UINT = 42
    R32_SINT = 43
    R24G8_TYPELESS = 44
    D24_UNORM_S8_UINT = 45
    R24_UNORM_X8_TYPELESS = 46
    X24_TYPELESS_G8_UINT = 47
    R8G8_TYPELESS = 48
    R8G8_UNORM = 49
    R8G8_UINT = 50
    R8G8_SNORM = 51
    R8G8_SINT = 52
    R16_TYPELESS = 53
    R16_FLOAT = 54
    D16_UNORM = 55
    R16_UNORM = 56
    R16_UINT = 57
    R16_SNORM = 58
    R16_SINT = 59
    R8_TYPELESS = 60
    R8_UNORM = 61
    R8_UINT = 62
    R8_SNORM = 63
    R8_SINT = 64
    A8_UNORM = 65
    R1_UNORM = 66
    R9G9B9E5_SHAREDEXP = 67
    R8G8_B8G8_UNORM = 68
    G8R8_G8B8_UNORM = 69
    BC1_TYPELESS = 70
    BC1_UNORM = 71
    BC1_UNORM_SRGB = 72
    BC2_TYPELESS = 73
    BC2_UNORM = 74
    BC2_UNORM_SRGB = 75
    BC3_TYPELESS = 76
    BC3_UNORM = 77
    BC3_UNORM_SRGB = 78
    BC4_TYPELESS = 79
    BC4_UNORM = 80
    BC4_SNORM = 81
    BC5_TYPELESS = 82
    BC5_UNORM = 83
    BC5_SNORM = 84
    B5G6R5_UNORM = 85
    B5G5R5A1_UNORM = 86
    B8G8R8A8_UNORM = 87
    B8G8R8X8_UNORM = 88
    R10G10B10_XR_BIAS_A2_UNORM = 89
    B8G8R8A8_TYPELESS = 90
    B8G8R8A8_UNORM_SRGB = 91
    B8G8R8X8_TYPELESS = 92
    B8G8R8X8_UNORM_SRGB = 93
    BC6H_TYPELESS = 94
    BC6H_UF16 = 95
    BC6H_SF16 = 96
    BC7_TYPELESS = 97
    BC7_UNORM = 98
    BC7_UNORM_SRGB = 99
    AYUV = 100
    Y410 = 101
    Y416 = 102
    NV12 = 103
    P010 = 104
    P016 = 105
    _420_OPAQUE = 106
    YUY2 = 107
    Y210 = 108
    Y216 = 109
    NV11 = 110
    AI44 = 111
    IA44 = 112
    P8 = 113
    A8P8 = 114
    B4G4R4A4_UNORM = 115
    P208 = 130
    V208 = 131
    V408 = 132
    SAMPLER_FEEDBACK_MIN_MIP_OPAQUE = 133
    SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE = 134
    INVALID = -1

    @classmethod
    def _missing_(cls, value: object):
        return cls.INVALID


def make_fourcc(name):
    return struct.unpack("I", name.encode("ascii"))[0]


class D3DFMT(IntEnum):
    UNKNOWN = 0
    R8G8B8 = 20
    A8R8G8B8 = 21
    X8R8G8B8 = 22
    R5G6B5 = 23
    X1R5G5B5 = 24
    A1R5G5B5 = 25
    A4R4G4B4 = 26
    R3G3B2 = 27
    A8 = 28
    A8R3G3B2 = 29
    X4R4G4B4 = 30
    A2B10G10R10 = 31
    A8B8G8R8 = 32
    X8B8G8R8 = 33
    G16R16 = 34
    A2R10G10B10 = 35
    A16B16G16R16 = 36
    A8P8 = 40
    P8 = 41
    L8 = 50
    A8L8 = 51
    A4L4 = 52
    V8U8 = 60
    L6V5U5 = 61
    X8L8V8U8 = 62
    Q8W8V8U8 = 63
    V16U16 = 64
    A2W10V10U10 = 67
    D16_LOCKABLE = 70
    D32 = 71
    D15S1 = 73
    D24S8 = 75
    D24X8 = 77
    D24X4S4 = 79
    D16 = 80
    D32F_LOCKABLE = 82
    D24FS8 = 83
    D32_LOCKABLE = 84
    S8_LOCKABLE = 85
    L16 = 81
    VERTEXDATA = 100
    INDEX16 = 101
    INDEX32 = 102
    Q16W16V16U16 = 110
    R16F = 111
    G16R16F = 112
    A16B16G16R16F = 113
    R32F = 114
    G32R32F = 115
    A32B32G32R32F = 116
    CxV8U8 = 117
    A1 = 118
    A2B10G10R10_XR_BIAS = 119
    BINARYBUFFER = 199

    UYVY = make_fourcc("UYVY")
    R8G8_B8G8 = make_fourcc("RGBG")
    YUY2 = make_fourcc("YUY2")
    G8R8_G8B8 = make_fourcc("GRGB")
    DXT1 = make_fourcc("DXT1")
    DXT2 = make_fourcc("DXT2")
    DXT3 = make_fourcc("DXT3")
    DXT4 = make_fourcc("DXT4")
    DXT5 = make_fourcc("DXT5")
    DX10 = make_fourcc("DX10")
    BC5S = make_fourcc("BC5S")
    ATI1 = make_fourcc("ATI1")
    ATI2 = make_fourcc("ATI2")
    MULTI2_ARGB8 = make_fourcc("MET1")
    INVALID = -1

    @classmethod
    def _missing_(cls, value: object):
        return cls.INVALID


class DdsImageFile(ImageFile.ImageFile):
    format = "DDS"
    format_description = "DirectDraw Surface"

    # fmt: off
    def _open(self):
        if not _accept(self.fp.read(4)):
            raise SyntaxError("not a DDS file")
        (header_size,) = struct.unpack("<I", self.fp.read(4))
        if header_size != 124:
            raise OSError(f"Unsupported header size {repr(header_size)}")
        header_bytes = self.fp.read(header_size - 4)
        if len(header_bytes) != 120:
            raise OSError(f"Incomplete header: {len(header_bytes)} bytes")
        header = BytesIO(header_bytes)

        flags_, height, width = struct.unpack("<3I", header.read(12))
        flags = DDSD(flags_)
        self._size = (width, height)

        pitch, depth, mipmaps = struct.unpack("<3I", header.read(12))
        struct.unpack("<11I", header.read(44))  # reserved

        # pixel format
        pfsize, pfflags_, fourcc_, bitcount = struct.unpack("<4I", header.read(16))
        pfflags = DDPF(pfflags_)
        fourcc = D3DFMT(fourcc_)
        masks = struct.unpack("<4I", header.read(16))
        if flags & DDSD.CAPS:
            (caps1_, caps2_, caps3, caps4, _,) = struct.unpack("<5I", header.read(20))
        else:
            (caps1_, caps2_, caps3, caps4, _,) = (0, 0, 0, 0, 0,)
        caps1 = DDSCAPS(caps1_)
        caps2 = DDSCAPS2(caps2_)
        if pfflags & DDPF.RGB:
            # Texture contains uncompressed RGB data
            masks = {mask: ["R", "G", "B", "A"][i] for i, mask in enumerate(masks)}
            if bitcount == 24:
                rawmode = masks[0x00FF0000] + masks[0x0000FF00] + masks[0x000000FF]
                self.mode = "RGB"
                self.tile = [("raw", (0, 0) + self.size, 0, (rawmode[::-1], 0, 1))]
            elif bitcount == 32 and pfflags & DDPF.ALPHAPIXELS:
                self.mode = "RGBA"
                rawmode = (masks[0xFF000000] + masks[0x00FF0000] + masks[0x0000FF00] + masks[0x000000FF])
                self.tile = [("raw", (0, 0) + self.size, 0, (rawmode[::-1], 0, 1))]
            else:
                raise OSError(f"Unsupported bitcount {bitcount} for {pfflags} DDS texture")
        elif pfflags & DDPF.LUMINANCE:
            if bitcount == 8:
                self.mode = "L"
                self.tile = [("raw", (0, 0) + self.size, 0, ("L", 0, 1))]
            elif bitcount == 16 and pfflags & DDPF.ALPHAPIXELS:
                self.mode = "LA"
                self.tile = [("raw", (0, 0) + self.size, 0, ("LA", 0, 1))]
            else:
                raise OSError(f"Unsupported bitcount {bitcount} for {pfflags} DDS texture")
        elif pfflags & DDPF.FOURCC:
            data_start = header_size + 4
            if fourcc == D3DFMT.DXT1:
                self.mode = "RGBA"
                self.pixel_format = "DXT1"
                tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (1, self.pixel_format))
            elif fourcc == D3DFMT.DXT3:
                self.mode = "RGBA"
                self.pixel_format = "DXT3"
                tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (2, self.pixel_format))
            elif fourcc == D3DFMT.DXT5:
                self.mode = "RGBA"
                self.pixel_format = "DXT5"
                tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (3, self.pixel_format))
            elif fourcc == D3DFMT.ATI1:
                self.mode = "L"
                self.pixel_format = "BC4"
                tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (4, self.pixel_format))
            elif fourcc == D3DFMT.BC5S:
                self.mode = "RGB"
                self.pixel_format = "BC5S"
                tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (5, self.pixel_format))
            elif fourcc == D3DFMT.ATI2:
                self.mode = "RGB"
                self.pixel_format = "BC5"
                tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (5, self.pixel_format))
            elif fourcc == D3DFMT.DX10:
                data_start += 20
                # ignoring flags which pertain to volume textures and cubemaps
                (dxgi_format,) = struct.unpack("<I", self.fp.read(4))
                self.fp.read(16)
                if dxgi_format in (DXGI_FORMAT.BC5_TYPELESS, DXGI_FORMAT.BC5_UNORM):
                    self.mode = "RGB"
                    self.pixel_format = "BC5"
                    tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (5, self.pixel_format))
                elif dxgi_format == DXGI_FORMAT.BC5_SNORM:
                    self.mode = "RGB"
                    self.pixel_format = "BC5S"
                    tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (5, self.pixel_format))
                elif dxgi_format in (DXGI_FORMAT.BC7_TYPELESS, DXGI_FORMAT.BC7_UNORM):
                    self.mode = "RGBA"
                    self.pixel_format = "BC7"
                    tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (7, self.pixel_format))
                elif dxgi_format == DXGI_FORMAT.BC7_UNORM_SRGB:
                    self.mode = "RGBA"
                    self.pixel_format = "BC7"
                    self.info["gamma"] = 1 / 2.2
                    tile = Image.Tile("bcn", (0, 0) + self.size, data_start, (7, self.pixel_format))
                elif dxgi_format in (
                    DXGI_FORMAT.R8G8B8A8_TYPELESS,
                    DXGI_FORMAT.R8G8B8A8_UNORM,
                    DXGI_FORMAT.R8G8B8A8_UNORM_SRGB,
                ):
                    self.mode = "RGBA"
                    tile = Image.Tile("raw", (0, 0) + self.size, 0, ("RGBA", 0, 1))
                    if dxgi_format == DXGI_FORMAT.R8G8B8A8_UNORM_SRGB:
                        self.info["gamma"] = 1 / 2.2
                else:
                    raise NotImplementedError(
                        f"Unimplemented DXGI format {dxgi_format}"
                    )

            else:
                raise NotImplementedError(f"Unimplemented pixel format {repr(fourcc)}")

            self.tile = [tile]
        else:
            raise NotImplementedError(f"Unknown pixel format flags {repr(pfflags)}")

    # fmt: on

    def load_seek(self, pos):
        pass


# fmt: off
def _save(im, fp, filename):
    if im.mode not in ("RGB", "RGBA", "L", 'LA'):
        raise OSError(f"cannot write mode {im.mode} as DDS")

    pixel_flags = DDPF.RGB
    if im.mode == "RGB":
        rgba_mask = struct.pack("<4I", 0x00FF0000, 0x0000FF00, 0x000000FF, 0x00000000)
        bit_count = 24
    elif im.mode == "RGBA":
        pixel_flags |= DDPF.ALPHAPIXELS
        rgba_mask = struct.pack("<4I", 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        bit_count = 32
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (a, r, g, b))
    elif im.mode == 'LA':
        pixel_flags = DDPF.LUMINANCE | DDPF.ALPHAPIXELS
        rgba_mask = struct.pack("<4I", 0x000000FF, 0x000000FF, 0x000000FF, 0x0000FF00)
        bit_count = 16
    else:  # im.mode == "L"
        pixel_flags = DDPF.LUMINANCE
        rgba_mask = struct.pack("<4I", 0xFF000000, 0xFF000000, 0xFF000000, 0x00000000)
        bit_count = 8

    flags = DDSD.CAPS | DDSD.HEIGHT | DDSD.WIDTH | DDSD.PITCH | DDSD.PIXELFORMAT

    fp.write(
        o32(DDS_MAGIC)
        # header size, flags, height, width, pith, depth, mipmaps
        + struct.pack("<IIIIIII", 124, flags, im.height, im.width, (im.width * bit_count + 7) // 8, 0, 0, )
        + struct.pack("11I", *((0,) * 11))  # reserved
        + struct.pack("<IIII", 32, pixel_flags, 0, bit_count)  # pfsize, pfflags, fourcc, bitcount
        + rgba_mask  # dwRGBABitMask
        + struct.pack("<IIIII", DDSCAPS.TEXTURE, 0, 0, 0, 0)
    )
    if im.mode == 'LA':
        ImageFile._save(im, fp, [Image.Tile("raw", (0, 0) + im.size, 0, ('LA', 0, 1))])
    else:
        ImageFile._save(im, fp, [Image.Tile("raw", (0, 0) + im.size, 0, (im.mode[::-1], 0, 1))])


# fmt: on


def _accept(prefix):
    return prefix[:4] == b"DDS "


Image.register_open(DdsImageFile.format, DdsImageFile, _accept)
Image.register_save(DdsImageFile.format, _save)
Image.register_extension(DdsImageFile.format, ".dds")
