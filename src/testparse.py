import refparse
import sys

def _main(input_file_path):
  lines = []
  with open(input_file_path, 'r') as input_file:
    lines = [l.strip() for l in input_file.readlines()]
  refs = refparse.parse_cse_refs(lines[1:])
  for ref in refs:
    print ref

if __name__ == '__main__':
  _main(sys.argv[1])
