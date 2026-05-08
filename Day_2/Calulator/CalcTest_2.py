import unittest
from Calculator import Calculator

class TestOperations(unittest.TestCase):
    def setUp(self):
            self.calc = Calculator(8,2)

    def test_sum(self):
        self.assertEqual(self.calc.get_sum(), 10, "The answer was not correct")

    def test_divide(self):
        self.assertEqual(self.calc.divide(), 4, "The answer was not correct")

    def test_multiply(self):
        self.assertEqual(self.calc.multiply(), 16, "The answer was not correct")
        
    def test_subtract(self):
        self.assertEqual(self.calc.subtract(), 6, "The answer was not correct")

if __name__ == '__main__':
    unittest.main()
