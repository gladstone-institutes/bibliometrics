####Truvada-FDA-NDA-Medical.txt
Truvada (emtricitabine; tenofovir disoproxil fumarate) was approved on 2 Aug 2004. Unfortunately, there is no bibliography or literature review in the Medical Review of the Approval Package, so there will be no publications linked to the FDA node in this network. Note: had to add a publication from the clinical trial set to the input file to avoid runtime error handling 0 FDA-sourced publications.

http://www.accessdata.fda.gov/drugsatfda_docs/nda/2004/021752s000_Truvada_Medr.pdf

####Truvada-core.pklz
```
python src/topdown.py --format cse --levels 2 input/Truvada-FDA-NDA-Medical.txt output/Truvada-core.pklz
```
Ran o/n.

####Truvada-core-individual-indegree.pklz, Truvada-core-propagate-sum.pklz
```
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Truvada-core.pklz output/Truvada-core-individual-indegree.pklz
python src/score.py --article-scoring propagate --neighbor-scoring sum output/Truvada-core.pklz output/Truvada-core-propagate-sum.pklz
```

####Truvada-core-individual-indegree.xgmml, Truvada-core-propagate-sum.xgmml
```
python src/xgmml.py output/Truvada-core-individual-indegree.pklz output/Truvada-core-individual-indegree.xgmml
python src/xgmml.py output/Truvada-core-propagate-sum.pklz output/Truvada-core-propagate-sum.xgmml
```
Network properties:
* 4937 articles (1951-2014)
* 21275 authors
* 15358 institutions
* 43 grant agencies
* 227 clinical trials 


####Truvada-Pubmed-Search-PMIDs*.txt
For the peripheral network, we will try sampling from the following search term:
* (("1900/1/1"[Date - Publication] : "2014/12/01"[Date - Publication])) AND reverse transcriptase inhibitor
 * ### hits spanning YYYY-YYYY 
  * took ### pmids from every ###th page to collect ### pubs, ### 
   * 1,7,13,...43 | 2,8,14,...44 | 3,9,15,...45 | 4,10,16,..46 | 5,11,17,..47,48(1794)

##Truvada-peripheral*.pklz
Note: only level 1 if providing comparable number of pmids from pubmed search, i.e., comparable to core network article count.
```
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Truvada-Pubmed-Search-PMIDs1.txt output/Truvada-peripheral1.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Truvada-Pubmed-Search-PMIDs2.txt output/Truvada-peripheral2.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Truvada-Pubmed-Search-PMIDs3.txt output/Truvada-peripheral3.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Truvada-Pubmed-Search-PMIDs4.txt output/Truvada-peripheral4.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Truvada-Pubmed-Search-PMIDs5.txt output/Truvada-peripheral5.pklz
```
Ran in 9-30 min each.

####Truvada-peripheral-individual-indegree*.pklz
```
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Truvada-peripheral1.pklz output/Truvada-peripheral-individual-indegree1.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Truvada-peripheral2.pklz output/Truvada-peripheral-individual-indegree2.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Truvada-peripheral3.pklz output/Truvada-peripheral-individual-indegree3.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Truvada-peripheral4.pklz output/Truvada-peripheral-individual-indegree4.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Truvada-peripheral5.pklz output/Truvada-peripheral-individual-indegree5.pklz
```

####Truvada-peripheral-scored-*.xgmml
```
python src/xgmml.py output/Truvada-peripheral-individual-indegree1.pklz output/Truvada-peripheral-individual-indegree1.xgmml
python src/xgmml.py output/Truvada-peripheral-individual-indegree2.pklz output/Truvada-peripheral-individual-indegree2.xgmml
python src/xgmml.py output/Truvada-peripheral-individual-indegree3.pklz output/Truvada-peripheral-individual-indegree3.xgmml
python src/xgmml.py output/Truvada-peripheral-individual-indegree4.pklz output/Truvada-peripheral-individual-indegree4.xgmml
python src/xgmml.py output/Truvada-peripheral-individual-indegree5.pklz output/Truvada-peripheral-individual-indegree5.xgmml
```
Network properties (average):
* # articles (# unique articles total)
* # authors
* # institutions
* # grantagencies

####Analysis
* Opened scored xgmml in Cytoscape
* Selected authors into new subnetwork; selected institutes into new subnetwork
* Exported default node tables for each subnetwork
* Opened csv in excel
* Pasted authors and scores from core-scored-sum author subnetworks into CP-Prop columns in analysis.xlsx template
* Pasted authors and ct_scores from core-scored-sum author subnetworks into CT-Count columns
* Pasted authors and score from core-scored-indegree author subnetworks into CP-Indegree columns
* Pasted authors and score from peripheral-scored-indegree author subnetwork into Denom-Indegree columns
* Pasted authors and score from peripheral-scored-indegree2 author subnetwork into Denom-Indegree2 columns
* Template formulas calculation ranks and ratios
* Note: averaged ratios across multiple samples of peripheral to get a better RBR filter criteria, i.e., it covers more of the pubmed search result space, without compromizing the scope and size contraints of a given peripheral network. 

CPI subnetwork:
* # articles (YYYY-YYYY)
* # authors
* # institutes (# unique)
