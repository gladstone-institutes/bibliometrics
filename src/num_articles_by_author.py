import sys
import pubmed

def main(author_names):
  client = pubmed.Client()
  for author_name in author_names:
    print '%s: %d' % (author_name, client.num_papers_by_author(author_name))

if __name__ == '__main__':
  main(sys.argv[1:])
