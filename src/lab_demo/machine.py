from lab_demo.config import Config


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
        
        if machine_id in self.seen_machine_ids:
            raise ValueError("Machine ID already specified!")
        
        if shift_pattern not in self.config.SHIFT_PATTERNS:
            raise ValueError("Shift pattern not recognised!")
        
        self.shift_pattern = self.config.SHIFT_PATTERNS[shift_pattern]
        self.seen_machine_ids.add(machine_id)