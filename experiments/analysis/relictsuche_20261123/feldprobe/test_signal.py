import unittest
import numpy as np
from signalmodell import Evidence,PAIR


class PublicHistory(unittest.TestCase):
    def test_stack_once_and_two_mirrors_twice(self):
        e=Evidence()
        a=np.array([[3,4],[3,4],[19,20]])
        e.observe(20,a,2,np.zeros((24,24),bool))
        k=PAIR[3,4]
        self.assertEqual(e.lifetime_n[k],1)
        self.assertAlmostEqual(e.lifetime_max[k],1.)
        e.observe(21,a,2,np.zeros((24,24),bool))
        self.assertEqual(e.lifetime_n[k],1)

    def test_zero_evidence_expires_but_positive_hint_remains(self):
        e=Evidence()
        a=np.array([[3,4],[4,4]])
        k=PAIR[3,4]
        e.observe(87,a,1,np.zeros((24,24),bool))
        self.assertEqual(e.recent_n[k],1)
        e.observe(0,np.zeros((0,2),int),0,np.zeros((24,24),bool))
        self.assertEqual(e.recent_n[k],0)
        self.assertAlmostEqual(e.lifetime_max[k],.5)


if __name__=="__main__":
    unittest.main()
