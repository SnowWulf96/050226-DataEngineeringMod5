import argparse

##pass variables
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Pass in Env Variables to do a calculation.')
    parser.add_argument('--a', type=int, default=625, help='First number')
    parser.add_argument('--b', type=int, default=125, help='Second number')
    return parser.parse_args()


class Calculator:  
    def __init__(self, a, b):
        self.a = a
        self.b = b
        
    def get_sum(self):
        return self.a + self.b
    def divide(self):
        return self.a / self.b
    def multiply(self):
        return self.a * self.b
    def subtract(self):
        return self.a - self.b
        ##must be able to get square root of a number e.g. 435
    def squareroot(self):
        return self.a ** 0.5

## Stretch goal: use argparse to import env variables to do the sum of two numbers, and print the result in the terminal.
if __name__ == "__main__":
    args = parse_args()
    mycal = Calculator(args.a, args.b)    
    mysum = mycal.get_sum()
    print(mysum)
