from lab_demo.config import Config


class Machine:
    
    def __init__(
        self,
        shift_pattern: str,
        config: Config = Config()
    ):
        self.config = config
        self.shift_pattern = shift_pattern