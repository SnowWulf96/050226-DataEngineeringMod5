from Calculator import Calculator

#MYCALCV2 = Calculator(5,20)

#print(MYCALCV2.multiply())

class SciCalc(Calculator):
    def get_exponent(self):
        return self.a ** self.b
    
    mySciCalc = SciCalc(a=2, b=3)
    print(mySciCalc.get_exponent())