"""Offline regression tests for PC routing, exhibits and unknown case facts."""
import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from docx import Document
from docx.oxml.ns import qn
from core.paths import templates_dir
from wizards.mls import templates_2026 as MLS
from wizards.mls.pc_ordinance import generate

class PCOrdinanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.map=self.folder/'map.png';Image.new('RGB',(600,700),'white').save(self.map)
        self.template=templates_dir('mls')/'MLS_Ordinance_Template_PC.docx'
        self.ctx=dict(Approval_Path='Planning Commission Approval',PC_Hearing_Date='October 29, 2026',Protest_Count=1,
            Ordinance_Area_Upper='NORTH SIDE OF THE 100 BLOCK OF TEST STREET',Ordinance_Area_Lower='north side of the 100 block of Test Street',
            Support_Percentage='54',Qualifying_Phrase='fifteen (15) out of eighteen (18)',Lot_Size_Phrase='nine thousand seven hundred and fifty (9,750)',
            Minimum_Lot_Size_Text='9,750',Ordinance_Year='2026',Director_Name='Test Director')
        self.rows=[dict(ADDRESS=f'{100+i} TEST ST',HCAD=str(611170000026+i),LEGAL_DESCRIPTION=f'LT {i+1} BLK 1 TEST SUBDIVISION',SUBDIVISION='TEST SUBDIVISION') for i in range(18)]
    def test_pc_route_uses_new_template_and_four_column_property_list(self):
        out=self.folder/'pc.docx'
        with patch.object(MLS,'build_context',return_value=self.ctx),patch.object(MLS.ME,'_read_property_rows_for_ordinance',return_value=self.rows):
            MLS.generate_draft_ordinance('fixture.xlsx',templates_dir('mls')/'MLS_Ordinance_Template.docx',self.map,out)
        doc=Document(out);text=' '.join(p.text for p in doc.paragraphs)
        self.assertIn('1 timely protest was received',text)
        self.assertIn('October 29, 2026',text)
        self.assertIn('54% of the Application Area',text)
        self.assertNotIn('Mayflower',text);self.assertNotIn('{{',text)
        self.assertEqual(len(doc.tables[-1].rows),19)
        self.assertEqual(len(doc.tables[-1].columns),4)
        self.assertEqual(doc.tables[-1].rows[1].cells[1].text,'0611170000026')
        self.assertEqual(doc.tables[-1].rows[1].cells[2].text,self.rows[0]['LEGAL_DESCRIPTION'])
        self.assertFalse(list(doc.tables[-1]._tbl.iter(qn('w:shd'))))
        self.assertEqual(len(list(doc.element.body.iter(qn('a:blip')))),1)
    def test_no_protest_pc_does_not_claim_protested_application(self):
        self.ctx['Protest_Count']=0
        out=self.folder/'no_protest.docx';generate(self.ctx,self.rows,self.template,self.map,out)
        text=' '.join(p.text for p in Document(out).paragraphs)
        self.assertNotIn('protested application',text);self.assertNotIn('timely protest',text)
        self.assertIn('Planning Commission considered the application',text)
    def test_missing_verified_facts_fail_before_output(self):
        for key,value in [('PC_Hearing_Date','[Date]'),('Qualifying_Phrase','X (X) out of eighteen (18)')]:
            bad=dict(self.ctx);bad[key]=value
            out=self.folder/'bad.docx'
            with self.assertRaises(ValueError):generate(bad,self.rows,self.template,self.map,out)
            self.assertFalse(out.exists())
    def test_director_case_cannot_use_pc_generator(self):
        self.ctx['Approval_Path']='Director Approval'
        with self.assertRaises(ValueError):generate(self.ctx,self.rows,self.template,self.map,self.folder/'bad.docx')

def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PCOrdinanceTests)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
