#!/usr/bin/env python3
"""Merge single-mesh 3MF exports (OpenSCAD writes one mesh per file) into one
multi-part 3MF: a single object whose components are the named parts.

Bambu Studio, Orca Slicer and PrusaSlicer load the result as ONE object with
several parts, each of which can be given its own filament. Coordinates are
kept exactly as exported, so parts exported from the same .scad line up.

usage:
  python merge_3mf.py out.3mf "Object Name" Bark=bark.3mf=#6F5034 Leaves=leaves.3mf=#3F8E43
"""
import re, sys, zipfile
from xml.sax.saxutils import escape

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    '</Types>')
RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')


def read_mesh(path):
    xml = zipfile.ZipFile(path).read('3D/3dmodel.model').decode()
    meshes = re.findall(r'<mesh>.*?</mesh>', xml, re.S)
    if len(meshes) != 1:
        raise SystemExit(f'{path}: expected exactly one mesh, found {len(meshes)}')
    return meshes[0]


def merge(out_path, obj_name, parts):
    """parts: list of (name, path, '#RRGGBB')."""
    bases, objects = [], []
    for k, (name, path, color) in enumerate(parts):
        bases.append(f'<base name="{escape(name)}" displaycolor="{color.upper()}FF"/>')
        objects.append(f'<object id="{k + 2}" type="model" name="{escape(name)}" pid="1" pindex="{k}">'
                       f'{read_mesh(path)}</object>')
    top = len(parts) + 2
    comps = ''.join(f'<component objectid="{k + 2}"/>' for k in range(len(parts)))
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{escape(obj_name)}</metadata>'
             f'<resources><basematerials id="1">{"".join(bases)}</basematerials>'
             + ''.join(objects) +
             f'<object id="{top}" type="model" name="{escape(obj_name)}"><components>{comps}</components></object>'
             f'</resources><build><item objectid="{top}"/></build></model>')
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES)
        z.writestr('_rels/.rels', RELS)
        z.writestr('3D/3dmodel.model', model)


def parse_spec(spec):
    name, rest = spec.split('=', 1)
    path, color = rest.rsplit('=', 1)
    return name, path, color


if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    merge(sys.argv[1], sys.argv[2], [parse_spec(s) for s in sys.argv[3:]])
    print('wrote', sys.argv[1])
