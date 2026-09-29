"""Bill of materials with weights for the 1S Pi Zero drone.

    python Drones/1S_PiZero/1S_PiZero_bom.py

Writes, next to the design:
    1S_PiZero_BOM.xlsx  the working copy: every weight that is not from a datasheet is red
                        (Status "Estimate"). Weigh the part, type the value into "Unit (g)" and set
                        its Status to "Weighed": it turns black and every total updates (formulas).
    1S_PiZero_BOM.md    the same table for reading on GitHub, estimates in red
    1S_PiZero_BOM.csv   plain values

Where the numbers come from:
- Printed parts: the three print parts are exported from 1S_PiZero.scad in their print
  orientation, merged into one Bambu Studio project (one filament each), and sliced for the H2C at
  0.20 mm Standard, 35 % sparse infill, PLA Basic; each weight is the slicer's figure for that
  filament, i.e. for that part alone.
- PCB: the bare board, from the area of the exported outline (holes removed) x thickness x FR4
  density, plus copper on both layers at an assumed fill.
- Hardware and connectors: exactly as the design lists them (its hardware_list, echoed with
  echo_bom=true), each weighed from its own dimensions and material.
- Bought components: the weights in the user's BOM and the makers' pages; anything else is
  estimated from its size and material, and says how.
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', 'tools')
sys.path.insert(0, TOOLS)
from render_png import openscad_exe  # noqa: E402
import bambu_3mf  # noqa: E402
import merge_3mf  # noqa: E402

SCAD = os.path.join(HERE, '1S_PiZero.scad')
INFILL = 35
FR4 = 1.85e-3                 # g/mm^3
COPPER = 8.96e-3
CU_T, CU_FILL = 0.035, 0.5    # 1 oz copper on both layers, half of the area kept

GIVEN, EST = 'Given', 'Estimate'

# category, item, qty, g each, status, basis / link
COMPONENTS = [
    ('Battery', 'Molicel INR-18650-P30B (1S)', 1, 48.0, GIVEN, 'https://www.molicel.com/inr-18650-p30b/'),
    ('Motor', 'RCINPOWER GTS V3 1203 11500 KV', 4, 4.5, GIVEN, 'https://www.rcinpower.com/G-SERIES/65.html'),
    ('Propeller', 'Gemfan 2520 Hurricane, 3-blade', 4, 1.0, GIVEN, 'https://www.gemfanhobby.com/2520-hurricane-pc-3-blade.html'),
    ('ESC', 'DYS XSD 7A (16.2 x 11 x 4 mm)', 4, 0.83, GIVEN, 'https://www.dys.hk/product/XSD%207A.html'),
    ('Flight controller', 'Bitcraze Crazyflie Bolt 1.1', 1, 9.2, GIVEN, 'https://www.bitcraze.io/products/crazyflie-bolt/'),
    ('Sensor deck', 'Bitcraze Flow deck v2', 1, 1.6, GIVEN, 'https://www.bitcraze.io/products/flow-deck-v2/'),
    ('Companion computer', 'Raspberry Pi Zero 2 W', 1, 9.0, EST,
     'size: FR4 65 x 30 x 1.4 mm = 5.0 g, + SiP/shield ~1.5 g, + mini HDMI, 2 x micro USB, SD, camera connectors ~2.5 g'),
    ('Camera', 'Waveshare RPi Zero v1.3 camera (flex, adhesive back)', 1, 0.8, EST,
     'size: lens module 8 x 8 x 5 mm ~0.4 g, + polyimide flex ~60 x 10 x 0.15 mm ~0.15 g, + parts and stiffener ~0.25 g'),
    ('Frame electronics', 'charger, protection, 5 V boost, passives on the frame PCB', 1, 2.0, EST,
     'guess for a 1S charger IC, protection FETs, 5 V boost inductor and capacitors; depends on the board'),
    ('Wiring', 'Bolt motor outputs to the ESC signal pads, solder', 1, 1.0, EST,
     '4 short 30 AWG leads + solder; the Pi and Bolt leads are listed with their connectors'),
]

PRINTED = [   # part value, name, colour (one filament each so the slice reports them apart), optional
    ('cradle_print', 'Battery cover (Pi posts, camera bosses)', '#FF6A13', False),
    ('gear_print', 'Landing gear', '#5B6579', False),
    ('cam_mount_print', 'Camera harness', '#000000', False),
    ('guard_print', 'Prop guard (optional)', '#545454', True),
]
OPTIONAL = 'Optional: prop guard'


def openscad(out, *defines):
    args = [openscad_exe(), '-o', out]
    for d in defines:
        args += ['-D', d]
    r = subprocess.run(args + [SCAD], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr)


def loops_from_svg(path):
    d = ' '.join(re.findall(r'd="([^"]+)"', open(path).read()))
    loops = []
    for sub in re.split(r'[Mm]', d)[1:]:
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', sub)]
        loops.append([(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)])
    return loops


def area(loop):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(loop, loop[1:] + loop[:1]))) / 2


def pcb_row(tmp):
    svg = os.path.join(tmp, 'pcb.svg')
    openscad(svg, 'part="pcb_outline"')
    areas = sorted((area(l) for l in loops_from_svg(svg)), reverse=True)
    a = areas[0] - sum(areas[1:])                         # outline minus every hole
    t = float(re.search(r'^pcb_t\s*=\s*([\d.]+)', open(SCAD).read(), re.M).group(1))
    fr4, cu = a * t * FR4, a * 2 * CU_T * CU_FILL * COPPER
    return ('PCB', f'Frame PCB, FR4 {t} mm, bare ({a / 100:.1f} cm2)', 1, round(fr4 + cu, 2), EST,
            f'outline area x {t} mm x 1.85 g/cm3 = {fr4:.1f} g, + copper 2 x 1 oz at {CU_FILL:.0%} = {cu:.1f} g')


def printed_rows(tmp):
    parts = []
    for part, name, colour, _ in PRINTED:
        path = os.path.join(tmp, f'{part}.3mf')
        openscad(path, f'part="{part}"')
        parts.append((name, path, colour))
    proj = os.path.join(tmp, 'printed.3mf')
    merge_3mf.merge(proj, '1S PiZero printed parts', parts)
    bambu_3mf.convert(proj, None, 'H2C', INFILL, False, False)
    ok, lines = bambu_3mf.slice_check(proj)
    text = '\n'.join(lines)
    m = re.search(r'filament (.*)  \(total', text)
    t = re.search(r'print time ([^,]+),', text)
    if not m:
        raise SystemExit(f'no weights from the slicer:\n{text}')
    grams = [float(g) for g in re.findall(r'([\d.]+) g', m.group(1))]
    if len(grams) != len(PRINTED):
        raise SystemExit(f'expected {len(PRINTED)} filament weights, got {grams}:\n{text}')
    note = f'Bambu Studio slice: H2C, 0.20 mm Standard, {INFILL} % infill, PLA Basic'
    return [(OPTIONAL if opt else 'Printed', f'{name}, PLA Basic', 1, g, EST, note)
            for (name, _, _), g, (_, _, _, opt) in zip(parts, grams, PRINTED)]


def hardware_rows(tmp):
    out = os.path.join(tmp, 'hw.echo')
    openscad(out, 'part="none"', 'echo_bom=true')
    rows = []
    for m in re.finditer(r'ECHO: "BOM\|([^|]+)\|(\d+)\|([\d.e-]+)\|([^"]*)"', open(out).read()):
        item, q, g, where = m.group(1), int(m.group(2)), float(m.group(3)), m.group(4)
        cat = 'Connectors' if 'JST' in item or 'lead' in item else 'Hardware'
        rows.append((cat, item, q, round(g, 3), EST, f'{where}; from its dimensions and material'))
    for m in re.finditer(r'ECHO: "BOMOPT\|([^|]+)\|(\d+)\|([\d.e-]+)\|([^"]*)"', open(out).read()):
        rows.append((OPTIONAL, m.group(1), int(m.group(2)), round(float(m.group(3)), 3), EST,
                     f'{m.group(4)}; from its dimensions and material'))
    if not rows:
        raise SystemExit('no hardware echoed')
    return rows


def write_xlsx(rows, path):
    from openpyxl import Workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = 'BOM'
    head = ['Category', 'Item', 'Qty', 'Unit (g)', 'Total (g)', 'Status', 'Basis / link']
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='404040')
    first = 2
    for k, r in enumerate(rows):
        n = first + k
        ws.append([r[0], r[1], r[2], r[3], f'=C{n}*D{n}', r[4], r[5]])
        ws[f'D{n}'].number_format = '0.00'
        ws[f'E{n}'].number_format = '0.00'
    last = first + len(rows) - 1
    total_row = last + 2
    ws[f'B{total_row}'] = 'All-up weight, without the prop guard'
    ws[f'E{total_row}'] = f'=SUM(E{first}:E{last})-SUMIF(A{first}:A{last},"{OPTIONAL}",E{first}:E{last})'
    ws[f'B{total_row + 1}'] = 'All-up weight, with the prop guard'
    ws[f'E{total_row + 1}'] = f'=SUM(E{first}:E{last})'
    ws[f'B{total_row + 2}'] = 'of which still estimated (with the guard)'
    ws[f'E{total_row + 2}'] = f'=SUMIF(F{first}:F{last},"{EST}",E{first}:E{last})'
    for rr in (total_row, total_row + 1, total_row + 2):
        ws[f'B{rr}'].font = Font(bold=True)
        ws[f'E{rr}'].font = Font(bold=True)
        ws[f'E{rr}'].number_format = '0.0'
    ws[f'E{total_row + 2}'].font = Font(bold=True, color='C00000')
    total_row += 2                                       # the summary goes below these

    # red whenever the Status says Estimate, so weighing a part and changing its Status turns it black
    red = Font(color='C00000')
    ws.conditional_formatting.add(f'A{first}:G{last}', FormulaRule(formula=[f'$F{first}="{EST}"'], font=red))
    dv = DataValidation(type='list', formula1=f'"{GIVEN},{EST},Weighed"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f'F{first}:F{last}')

    # category summary
    cats = list(dict.fromkeys(r[0] for r in rows))
    s = total_row + 3
    ws[f'A{s}'] = 'Category'
    ws[f'B{s}'] = 'Weight (g)'
    ws[f'C{s}'] = 'Share'
    for c in (f'A{s}', f'B{s}', f'C{s}'):
        ws[c].font = Font(bold=True)
    for k, cat in enumerate(cats):
        n = s + 1 + k
        ws[f'A{n}'] = cat
        ws[f'B{n}'] = f'=SUMIF(A${first}:A${last},A{n},E${first}:E${last})'
        ws[f'C{n}'] = f'=B{n}/E${total_row - 1}'          # share of the all-up weight with the guard
        ws[f'B{n}'].number_format = '0.0'
        ws[f'C{n}'].number_format = '0%'

    for col, w in zip('ABCDEFG', (18, 58, 6, 10, 10, 11, 90)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=first, max_row=last):
        for c in row:
            c.alignment = Alignment(vertical='top')
    ws.freeze_panes = 'A2'
    wb.save(path)


def main():
    tmp = tempfile.mkdtemp(prefix='bom_1s_')
    try:
        rows = [*COMPONENTS, pcb_row(tmp), *printed_rows(tmp), *hardware_rows(tmp)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = sum(r[2] * r[3] for r in rows)                          # with the prop guard
    base = sum(r[2] * r[3] for r in rows if r[0] != OPTIONAL)       # without it
    est = sum(r[2] * r[3] for r in rows if r[4] == EST)
    by_cat = {}
    for r in rows:
        by_cat[r[0]] = by_cat.get(r[0], 0) + r[2] * r[3]

    write_xlsx(rows, os.path.join(HERE, '1S_PiZero_BOM.xlsx'))

    with open(os.path.join(HERE, '1S_PiZero_BOM.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Category', 'Item', 'Qty', 'Unit (g)', 'Total (g)', 'Status', 'Basis / link'])
        for r in rows:
            w.writerow([r[0], r[1], r[2], f'{r[3]:.2f}', f'{r[2] * r[3]:.2f}', r[4], r[5]])
        w.writerow(['', 'All-up weight, without the prop guard', '', '', f'{base:.1f}', '', ''])
        w.writerow(['', 'All-up weight, with the prop guard', '', '', f'{total:.1f}', '', ''])

    def red(v):
        return f'$\\color{{red}}{{\\text{{{v}}}}}$'

    md = ['# 1S Pi Zero drone: bill of materials', '',
          'Generated by `1S_PiZero_bom.py` from `1S_PiZero.scad`; rerun it after changing the design. '
          'Weights in red are estimates (from size and material, or the slicer) and should be replaced '
          'by weighed values: edit them in `1S_PiZero_BOM.xlsx`, where setting a row\'s Status to '
          '"Weighed" turns it black and updates the totals.', '',
          '| Category | Item | Qty | Unit (g) | Total (g) | Basis |', '|---|---|---:|---:|---:|---|']
    for r in rows:
        u, t = f'{r[3]:.2f}', f'{r[2] * r[3]:.2f}'
        if r[4] == EST:
            u, t = red(u), red(t)
        md.append(f'| {r[0]} | {r[1]} | {r[2]} | {u} | {t} | {r[5]} |')
    md += [f'| | **All-up weight, without the prop guard** | | | **{base:.1f}** | |',
           f'| | **All-up weight, with the prop guard** | | | **{total:.1f}** | of which estimated: {red(f"{est:.1f} g")} |', '',
           '## By category', '', '| Category | Weight (g) | Share |', '|---|---:|---:|']
    for c, g in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        md.append(f'| {c} | {g:.1f} | {100 * g / total:.0f} % |')
    md += ['', '## Notes', '',
           f'- Printed weights are Bambu Studio\'s own figures for each part: H2C, 0.4 mm nozzle, '
           f'0.20mm Standard, {INFILL} % sparse infill, PLA Basic.',
           '- Hardware and connector weights come from each part\'s dimensions (steel 7.85, brass 8.5, '
           'nylon 1.14, copper 8.96, PVC 1.4 g/cm3); expect +-20 %.',
           '- The PCB line is the bare board; the parts on it are the "Frame electronics" estimate.',
           '- "Given" weights are the ones in the original BOM / the makers\' pages.']
    with open(os.path.join(HERE, '1S_PiZero_BOM.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')

    for c, g in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        print(f'  {c:20s} {g:7.1f} g')
    print(f'  {"All-up, no guard":20s} {base:7.1f} g')
    print(f'  {"All-up, with guard":20s} {total:7.1f} g  (estimated part {est:.1f} g)')
    print('wrote 1S_PiZero_BOM.xlsx, .md and .csv')


if __name__ == '__main__':
    main()
