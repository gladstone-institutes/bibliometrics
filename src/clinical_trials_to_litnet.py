import clinicaltrials
import pubmed

def main(drugname):
  ct_client = clinicaltrials.Client()
  trials = ctclient.search(drugname)
