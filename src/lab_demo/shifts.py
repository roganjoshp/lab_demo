from lab_demo.config import Config


class ShiftPatterns:
    
    def __init__(self):
        self.config = Config()
        self.shifts = self.config.SHIFT_PATTERNS
        

if __name__ == '__main__':
    
    patterns = ShiftPatterns()
    print(patterns.shifts)