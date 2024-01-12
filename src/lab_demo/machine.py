from lab_demo.config import Config
from lab_demo.products import Product


class Machine:
    
    # Prevent duplicates
    seen_machine_ids = set()
    
    def __init__(
        self,
        machine_id: int,
        shift_pattern: str,
        config: Config = Config()
    ):
        self.config = config
        self._products = []
        self._product_names = {}
        
        if machine_id in self.seen_machine_ids:
            raise ValueError("Machine ID already specified!")
        
        if shift_pattern not in self.config.SHIFT_PATTERNS:
            raise ValueError("Shift pattern not recognised!")
        
        self.shift_pattern = self.config.SHIFT_PATTERNS[shift_pattern]
        self.hourly_production = (
            self.config.MACHINE_STATS[machine_id]['ideal_run_rate']
        )
        self.seen_machine_ids.add(machine_id)
    
    def add_product(
        self, 
        product: Product
    ):
        if not isinstance(product, Product):
            raise TypeError("Not a valid product!")
        
        if product.name in self._product_names:
            raise RuntimeError(f"Product: {product.name} already added!")
        
        self._products.append(product)
        self._product_names.add(product.name)