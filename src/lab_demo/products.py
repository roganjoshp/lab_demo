# This really would have more stuff but beyond this demo

class Product:
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"<Product. Name: {self.name}>"