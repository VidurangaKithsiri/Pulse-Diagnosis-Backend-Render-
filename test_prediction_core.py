import unittest
from prediction_core import predict_payload, DOMAIN
class PredictionTests(unittest.TestCase):
 def setUp(self): self.data={k:(v['min']+v['max'])/2 for k,v in DOMAIN.items()}
 def test_sensor_domain(self):
  r=predict_payload(dict(mean=128250,std=1000,variance=1000000,max=130250,min=126250,range=4000,energy=1920*128250**2))
  self.assertEqual(r['status'],'OUT_OF_DISTRIBUTION');self.assertEqual(r['prediction'],'Unavailable');self.assertIsNone(r['confidence']);self.assertEqual(r['risk_level'],'Not assessed')
 def test_supported(self):
  r=predict_payload(self.data);self.assertIn(r['prediction_id'],[0,1]);self.assertEqual(r['risk_level'],'Not assessed')
 def test_invalid(self):
  for v in ['ovf',None,float('nan'),float('inf'),True]:
   with self.subTest(value=v):
    with self.assertRaises(ValueError):predict_payload({**self.data,'energy':v})
 def test_missing(self):
  for v in [{},None,[]]:
   with self.assertRaises(ValueError):predict_payload(v)
if __name__=='__main__':unittest.main()
