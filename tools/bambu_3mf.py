#!/usr/bin/env python3
"""Turn a design 3MF into a Bambu Studio project: printer, build plate and one Bambu PLA Basic
filament per part, so it opens ready to slice.

build_design.py merges the OpenSCAD part exports into a core-spec 3MF (one object, one named part
per colour). Bambu Studio opens that as "geometry only": no printer, every part on filament 1. This
rewrites it in the layout Bambu Studio itself saves:

  3D/3dmodel.model                  the object as components, centred on plate 1, standing on the bed
  3D/Objects/object_1.model         the part meshes, coordinates unchanged (mesh_check.py reads them)
  Metadata/model_settings.config    object and part names, the filament of each part, the plate
  Metadata/project_settings.config  printer, process and filament preset NAMES, filament colours,
                                    purge matrix and sparse infill

Bambu Studio looks each preset name up in its own system profiles and rebuilds that preset, keeping
only the keys listed in different_settings_to_system (here: the infill densities). So the file never
ships stale temperatures or G-code, and does not raise the "modified G-code" warning. Preset names
are from Bambu Studio 02.05 resources/profiles/BBL; every printer uses its 0.4 mm nozzle and the
0.20mm Standard process. Each part colour is snapped to the nearest Bambu PLA Basic colour
(CIEDE2000, list below and in OPENSCAD_DESIGNER_AGENT.md §4); parts that land on the same filament
share a slot.

The purge volumes are computed as Bambu Studio's "Re-calculate" does (ports of libslic3r
FlushVolCalc.cpp and FlushVolPredictor.cpp, 02.05). Without the matrix Bambu Studio pads its
2-filament default with zeros, so filaments 3+ would change with no purge at all.

Ported from the JavaScript exporter of the browser designers (Equation-Driven-Pots); colour
matching and purge volumes give identical results.

--slice then slices the project with the installed Bambu Studio (its command line, ~10 s) and
reports what the slicer says: warnings such as "floating regions" (a region that starts in mid-air),
print time and filament per colour. Exit code 1 on any slicing warning.

usage:
  python bambu_3mf.py model.3mf [more.3mf ...] [--printer H2C] [--infill 35] [--exact-colors] [--slice]
  python bambu_3mf.py model.3mf --out project.3mf
  python bambu_3mf.py --list-printers

Files are converted in place unless --out is given. A file this script wrote can be converted again,
e.g. for another printer: parts, names and filaments are read back from the project. A project saved
by Bambu Studio itself is refused (converting it would drop your edits) unless --force is given.
"""
import argparse, datetime, json, math, os, re, shutil, subprocess, sys, tempfile, zipfile
from xml.sax.saxutils import escape, unescape

# Bambu Lab PLA Basic, the only filaments the house designs use (same table as
# OPENSCAD_DESIGNER_AGENT.md §4). Keep the two in step.
PLA_BASIC_COLORS = [
    ('Jade White', '#FFFFFF'), ('Beige', '#F7E6DE'), ('Gold', '#E4BD68'), ('Silver', '#A6A9AA'),
    ('Gray', '#8E9089'), ('Bronze', '#847D48'), ('Brown', '#9D432C'), ('Cocoa Brown', '#6F5034'),
    ('Maroon Red', '#9D2235'), ('Red', '#C12E1F'), ('Magenta', '#EC008C'), ('Pink', '#F55A74'),
    ('Hot Pink', '#F5547C'), ('Orange', '#FF6A13'), ('Pumpkin Orange', '#FF9016'),
    ('Sunflower Yellow', '#FEC600'), ('Yellow', '#F4EE2A'), ('Bright Green', '#BECF00'),
    ('Bambu Green', '#00AE42'), ('Mistletoe Green', '#3F8E43'), ('Turquoise', '#00B1B7'),
    ('Cyan', '#0086D6'), ('Blue', '#0A2989'), ('Cobalt Blue', '#0056B8'), ('Purple', '#5E43B7'),
    ('Indigo Purple', '#482960'), ('Blue Gray', '#5B6579'), ('Light Gray', '#D1D3D5'),
    ('Dark Gray', '#545454'), ('Black', '#000000'),
]

# flush holds one (purge data set, minimum purge mm3) pair per nozzle, for the Standard nozzle:
# nozzle_flush_dataset, and nozzle_volume minus the default filament retraction when cutting
# (Plater.cpp get_min_flush_volumes).
PRINTERS = [
    dict(id='H2C', model='Bambu Lab H2C', process='0.20mm Standard @BBL H2C', filament='Bambu PLA Basic @BBL H2C', flush=[(1, 96), (1, 111)], bed=(330, 320), height=325),
    dict(id='H2D', model='Bambu Lab H2D', process='0.20mm Standard @BBL H2D', filament='Bambu PLA Basic @BBL H2D', flush=[(1, 130), (1, 145)], bed=(350, 320), height=325),
    dict(id='H2DP', model='Bambu Lab H2D Pro', process='0.20mm Standard @BBL H2DP', filament='Bambu PLA Basic @BBL H2DP', flush=[(1, 130), (1, 145)], bed=(350, 320), height=325),
    dict(id='H2S', model='Bambu Lab H2S', process='0.20mm Standard @BBL H2S', filament='Bambu PLA Basic @BBL H2S', flush=[(1, 145)], bed=(340, 320), height=340),
    dict(id='X1C', model='Bambu Lab X1 Carbon', process='0.20mm Standard @BBL X1C', filament='Bambu PLA Basic @BBL X1C', flush=[(0, 63)], bed=(256, 256), height=250),
    dict(id='X1E', model='Bambu Lab X1E', process='0.20mm Standard @BBL X1C', filament='Bambu PLA Basic @BBL X1C', flush=[(0, 107)], bed=(256, 256), height=250),
    dict(id='P2S', model='Bambu Lab P2S', process='0.20mm Standard @BBL P2S', filament='Bambu PLA Basic @BBL P2S', flush=[(0, 110)], bed=(256, 256), height=256),
    dict(id='P1S', model='Bambu Lab P1S', process='0.20mm Standard @BBL X1C', filament='Bambu PLA Basic @BBL P1S 0.4 nozzle', flush=[(0, 63)], bed=(256, 256), height=250),
    dict(id='A1', model='Bambu Lab A1', process='0.20mm Standard @BBL A1', filament='Bambu PLA Basic @BBL A1', flush=[(0, 48)], bed=(256, 256), height=256),
    dict(id='A1M', model='Bambu Lab A1 mini', process='0.20mm Standard @BBL A1M', filament='Bambu PLA Basic @BBL A1M', flush=[(0, 48)], bed=(180, 180), height=180),
]
DEFAULT_PRINTER = 'H2C'
DEFAULT_INFILL = 35
# Written as the file's generator. From 2.0.0 on, Bambu Studio skips its pre-2.0 project migration,
# and keeping it at 2.0 means no 2.x install warns about a newer file. Also how this script tells
# its own output from a project saved by Bambu Studio (which writes its real version).
APP_VERSION = '02.00.00.00'
APPLICATION = f'BambuStudio-{APP_VERSION}'
# Bambu Studio keeps these three densities in step when sparse infill is edited.
INFILL_DENSITY_KEYS = ['skeleton_infill_density', 'skin_infill_density', 'sparse_infill_density']
NS_3MF_CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
NS_3MF_PRODUCTION = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
NS_BAMBU = 'http://schemas.bambulab.com/package/2021'
NS_RELATIONSHIPS = 'http://schemas.openxmlformats.org/package/2006/relationships'
REL_TYPE_3DMODEL = 'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
OBJECT_PATH = '/3D/Objects/object_1.model'


# ------------------------------------------------------------------ colours
def normalize_hex(hex_color):
    body = str(hex_color or '#FFFFFF').strip().lstrip('#')[:6]
    return '#' + body.upper() if re.fullmatch(r'[0-9A-Fa-f]{6}', body) else '#FFFFFF'


def hex_to_rgb01(hex_color):
    n = int(normalize_hex(hex_color)[1:], 16)
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]


def srgb_to_lab(hex_color):
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in hex_to_rgb01(hex_color)]
    x = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return [116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))]


def delta_e2000(lab1, lab2):
    """CIEDE2000. Plain Lab distance is badly skewed in the blues (it maps #0F4D80 to Blue Gray);
    this picks Cobalt Blue, as a person would."""
    rad = math.pi / 180
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    c_bar = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(c_bar ** 7 / (c_bar ** 7 + 25 ** 7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = (math.atan2(b1, a1p) / rad + 360) % 360
    h2p = (math.atan2(b2, a2p) / rad + 360) % 360
    chromaless = c1p * c2p == 0
    dhp = 0 if chromaless else h2p - h1p
    if dhp > 180:
        dhp -= 360
    elif dhp < -180:
        dhp += 360
    dLp, dCp = L2 - L1, c2p - c1p
    dHp = 2 * math.sqrt(c1p * c2p) * math.sin(dhp * rad / 2)
    l_bar_p, c_bar_p = (L1 + L2) / 2, (c1p + c2p) / 2
    h_bar_p = h1p + h2p
    if not chromaless:
        if abs(h1p - h2p) <= 180:
            h_bar_p /= 2
        else:
            h_bar_p = (h_bar_p + 360) / 2 if h_bar_p < 360 else (h_bar_p - 360) / 2
    t = (1 - 0.17 * math.cos((h_bar_p - 30) * rad) + 0.24 * math.cos(2 * h_bar_p * rad)
         + 0.32 * math.cos((3 * h_bar_p + 6) * rad) - 0.20 * math.cos((4 * h_bar_p - 63) * rad))
    d_theta = 30 * math.exp(-(((h_bar_p - 275) / 25) ** 2))
    rc = 2 * math.sqrt(c_bar_p ** 7 / (c_bar_p ** 7 + 25 ** 7))
    sl = 1 + 0.015 * (l_bar_p - 50) ** 2 / math.sqrt(20 + (l_bar_p - 50) ** 2)
    sc = 1 + 0.045 * c_bar_p
    sh = 1 + 0.015 * c_bar_p * t
    rt = -math.sin(2 * d_theta * rad) * rc
    return math.sqrt((dLp / sl) ** 2 + (dCp / sc) ** 2 + (dHp / sh) ** 2 + rt * (dCp / sc) * (dHp / sh))


def nearest_pla(hex_color):
    """(name, hex, delta E) of the closest PLA Basic colour."""
    target = srgb_to_lab(normalize_hex(hex_color))
    return min(((name, h, delta_e2000(target, srgb_to_lab(h))) for name, h in PLA_BASIC_COLORS),
               key=lambda c: c[2])


# ------------------------------------------------------------------ purge volumes
# A colour pair is first looked up in Bambu's measured tables (resources/flush/
# flush_data_standard.txt for data set 0, flush_data_dual_standard.txt for data set 1). Each colour is
# snapped to the first table colour within CIEDE2000 5. On a miss, an HSV formula is used instead.
# Entries are FROM (6 hex) + TO (6 hex) + purge mm3.
FLUSH_TABLES = {
    0: (
        '000000 C12E1F 00AE42 545454 D1D3D5 5B6579 F4EE2A 9D432C 5E43B7 0A2989 FF6A13 8E9089',
        '000000F4EE2A450 0000005E43B7330 C12E1FF4EE2A420 C12E1FFF6A13210 00AE42D1D3D5330 00AE42F4EE2A240 '
        '00AE42FF6A13270 54545400AE42180 545454D1D3D5240 545454F4EE2A270 5454545E43B7120 545454FF6A13300 '
        '5454548E9089120 D1D3D5F4EE2A120 D1D3D5FF6A13150 5B6579C12E1F120 5B657900AE4290 5B6579D1D3D5120 '
        '5B6579F4EE2A180 5B65799D432C120 5B65790A298990 5B6579FF6A13180 5B65798E908990 F4EE2A000000120 '
        'F4EE2AC12E1F90 F4EE2A00AE42150 F4EE2A9D432C150 F4EE2AFF6A1390 9D432C00AE42240 9D432CD1D3D5300 '
        '9D432CF4EE2A270 9D432CFF6A13180 9D432C8E9089210 5E43B700AE42180 5E43B7D1D3D5270 5E43B7F4EE2A270 '
        '5E43B79D432C150 5E43B7FF6A13270 5E43B78E9089210 0A2989C12E1F330 0A298900AE42210 0A2989545454150 '
        '0A2989D1D3D5450 0A29895B6579240 0A29899D432C270 0A29895E43B7180 0A2989FF6A13390 0A29898E9089270 '
        'FF6A13C12E1F90 FF6A13D1D3D5210 FF6A13F4EE2A210 FF6A139D432C120 FF6A138E9089180 8E9089C12E1F150 '
        '8E908900AE42120 8E9089D1D3D5150 8E9089F4EE2A270 8E9089FF6A13150'
    ),
    1: (
        '000000 FFFFFF 545454 8E9089 C12E1F F4EE2A 0086D6 F7E6DE 00AE42 5E43B7 482960 0056B8 FEC600 EC008C F5547C 6F5034 FF9016 00B1B7 BECF00',
        '000000FFFFFF900 000000545454450 0000008E9089540 000000C12E1F600 000000F4EE2A900 0000000086D6570 '
        '000000F7E6DE900 00000000AE42810 0000005E43B7480 000000482960270 0000000056B8540 000000FEC600900 '
        '000000EC008C900 000000F5547C900 000000FF9016900 00000000B1B7630 000000BECF00900 FFFFFF00000090 '
        'FFFFFF545454240 FFFFFF8E9089120 FFFFFFC12E1F90 FFFFFFF4EE2A90 FFFFFF0086D690 FFFFFFF7E6DE90 '
        'FFFFFF00AE42120 FFFFFF5E43B790 FFFFFF0056B890 FFFFFFFEC600150 FFFFFFEC008C150 FFFFFFF5547C120 '
        'FFFFFF6F5034120 FFFFFFFF9016120 FFFFFF00B1B7120 FFFFFFBECF0090 54545400000090 545454FFFFFF360 '
        '5454548E9089120 545454C12E1F270 545454F4EE2A330 5454540086D6270 545454F7E6DE390 54545400AE42270 '
        '5454545E43B7120 545454482960150 5454540056B8180 545454FEC600300 545454EC008C240 545454F5547C300 '
        '5454546F5034120 545454FF9016240 54545400B1B7270 545454BECF00300 8E9089000000270 8E9089FFFFFF330 '
        '8E9089545454300 8E9089C12E1F240 8E9089F4EE2A240 8E90890086D6240 8E9089F7E6DE390 8E908900AE42210 '
        '8E90895E43B7270 8E9089482960300 8E90890056B8180 8E9089FEC600240 8E9089EC008C240 8E9089F5547C240 '
        '8E90896F5034210 8E9089FF9016240 8E908900B1B7210 8E9089BECF00270 C12E1F000000150 C12E1FFFFFFF900 '
        'C12E1F545454300 C12E1F8E9089570 C12E1FF4EE2A450 C12E1F0086D6390 C12E1FF7E6DE630 C12E1F00AE42420 '
        'C12E1F5E43B7330 C12E1F482960210 C12E1F0056B8300 C12E1FFEC600660 C12E1FEC008C240 C12E1FF5547C180 '
        'C12E1F6F5034210 C12E1FFF9016270 C12E1F00B1B7540 C12E1FBECF00360 F4EE2A000000150 F4EE2AFFFFFF900 '
        'F4EE2A545454390 F4EE2A8E9089450 F4EE2AC12E1F180 F4EE2A0086D6270 F4EE2AF7E6DE570 F4EE2A00AE42120 '
        'F4EE2A5E43B7330 F4EE2A482960330 F4EE2A0056B8240 F4EE2AFEC60090 F4EE2AEC008C330 F4EE2AF5547C420 '
        'F4EE2A6F5034240 F4EE2AFF9016150 F4EE2A00B1B7360 F4EE2ABECF00240 0086D6000000150 0086D6FFFFFF420 '
        '0086D6545454120 0086D68E9089480 0086D6C12E1F240 0086D6F4EE2A360 0086D6F7E6DE390 0086D600AE42120 '
        '0086D65E43B7150 0086D6482960150 0086D60056B8120 0086D6EC008C330 0086D6F5547C330 0086D66F5034150 '
        '0086D6FF9016300 0086D600B1B7150 0086D6BECF00270 F7E6DE00000090 F7E6DEFFFFFF90 F7E6DE545454120 '
        'F7E6DE8E9089120 F7E6DEC12E1F90 F7E6DEF4EE2A60 F7E6DE0086D690 F7E6DE00AE4290 F7E6DE5E43B790 '
        'F7E6DE482960120 F7E6DE0056B8120 F7E6DEFEC600120 F7E6DEEC008C150 F7E6DEF5547C120 F7E6DE6F5034150 '
        'F7E6DEFF9016120 F7E6DE00B1B790 F7E6DEBECF00120 00AE42000000150 00AE42FFFFFF900 00AE42545454240 '
        '00AE428E9089330 00AE42C12E1F210 00AE42F4EE2A270 00AE42F7E6DE360 00AE425E43B7180 00AE42482960180 '
        '00AE420056B8240 00AE42FEC600300 00AE42EC008C300 00AE42F5547C390 00AE426F5034180 00AE42FF9016300 '
        '00AE4200B1B7360 00AE42BECF00270 5E43B700000090 5E43B7FFFFFF630 5E43B7545454150 5E43B78E9089210 '
        '5E43B7C12E1F210 5E43B7F4EE2A330 5E43B70086D6180 5E43B7F7E6DE510 5E43B700AE42240 5E43B7482960150 '
        '5E43B70056B8120 5E43B7FEC600540 5E43B7EC008C270 5E43B7F5547C420 5E43B76F5034150 5E43B7FF9016330 '
        '5E43B700B1B7270 5E43B7BECF00330 48296000000090 482960FFFFFF900 482960545454240 4829608E9089510 '
        '482960C12E1F360 482960F4EE2A420 4829600086D6330 482960F7E6DE510 48296000AE42390 4829605E43B7270 '
        '4829600056B8300 482960FEC600660 482960EC008C360 482960F5547C510 4829606F5034180 482960FF9016540 '
        '48296000B1B7450 482960BECF00600 0056B800000090 0056B8FFFFFF780 0056B8545454270 0056B88E9089270 '
        '0056B8C12E1F330 0056B8F4EE2A630 0056B80086D6180 0056B8F7E6DE840 0056B800AE42270 0056B85E43B7270 '
        '0056B8482960150 0056B8FEC600630 0056B8EC008C450 0056B86F5034240 0056B8FF9016510 0056B800B1B7240 '
        '0056B8BECF00510 FEC60000000090 FEC600FFFFFF900 FEC600545454390 FEC6008E9089600 FEC600C12E1F180 '
        'FEC600F4EE2A150 FEC6000086D6330 FEC600F7E6DE600 FEC60000AE42180 FEC6005E43B7270 FEC600482960330 '
        'FEC6000056B8300 FEC600EC008C390 FEC600F5547C570 FEC6006F5034240 FEC600FF9016150 FEC60000B1B7510 '
        'FEC600BECF00300 EC008C00000090 EC008CFFFFFF900 EC008C545454240 EC008C8E9089270 EC008CC12E1F120 '
        'EC008CF4EE2A360 EC008C0086D6270 EC008CF7E6DE660 EC008C00AE42330 EC008C5E43B7270 EC008C482960270 '
        'EC008C0056B8210 EC008CFEC600510 EC008CF5547C120 EC008C6F5034180 EC008C00B1B7360 EC008CBECF00570 '
        'F5547C00000090 F5547CFFFFFF900 F5547C545454180 F5547C8E9089180 F5547CC12E1F150 F5547CF4EE2A270 '
        'F5547C0086D6270 F5547CF7E6DE540 F5547C00AE42300 F5547C5E43B7210 F5547C482960240 F5547C0056B8210 '
        'F5547CFEC600330 F5547CEC008C120 F5547C6F5034180 F5547CFF9016150 F5547C00B1B7300 F5547CBECF00330 '
        '6F5034000000180 6F5034FFFFFF660 6F5034545454180 6F50348E9089240 6F5034C12E1F240 6F5034F4EE2A390 '
        '6F50340086D6330 6F5034F7E6DE420 6F503400AE42300 6F50345E43B7300 6F5034482960180 6F50340056B8300 '
        '6F5034FEC600270 6F5034EC008C210 6F5034F5547C240 6F5034FF9016240 6F503400B1B7270 6F5034BECF00360 '
        'FF9016FFFFFF900 FF9016545454240 FF90168E9089270 FF9016C12E1F150 FF9016F4EE2A330 FF90160086D6240 '
        'FF9016F7E6DE390 FF901600AE42240 FF90165E43B7270 FF9016482960180 FF90160056B8240 FF9016FEC600210 '
        'FF9016EC008C210 FF9016F5547C210 FF90166F5034180 FF901600B1B7300 FF9016BECF00270 00B1B7000000210 '
        '00B1B7FFFFFF480 00B1B7545454300 00B1B78E9089180 00B1B7C12E1F300 00B1B7F4EE2A300 00B1B70086D6150 '
        '00B1B7F7E6DE390 00B1B700AE42120 00B1B75E43B7270 00B1B7482960270 00B1B70056B8150 00B1B7FEC600330 '
        '00B1B7EC008C270 00B1B7F5547C270 00B1B76F5034210 00B1B7FF9016270 00B1B7BECF00240 BECF00000000270 '
        'BECF00FFFFFF450 BECF00545454270 BECF008E9089270 BECF00C12E1F150 BECF00F4EE2A90 BECF000086D6300 '
        'BECF00F7E6DE300 BECF0000AE42180 BECF005E43B7270 BECF00482960210 BECF000056B8240 BECF00FEC600210 '
        'BECF00EC008C240 BECF00F5547C150 BECF006F5034150 BECF00FF9016150 BECF0000B1B7270'
    ),
}
MAX_FLUSH_VOLUME = 900
MIN_FORMULA_FLUSH = 60
_flush_cache = {}


def _flush_table(dataset):
    if dataset not in _flush_cache:
        colors_src, pairs_src = FLUSH_TABLES[dataset]
        colors = ['#' + c for c in colors_src.split()]
        volumes = {(f'#{e[:6]}', f'#{e[6:12]}'): int(e[12:]) for e in pairs_src.split()}
        _flush_cache[dataset] = (colors, [srgb_to_lab(c) for c in colors], volumes)
    return _flush_cache[dataset]


def _lookup_flush(dataset, from_hex, to_hex):
    colors, labs, volumes = _flush_table(dataset)

    def snap(hex_color):
        lab = srgb_to_lab(hex_color)
        return next((c for c, l in zip(colors, labs) if delta_e2000(l, lab) <= 5), None)
    a, b = snap(from_hex), snap(to_hex)
    return volumes.get((a, b)) if a and b else None


def _rgb_to_hsv(r, g, b):
    """RGB2HSV from ColorSpaceConvert.cpp: hue in degrees, can be negative (fmod keeps the sign)."""
    cmax = max(r, g, b)
    delta = cmax - min(r, g, b)
    if abs(delta) < 0.001:
        h = 0.0
    elif cmax == r:
        h = 60 * math.fmod((g - b) / delta, 6)
    elif cmax == g:
        h = 60 * ((b - r) / delta + 2)
    else:
        h = 60 * ((r - g) / delta + 4)
    return h, (0.0 if abs(cmax) < 0.001 else delta / cmax), cmax


def _formula_flush(from_hex, to_hex):
    """FlushVolCalculator::calc_flush_vol_rgb without its table lookup."""
    rad = math.pi / 180
    src, dst = hex_to_rgb01(from_hex), hex_to_rgb01(to_hex)
    h1, s1, v1 = _rgb_to_hsv(*src)
    h2, s2, v2 = _rgb_to_hsv(*dst)
    hs_dist = min(1.2, math.hypot(math.cos(h1 * rad) * s1 * v1 - math.cos(h2 * rad) * s2 * v2,
                                  math.sin(h1 * rad) * s1 * v1 - math.sin(h2 * rad) * s2 * v2))
    lum = lambda c: c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11
    from_lumi, to_lumi = lum(src), lum(dst)
    if to_lumi >= from_lumi:
        lumi_flush = (to_lumi - from_lumi) ** 0.7 * 560
    else:
        lumi_flush = (from_lumi - to_lumi) * 80
        hs_dist = min(0.67 * v2 + 0.33 * v1, hs_dist)
    hs_flush = 230 * hs_dist
    flush = math.sqrt(hs_flush ** 2 + lumi_flush ** 2 - 2 * hs_flush * lumi_flush * math.cos(120 * rad))
    return max(flush, MIN_FORMULA_FLUSH)


def flush_volume(from_hex, to_hex, dataset, min_flush):
    """FlushVolCalculator::calc_flush_vol for opaque colours."""
    flush = _lookup_flush(dataset, from_hex, to_hex) if dataset != 0 else None
    if flush is None:
        measured = _lookup_flush(0, from_hex, to_hex) if dataset == 0 else None
        flush = math.trunc(measured if measured is not None else _formula_flush(from_hex, to_hex))
        # Bambu tests 0-255 channel luminance against 0-1 thresholds here, so in practice this
        # fires for any non-black colour followed by black.
        lum255 = lambda h: sum(c * 255 * w for c, w in zip(hex_to_rgb01(h), (0.3, 0.59, 0.11)))
        if dataset != 0 and lum255(from_hex) > 180 / 255 and lum255(to_hex) < 75 / 255:
            flush *= 1.3
        flush += min_flush
    return min(math.trunc(flush), MAX_FLUSH_VOLUME)


def flush_matrix(printer, hexes):
    """Row = from, column = to, one n x n block per nozzle, as flush_volumes_matrix stores it."""
    return [str(0 if i == j else flush_volume(a, b, dataset, min_flush))
            for dataset, min_flush in printer['flush']
            for i, a in enumerate(hexes) for j, b in enumerate(hexes)]


# ------------------------------------------------------------------ project settings
def project_settings(printer, filaments, infill):
    n = len(filaments)
    per_nozzle = lambda v: [v] * len(printer['flush'])
    bed_w, bed_d = printer['bed']
    hexes = [f['hex'] for f in filaments]
    settings = dict(
        name='project_settings', **{'from': 'project'}, version=APP_VERSION,
        printer_model=printer['model'],
        printer_settings_id=f"{printer['model']} 0.4 nozzle",
        print_settings_id=printer['process'],
        # Per-nozzle keys, sized to the printer. On a dual-nozzle printer Bambu Studio drops the
        # whole config unless extruder_type matches nozzle_diameter, and it reads
        # nozzle_volume_type once per nozzle after loading.
        nozzle_diameter=per_nozzle('0.4'),
        extruder_type=per_nozzle('Direct Drive'),
        nozzle_volume_type=per_nozzle('Standard'),
        printable_area=['0x0', f'{bed_w}x0', f'{bed_w}x{bed_d}', f'0x{bed_d}'],
        printable_height=str(printer['height']),
        filament_settings_id=[printer['filament']] * n,
        filament_colour=hexes,
        filament_multi_colour=hexes,
        filament_type=['PLA'] * n,
        filament_vendor=['Bambu Lab'] * n,
        filament_ids=['GFA00'] * n,
        filament_diameter=['1.75'] * n,
        # One extruder variant per slot. Bambu Studio rejects the config as invalid unless
        # filament_self_index lines up with this list entry for entry.
        filament_extruder_variant=['Direct Drive Standard'] * n,
        filament_self_index=[str(i + 1) for i in range(n)],
        # One multiplier per nozzle, so Bambu Studio reads the matrix as n x n per nozzle and keeps
        # it instead of resizing it.
        flush_volumes_matrix=flush_matrix(printer, hexes),
        flush_multiplier=per_nozzle('1'),
    )
    settings.update({key: f'{infill}%' for key in INFILL_DENSITY_KEYS})
    # Entries are print, filaments..., printer. Empty means "the system preset, unchanged". A key
    # missing from the print entry would be reset to the system value on load, so the infill
    # densities are listed there. The process then opens as a modified copy of its system preset,
    # as if edited by hand.
    settings['inherits_group'] = [''] * (n + 2)
    settings['different_settings_to_system'] = [';'.join(INFILL_DENSITY_KEYS)] + [''] * (n + 1)
    settings['curr_bed_type'] = 'Textured PEI Plate'
    return settings


# ------------------------------------------------------------------ reading
MESH_RE = re.compile(r'<object\b([^>]*)>\s*<mesh>(.*?)</mesh>', re.S)
VERTEX_RE = re.compile(r'<vertex\s+x="([^"]+)"\s+y="([^"]+)"\s+z="([^"]+)"')
TRIANGLE_RE = re.compile(r'<triangle\s+v1="(\d+)"\s+v2="(\d+)"\s+v3="(\d+)"')


def _attrs(tag_body):
    return dict(re.findall(r'([\w:]+)="([^"]*)"', tag_body))


def _mesh(body):
    return VERTEX_RE.findall(body), TRIANGLE_RE.findall(body)


def read_design(path, force=False):
    """(title, [dict(name, color, verts, tris)]) from a core-spec 3MF (build_design.py /
    merge_3mf.py / a plain OpenSCAD export) or from a project this script wrote."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        root = z.read('3D/3dmodel.model').decode('utf-8')
        title_m = re.search(r'<metadata name="Title">(.*?)</metadata>', root, re.S)
        title = unescape(title_m.group(1).strip()) if title_m else ''
        if 'Metadata/project_settings.config' in names:
            app = re.search(r'<metadata name="Application">(.*?)</metadata>', root)
            if not force and (not app or app.group(1).strip() != APPLICATION):
                raise SystemExit(f'{path}: a project saved by Bambu Studio ({app.group(1) if app else "unknown"}); '
                                 'converting it would drop its edits. Use --force to convert anyway.')
            settings = json.loads(z.read('Metadata/project_settings.config'))
            colours = settings.get('filament_colour', [])
            model_settings = z.read('Metadata/model_settings.config').decode('utf-8')
            meshes = {}
            for entry in names:
                if entry.startswith('3D/') and entry.endswith('.model'):
                    for m in MESH_RE.finditer(z.read(entry).decode('utf-8')):
                        meshes[_attrs(m.group(1)).get('id')] = _mesh(m.group(2))
            obj = re.search(r'<object id="\d+">\s*<metadata key="name" value="([^"]*)"', model_settings)
            title = title or (unescape(obj.group(1)) if obj else '')
            parts = []
            for pid, body in re.findall(r'<part id="(\d+)"[^>]*>(.*?)</part>', model_settings, re.S):
                meta = dict(re.findall(r'<metadata key="(\w+)" value="([^"]*)"', body))
                slot = int(meta.get('extruder', '1'))
                verts, tris = meshes[pid]
                parts.append(dict(name=unescape(meta.get('name', f'Part {pid}')),
                                  color=colours[slot - 1] if slot <= len(colours) else '#FFFFFF',
                                  verts=verts, tris=tris))
        else:
            bases = {m.group(1): [normalize_hex(_attrs(b).get('displaycolor', '#FFFFFF'))
                                  for b in re.findall(r'<base\b([^>]*)/>', m.group(2))]
                     for m in re.finditer(r'<basematerials id="(\d+)">(.*?)</basematerials>', root, re.S)}
            parts = []
            for m in MESH_RE.finditer(root):
                a = _attrs(m.group(1))
                color = None
                if a.get('pid') in bases:
                    color = bases[a['pid']][int(a.get('pindex', 0))]
                verts, tris = _mesh(m.group(2))
                parts.append(dict(name=unescape(a.get('name', '')), color=color, verts=verts, tris=tris))
            if not title:
                holder = re.search(r'<object\b([^>]*)>\s*<components>', root)
                title = unescape(_attrs(holder.group(1)).get('name', '')) if holder else ''
    title = title or os.path.splitext(os.path.basename(path))[0].replace('_', ' ')
    for k, p in enumerate(parts):
        if not p['name'] or p['name'] == 'OpenSCAD Model':
            p['name'] = title if len(parts) == 1 else f'Part {k + 1}'
        if not p['verts'] or not p['tris']:
            raise SystemExit(f'{path}: part "{p["name"]}" has no mesh')
    if not parts:
        raise SystemExit(f'{path}: no meshes found')
    return title, parts


# ------------------------------------------------------------------ writing
def assign_filaments(parts, exact):
    """One filament slot per distinct printed colour, in part order; colours that land on the same
    filament share a slot, so the printer never swaps to an identical spool."""
    filaments, slot_of = [], {}
    for p in parts:
        key = normalize_hex(p['color'] or '#FFFFFF')
        if key not in slot_of:
            name, hex_color, de = (None, key, 0.0) if exact else nearest_pla(key)
            slot = next((i for i, f in enumerate(filaments) if f['hex'] == hex_color), None)
            if slot is None:
                filaments.append(dict(name=name, hex=hex_color, de=de, source=key))
                slot = len(filaments) - 1
            slot_of[key] = slot + 1
        p['extruder'] = slot_of[key]
    return filaments


def _model_header():
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
            f'xmlns="{NS_3MF_CORE}" xmlns:BambuStudio="{NS_BAMBU}" xmlns:p="{NS_3MF_PRODUCTION}" '
            f'requiredextensions="p">')


def _mesh_xml(obj_id, part):
    out = [f'  <object id="{obj_id}" type="model" name="{escape(part["name"], {chr(34): "&quot;"})}">',
           '   <mesh>', '    <vertices>']
    out += [f'     <vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in part['verts']]
    out += ['    </vertices>', '    <triangles>']
    out += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in part['tris']]
    out += ['    </triangles>', '   </mesh>', '  </object>']
    return '\n'.join(out)


def write_project(out_path, title, parts, printer, filaments, infill):
    q = lambda s: escape(str(s), {'"': '&quot;'})
    part_ids = list(range(1, len(parts) + 1))
    assembly_id = len(parts) + 1
    lo = [min(float(v[k]) for p in parts for v in p['verts']) for k in range(3)]
    hi = [max(float(v[k]) for p in parts for v in p['verts']) for k in range(3)]
    bed_w, bed_d = printer['bed']
    # Centre the object on plate 1 and stand it on the bed; the meshes keep their own coordinates.
    tx, ty, tz = bed_w / 2 - (lo[0] + hi[0]) / 2, bed_d / 2 - (lo[1] + hi[1]) / 2, 0.0 - lo[2]
    header = _model_header()
    components = '\n'.join(f'    <component p:path="{OBJECT_PATH}" objectid="{i}" '
                           f'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>' for i in part_ids)
    root_model = f'''{header}
 <metadata name="Application">{APPLICATION}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="CreationDate">{datetime.date.today().isoformat()}</metadata>
 <metadata name="Title">{q(title)}</metadata>
 <resources>
  <object id="{assembly_id}" type="model">
   <components>
{components}
   </components>
  </object>
 </resources>
 <build>
  <item objectid="{assembly_id}" transform="1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} {tz:.4f}" printable="1"/>
 </build>
</model>'''
    object_model = (f'{header}\n <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                    + '\n'.join(_mesh_xml(i, p) for i, p in zip(part_ids, parts))
                    + '\n </resources>\n <build/>\n</model>')
    part_cfg = '\n'.join(f'''    <part id="{i}" subtype="normal_part">
      <metadata key="name" value="{q(p['name'])}"/>
      <metadata key="extruder" value="{p['extruder']}"/>
    </part>''' for i, p in zip(part_ids, parts))
    model_settings = f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="{assembly_id}">
    <metadata key="name" value="{q(title)}"/>
    <metadata key="extruder" value="{parts[0]['extruder']}"/>
{part_cfg}
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="{q(title)}"/>
    <metadata key="locked" value="false"/>
    <model_instance>
      <metadata key="object_id" value="{assembly_id}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{assembly_id}"/>
    </model_instance>
  </plate>
</config>'''
    files = {
        '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            '</Types>',
        '_rels/.rels': f'<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="{NS_RELATIONSHIPS}">\n'
            f' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{REL_TYPE_3DMODEL}"/>\n</Relationships>',
        '3D/3dmodel.model': root_model,
        '3D/_rels/3dmodel.model.rels': f'<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="{NS_RELATIONSHIPS}">\n'
            f' <Relationship Target="{OBJECT_PATH}" Id="rel-1" Type="{REL_TYPE_3DMODEL}"/>\n</Relationships>',
        OBJECT_PATH[1:]: object_model,
        'Metadata/model_settings.config': model_settings,
        'Metadata/project_settings.config': json.dumps(project_settings(printer, filaments, infill), indent=4),
    }
    # Write next to the target and swap it in, so a failure never leaves half a file behind.
    fd, tmp = tempfile.mkstemp(suffix='.3mf', dir=os.path.dirname(os.path.abspath(out_path)))
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for name, text in files.items():
                z.writestr(name, text)
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    size = [h - l for l, h in zip(lo, hi)]
    return size, size[0] <= bed_w and size[1] <= bed_d and size[2] <= printer['height']


def convert(src, dst=None, printer_id=DEFAULT_PRINTER, infill=DEFAULT_INFILL, exact=False, force=False):
    """Rewrite src as a Bambu Studio project (in place unless dst). Returns summary lines."""
    printer = next((p for p in PRINTERS if p['id'].lower() == str(printer_id).lower()), None)
    if printer is None:
        raise SystemExit(f'unknown printer {printer_id!r}; one of: {", ".join(p["id"] for p in PRINTERS)}')
    infill = min(100, max(0, int(round(float(infill)))))
    title, parts = read_design(src, force)
    filaments = assign_filaments(parts, exact)
    size, fits = write_project(dst or src, title, parts, printer, filaments, infill)
    lines = [f'Bambu Studio project for {printer["model"]} (0.4 nozzle, 0.20mm Standard, {infill}% sparse infill): '
             f'{dst or src}',
             f'  plate 1: {title}, {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm'
             + ('' if fits else f'  EXCEEDS the {printer["model"]} build volume')]
    for p in parts:
        f = filaments[p['extruder'] - 1]
        label = f['name'] or 'exact colour'
        note = '' if f['source'] == f['hex'] else f'  (from {f["source"]}, delta E {f["de"]:.1f})'
        lines.append(f'  {p["name"]:<14} filament {p["extruder"]}  Bambu PLA Basic {label} {f["hex"]}{note}')
    return lines


# ------------------------------------------------------------------ slicing with Bambu Studio
def bambu_studio_exe():
    for p in (os.environ.get('BAMBU_STUDIO'), r'C:\Program Files\Bambu Studio\bambu-studio.exe',
              shutil.which('bambu-studio')):
        if p and os.path.exists(p):
            return p
    return None


def _system_preset(profiles, kind, name):
    """A Bambu system preset with its inherits chain folded in. The command line needs complete
    presets: without them it looks for machine_full/ files a desktop install does not have, and
    crashes."""
    with open(os.path.join(profiles, kind, name + '.json'), encoding='utf-8') as f:
        d = json.load(f)
    full = _system_preset(profiles, kind, d['inherits']) if d.get('inherits') else {}
    full.update(d)
    full.pop('inherits', None)
    full['name'], full['from'] = name, 'system'
    return full


def slice_check(path, exe=None):
    """Slice a project written by this script with Bambu Studio's command line, using the same
    system presets plus the project's own edits (the infill). Returns (ok, lines); ok is None when
    Bambu Studio is not installed."""
    exe = exe or bambu_studio_exe()
    if not exe:
        return None, ['slicer check skipped: Bambu Studio not found (set $BAMBU_STUDIO)']
    with zipfile.ZipFile(path) as z:
        ps = json.loads(z.read('Metadata/project_settings.config'))
    profiles = os.path.join(os.path.dirname(exe), 'resources', 'profiles', 'BBL')
    tmp = tempfile.mkdtemp(prefix='bambu_slice_')
    try:
        process = _system_preset(profiles, 'process', ps['print_settings_id'])
        for key in filter(None, ps.get('different_settings_to_system', [''])[0].split(';')):
            if key in ps:
                process[key] = ps[key]
        presets = {'machine.json': _system_preset(profiles, 'machine', ps['printer_settings_id']),
                   'process.json': process}
        filament_files = []
        for name in ps['filament_settings_id']:
            fn = next((k for k, p in presets.items() if k.startswith('filament') and p['name'] == name), None)
            if fn is None:
                fn = f'filament_{len(presets)}.json'
                presets[fn] = _system_preset(profiles, 'filament', name)
            filament_files.append(fn)
        for fn, preset in presets.items():
            with open(os.path.join(tmp, fn), 'w', encoding='utf-8') as f:
                json.dump(preset, f)
        r = subprocess.run([exe, '--debug', '2', '--slice', '0', '--outputdir', tmp,
                            '--load-settings', 'machine.json;process.json',
                            '--load-filaments', ';'.join(filament_files), os.path.abspath(path)],
                           cwd=tmp, capture_output=True, text=True, errors='replace', timeout=1800)
        log = r.stdout + r.stderr
        gcode = os.path.join(tmp, 'plate_1.gcode')
        head = ''
        if os.path.exists(gcode):
            with open(gcode, encoding='utf-8', errors='replace') as f:
                head = f.read(200000)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    version = re.search(r'BambuStudio Version (\S+)', log)
    warnings = [m.group(1).strip() for m in re.finditer(r'slicing warnings: (.*)', log)]
    ok = r.returncode == 0 and bool(head) and not warnings
    lines = [f'Bambu Studio {version.group(1) if version else ""} sliced plate 1 for {ps["printer_model"]}'
             + ('' if head else f': FAILED (exit code {r.returncode})')]
    t = re.search(r'; total estimated time: ([^\n;]+)', head)
    grams = re.search(r'; total filament weight \[g\] : ([\d.,]+)', head)
    if t:
        lines.append(f'  print time {t.group(1).strip()}, {ps.get("sparse_infill_density", "?")} sparse infill')
    if grams:
        g = [float(x) for x in grams.group(1).split(',')]
        lines.append('  filament ' + ', '.join(f'{w:.1f} g {c}' for w, c in zip(g, ps['filament_colour']))
                     + f'  (total {sum(g):.0f} g)')
    lines += [f'  WARNING: {w}' for w in warnings]
    lines.append(f'  {"PASS" if ok else "FAIL"}: slicer check')
    return ok, lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='*', help='3MF files to convert (in place unless --out)')
    ap.add_argument('--printer', default=DEFAULT_PRINTER, help=f'printer id (default {DEFAULT_PRINTER}); see --list-printers')
    ap.add_argument('--infill', type=float, default=DEFAULT_INFILL, help=f'sparse infill %% (default {DEFAULT_INFILL})')
    ap.add_argument('--exact-colors', action='store_true', help='keep the part colours as they are instead of snapping to PLA Basic')
    ap.add_argument('--out', help='output file (one input only)')
    ap.add_argument('--force', action='store_true', help='also convert a project saved by Bambu Studio')
    ap.add_argument('--slice', action='store_true', help='slice with the installed Bambu Studio and report its warnings')
    ap.add_argument('--list-printers', action='store_true')
    a = ap.parse_args()
    if a.list_printers:
        for p in PRINTERS:
            print(f'{p["id"]:<5} {p["model"]:<20} bed {p["bed"][0]} x {p["bed"][1]} x {p["height"]} mm, '
                  f'{len(p["flush"])} nozzle{"s" if len(p["flush"]) > 1 else ""}')
        return
    if not a.files:
        ap.error('no input files')
    if a.out and len(a.files) > 1:
        ap.error('--out takes one input file')
    failed = False
    for f in a.files:
        print('\n'.join(convert(f, a.out, a.printer, a.infill, a.exact_colors, a.force)))
        if a.slice:
            ok, lines = slice_check(a.out or f)
            print('\n'.join(lines))
            failed |= ok is False
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
