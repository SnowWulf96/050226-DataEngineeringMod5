from pathlib import Path
from datetime import datetime

out = Path('/data/hello.txt')
#checking and printing the current content of the file in the volume (if it exists)
if out.exists():
    current_content = out.read_text()
    print(f"Current content:")
    print(current_content)
else:
    print("File does not exist in the volume.")

##appending a new line
with out.open('a') as f:
    f.write(f"Hello Docker volume! The time is {datetime.now()}\n")