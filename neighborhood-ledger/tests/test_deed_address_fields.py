import unittest
from unittest.mock import patch
import deed_search as d

class SeparateAddressTests(unittest.TestCase):
    def test_fields_assume_houston_and_filter_zip(self):
        with patch.object(d,'parcel_query',return_value={'features':[]}) as query:
            d.find_properties_fields('1042','Sampleoak Street','77018')
        where=query.call_args.args[0]
        self.assertIn('site_str_num = 1042',where)
        self.assertIn("'SAMPLEOAK'",where)
        self.assertIn("UPPER(site_city) = 'HOUSTON'",where)
        self.assertIn("site_zip = '77018'",where)

    def test_zip_is_optional(self):
        with patch.object(d,'parcel_query',return_value={'features':[]}) as query:
            d.find_properties_fields('1042','Sampleoak Street')
        self.assertNotIn('site_zip',query.call_args.args[0])
        self.assertIn("'HOUSTON'",query.call_args.args[0])

    def test_invalid_fields_never_call_county(self):
        with patch.object(d,'parcel_query') as query:
            for args in [('', 'Sampleoak St',''),('1042','', ''),('10A','Sampleoak',''),('1042','Sampleoak','7701'),('1042','Sampleoak',"' OR 1=1"),('1042','5','')]:
                with self.subTest(args=args),self.assertRaises(ValueError):
                    d.find_properties_fields(*args)
            query.assert_not_called()

    def test_directions_are_preserved(self):
        with patch.object(d,'find_properties',return_value={}) as lookup:
            d.find_properties_fields(' 1200 ',' North Main Street ',' 77009 ')
        lookup.assert_called_once_with('1200 North Main Street, Houston, TX',zip_code='77009',houston_only=True)
