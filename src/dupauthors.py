import sys
import pandas

def main(mat1_path, mat2_path):
  mat1 = pandas.read_csv(mat1_path)
  mat2 = pandas.read_csv(mat2_path)

  authors1 = set(mat1['Unnamed: 0'])
  authors2 = set(mat2['Unnamed: 0'])

  common_authors = authors1 & authors2

  for common_author in common_authors:
    print common_author


if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
