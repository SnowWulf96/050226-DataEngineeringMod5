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
## Stretch goal: use argparse to import env variables to do the sum of two numbers, and print the result in the terminal.
    
if __name__ == "__main__":
    mycal = Calculator(a=5, b=20)    
    mysum = mycal.multiply()
    print(mysum)
