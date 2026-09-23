import sys
import json
from pathlib import Path

def count_extensions(filenames):
    counts = {}
    for filename in filenames:
        if "." in filename:
            parts = filename.split(".")
            extension = "." + parts[-1]
            if extension not in counts:
                counts[extension] = 0
            counts[extension] += 1
            
    return counts        
    
def count_directory_extensions(directory):
    counts = {}
    for item in directory.rglob("*"):
        if item.is_file():
            extension = item.suffix
            
            if extension != "":
                if extension not in counts:
                    counts[extension] = 0
                    
                counts[extension] += 1
    
    return counts

# 将 dict(字典) 转化成 json 格式
def write_counts_to_json(counts, output_path):
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(counts, file, indent=2)
        
def main():
    directory = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    counts = count_directory_extensions(directory)
    write_counts_to_json(counts, output_path)
    
    print("Wrote statistics to", output_path)
    
if __name__ == "__main__":
    main()