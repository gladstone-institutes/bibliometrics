####Evolocumab-FDA-NDA-Medical.txt
As of July 30, 2015, evolocumab (Repatha) has not been approved by FDA, but there are plenty of references to work with in the clicinal trials and the FDA Briefing Document:
* https://clinicaltrials.gov/ct2/results?term=evolocumab&Search=Search
* http://www.fda.gov/downloads/AdvisoryCommittees/CommitteesMeetingMaterials/Drugs/EndocrinologicandMetabolicDrugsAdvisoryCommittee/UCM450072.pdf

####Evolocumab-core.pklz
```
python src/topdown.py --format cse --levels 2 input/Evolocumab-FDA-NDA-Medical.txt output/Evolocumab-core.pklz
```
Ran o/n.

####Evolocumab-core-individual-indegree.pklz, Evolocumab-core-propagate-sum.pklz
```
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Evolocumab-core.pklz output/Evolocumab-core-individual-indegree.pklz
python src/score.py --article-scoring propagate --neighbor-scoring sum output/Evolocumab-core.pklz output/Evolocumab-core-propagate-sum.pklz
```

####Evolocumab-core-individual-indegree.xgmml, Evolocumab-core-propagate-sum.xgmml
```
python src/xgmml.py output/Evolocumab-core-individual-indegree.pklz output/Evolocumab-core-individual-indegree.xgmml
python src/xgmml.py output/Evolocumab-core-propagate-sum.pklz output/Evolocumab-core-propagate-sum.xgmml
```
Network properties:
* 1548 articles (1950-2015)
* 7350 authors
* 4846 institutions
* 37 grant agencies
* 26 clinical trials 


####Evolocumab-Pubmed-Search-PMIDs*.txt
For the peripheral network, we will try sampling from the following search term:
* (("1900/1/1"[Date - Publication] : "2015/03/11"[Date - Publication])) AND ldl cholesterol reduction
 * 9593 hits spanning 1971-2015 
  * took 200 pmids from every 6th page to collect 1600 pubs, 5 
   * 1,7,13,...43 | 2,8,14,...44 | 3,9,15,...45 | 4,10,16,..46 | 5,11,17,..47,48(1794)

##Evolocumab-peripheral*.pklz
Note: only level 1 if providing comparable number of pmids from pubmed search, i.e., comparable to core network article count.
```
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Evolocumab-Pubmed-Search-PMIDs1.txt output/Evolocumab-peripheral1.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Evolocumab-Pubmed-Search-PMIDs2.txt output/Evolocumab-peripheral2.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Evolocumab-Pubmed-Search-PMIDs3.txt output/Evolocumab-peripheral3.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Evolocumab-Pubmed-Search-PMIDs4.txt output/Evolocumab-peripheral4.pklz
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Evolocumab-Pubmed-Search-PMIDs5.txt output/Evolocumab-peripheral5.pklz
```
Ran in 26min

####Evolocumab-peripheral-individual-indegree*.pklz
```
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Evolocumab-peripheral1.pklz output/Evolocumab-peripheral-individual-indegree1.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Evolocumab-peripheral2.pklz output/Evolocumab-peripheral-individual-indegree2.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Evolocumab-peripheral3.pklz output/Evolocumab-peripheral-individual-indegree3.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Evolocumab-peripheral4.pklz output/Evolocumab-peripheral-individual-indegree4.pklz
python src/score.py --article-scoring individual --neighbor-scoring indegree output/Evolocumab-peripheral5.pklz output/Evolocumab-peripheral-individual-indegree5.pklz
```

####Evolocumab-peripheral-scored-*.xgmml
```
python src/xgmml.py output/Evolocumab-peripheral-individual-indegree1.pklz output/Evolocumab-peripheral-individual-indegree1.xgmml
python src/xgmml.py output/Evolocumab-peripheral-individual-indegree2.pklz output/Evolocumab-peripheral-individual-indegree2.xgmml
python src/xgmml.py output/Evolocumab-peripheral-individual-indegree3.pklz output/Evolocumab-peripheral-individual-indegree3.xgmml
python src/xgmml.py output/Evolocumab-peripheral-individual-indegree4.pklz output/Evolocumab-peripheral-individual-indegree4.xgmml
python src/xgmml.py output/Evolocumab-peripheral-individual-indegree5.pklz output/Evolocumab-peripheral-individual-indegree5.xgmml
```
Network properties (average):
* ### articles (1971-2015 )
* ### authors
* ### institutions
* ### grantagencies

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
* 342 articles (1974-2014)
* 27 authors
* 7 institutes (4 unique)
