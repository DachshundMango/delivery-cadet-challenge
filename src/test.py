import glob
import os

if __name__ == "__main__":
    
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    data_dir = os.path.join(BASE_DIR, 'data')
    print(data_dir)
