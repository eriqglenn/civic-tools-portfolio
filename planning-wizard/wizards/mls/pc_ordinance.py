"""MLS Planning Commission ordinance, user-supplied November 18, 2026 source."""
from pathlib import Path
import copy
import re
import tempfile
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

def _set(p, text):
    props = copy.deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
    p.clear()
    run = p.add_run(str(text))
    if props is not None:
        run._r.insert(0, props)
    run.font.color.rgb = __import__('docx.shared', fromlist=['RGBColor']).RGBColor(0, 0, 0)
    if text.startswith(('WHEREAS,', 'Section ')):
        lead = 'WHEREAS,' if text.startswith('WHEREAS,') else text.split('.', 1)[0] + '.'
        run.text = lead
        run.bold = True
        rest = p.add_run(text[len(lead):])
        rest.font.name = 'Arial'
        rest.font.size = Pt(12)
        rest.bold = False

def generate(ctx, rows, template_path, map_path, output_path):
    if ctx.get('Approval_Path') != 'Planning Commission Approval':
        raise ValueError('The PC ordinance template requires Planning Commission approval.')
    hearing = str(ctx.get('PC_Approval_Date') or ctx.get('PC_Hearing_Date') or '').strip()
    if not hearing or '[' in hearing:
        raise ValueError('Enter the verified Planning Commission approval date in Case Info.')
    if not rows or not Path(map_path or '').is_file():
        raise ValueError('Property inventory and boundary map are required for Exhibits A, B and C.')
    for key in ('Support_Percentage', 'Qualifying_Phrase', 'Lot_Size_Phrase'):
        value = str(ctx.get(key) or '')
        if not value or re.search(r'\bX+\b', value) or '[' in value:
            raise ValueError('Complete and verify the calculation sheet: ' + key)
    protest = int(ctx.get('Protest_Count') or 0)
    recital = (f'WHEREAS, {protest} timely protest' + (' was' if protest == 1 else 's were') +
               ' received against the application; and') if protest else ''
    pc = ('WHEREAS, the Houston Planning Commission considered the ' +
          ('protested ' if protest else '') + f'application on {hearing}, and voted to recommend that the City Council establish the Special Minimum Lot Size Block; and')
    values = dict(ctx, Protest_Recital=recital, PC_Recital=pc,
                  Legal_File_No=ctx.get('Legal_File_No') or '________________',
                  Ordinance_Year=ctx.get('Ordinance_Year') or '____')
    doc = Document(str(template_path))
    if '{{EXHIBIT_A}}' not in '\n'.join(p.text for p in doc.paragraphs):
        raise ValueError('Select the adapted MLS Planning Commission ordinance template from Template Manager.')
    for p in list(doc.paragraphs):
        text = p.text
        if text.strip() == '{{Protest_Recital}}' and not recital:
            p._p.getparent().remove(p._p)
            continue
        if '{{' in text and text.strip() not in ('{{EXHIBIT_A}}', '{{EXHIBIT_B}}'):
            for key, value in values.items():
                text = text.replace('{{' + key + '}}', str(value))
            _set(p, text)
        if p.text.strip() == '{{EXHIBIT_A}}':
            descriptions = list(dict.fromkeys(row.get('LEGAL_DESCRIPTION', '') for row in rows))
            if any(not x for x in descriptions):
                raise ValueError('Every property needs its verified legal description.')
            _set(p, '\n'.join(descriptions))
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = 0
            p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.left_indent = Inches(0)
            for r in p.runs:
                r.font.size = Pt(10)
        elif p.text.strip() == '{{EXHIBIT_B}}':
            from core.docx_merge import _map_to_png
            with tempfile.TemporaryDirectory() as td:
                png = _map_to_png(map_path, td)
                if not png:
                    raise ValueError('The boundary map could not be rendered.')
                p.clear()
                p.alignment = 1
                from PIL import Image
                with Image.open(png) as img:
                    width, height = img.size
                p.add_run().add_picture(png, width=Inches(min(6.25, 8.3 * width / height)))
    table = doc.tables[-1]
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[-1]._tr)
    header = table.rows[0]._tr.get_or_add_trPr()
    header.append(OxmlElement('w:tblHeader'))
    for row in rows:
        account = re.sub(r'\D', '', str(row.get('HCAD') or ''))
        if not account or len(account) > 13:
            raise ValueError('A valid HCAD account is required for every property.')
        cells = table.add_row().cells
        for cell, val in zip(cells, (row.get('ADDRESS'), account.zfill(13), row.get('LEGAL_DESCRIPTION'), row.get('SUBDIVISION'))):
            if not val:
                raise ValueError('Exhibit C contains missing property data.')
            cell.text = str(val)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.line_spacing = 1.0
                p.alignment = 0
                p.paragraph_format.first_line_indent = Inches(0)
                for r in p.runs:
                    r.font.name = 'Arial'
                    r.font.size = Pt(8)
        table.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    for e in list(doc.element.body.iter(qn('w:shd'))):
        e.getparent().remove(e)
    text = '\n'.join(p.text for p in doc.paragraphs)
    if '{{' in text:
        raise ValueError('An ordinance field is unresolved; complete Case Info before generating.')
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    from core.docx_unlock import unlock_docx
    unlock_docx(out)
    return 1
