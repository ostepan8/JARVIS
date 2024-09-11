def factorial(n):
    # Check if the input is a non-negative integer
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    
    # Base case: factorial of 0 is 1
    if n == 0:
        return 1
    
    # Initialize result
    result = 1
    
    # Calculate factorial
    for i in range(1, n + 1):
        result *= i
    
    return result

import unittest
from test import factorial

class TestFactorial(unittest.TestCase):
    def test_factorial_zero(self):
        self.assertEqual(factorial(0), 1)

    def test_factorial_one(self):
        self.assertEqual(factorial(1), 1)

    def test_factorial_two(self):
        self.assertEqual(factorial(2), 2)

    def test_factorial_three(self):
        self.assertEqual(factorial(3), 6)

    def test_factorial_four(self):
        self.assertEqual(factorial(4), 24)

    def test_factorial_five(self):
        self.assertEqual(factorial(5), 120)

    def test_factorial_six(self):
        self.assertEqual(factorial(6), 720)

    def test_factorial_large_number(self):
        self.assertEqual(factorial(10), 3628800)

    def test_factorial_negative(self):
        with self.assertRaises(ValueError):
            factorial(-1)

if __name__ == '__main__':
    unittest.main()