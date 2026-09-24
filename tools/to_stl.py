#!/usr/bin/env python3
"""Write a mesh (3MF or STL) as one binary STL, for slicers other than Bambu Studio.

OpenSCAD's own ASCII STL keeps 6 significant digits. Where two surfaces meet at a grazing angle
(a fork leaving its parent), vertices 1e-4 mm apart come out as one, which can leave a
non-manifold edge that the exact mesh does not have. Export a 3MF from OpenSCAD instead (full
precision) and convert it with this: binary STL stores float32, about 1e-5 mm at these sizes.
All parts of a multi-part 3MF are written into the one STL.

usage:
  python to_stl.py model.3mf model.stl
"""
import os, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesh_check import load  # noqa: E402


def write_stl(path, parts, name=b'OpenSCAD'):
    tris = np.concatenate([V[F] for _, V, F in parts]).astype(np.float64)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    rec = np.zeros(len(tris), dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    rec['n'] = n
    rec['v'] = tris.reshape(-1, 9)
    with open(path, 'wb') as f:
        f.write(name.ljust(80, b' ')[:80])
        f.write(struct.pack('<I', len(tris)))
        f.write(rec.tobytes())
    return len(tris)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    n = write_stl(sys.argv[2], load(sys.argv[1]))
    print(f'wrote {sys.argv[2]}: {n} triangles')
