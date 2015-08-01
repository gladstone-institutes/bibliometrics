####Evolocumab-FDA-NDA-Medical.txt
As of July 30, 2015, evolocumab (Repatha) has not been approved by FDA, but there are plenty of references to work with in the clicinal trials and the FDA Briefing Document:
* https://clinicaltrials.gov/ct2/results?term=evolocumab&Search=Search
* http://www.fda.gov/downloads/AdvisoryCommittees/CommitteesMeetingMaterials/Drugs/EndocrinologicandMetabolicDrugsAdvisoryCommittee/UCM450072.pdf

####Evolocumab-core.pklz
```
python src/topdown.py --format cse --levels 2 input/Evolocumab-FDA-NDA-Medical.txt output/Evolocumab-core.pklz
```
Ran o/n.

####Evolocumab-core-scored-*.pklz
```
python src/score.py --article-scoring propagate --neighbor-scoring indegree output/Evolocumab-core.pklz output/Evolocumab-core-scored-indegree.pklz
python src/score.py --article-scoring propagate --neighbor-scoring sum output/Evolocumab-core.pklz output/Evolocumab-core-scored-sum.pklz
```

####Evolocumab-core-scored-*.xgmml
```
python src/xgmml.py output/Evolocumab-core-scored-indegree.pklz output/Evolocumab-core-scored-indegree.xgmml
python src/xgmml.py output/Evolocumab-core-scored-sum.pklz output/Evolocumab-core-scored-sum.xgmml
```
Network properties:
* 1548 articles (1950-2015)
* 7350 authors
* 4846 institutions
* 37 grantagencies


####Evolocumab-Pubmed-Search-PMIDs.txt
For the peripheral network, we will try sampling from the following search term:
* ldl cholesterol reduction (9722 hits spanning 1971-2015) 
 * took 200 pmids from every 6th page starting at 1,7,13,19,... to collect sample of 1600
 * took 200 pmids from every 6th page starting at 4,10,16,22,... to collect alternate sample of 1600 (to see if indegree denom results depend on collection), thus Evolocumab-Pubmed-Search-PMIDs2.txt and "2" versions of subsequent files

####Evolocumab-peripheral.pklz
Note: only level 1 if providing comparable number of pmids from pubmed search, i.e., comparable to core network article count.
```
python src/topdown.py --format pmid --dont-search-trials --levels 1 input/Evolocumab-Pubmed-Search-PMIDs.txt output/Evolocumab-peripheral.pklz
```
Ran in 30 sec or 30min (noticed big difference for two different lists of 1600 pmids; not sure why)

####Evolocumab-peripheral-scored-*.pklz
```
python src/score.py --article-scoring propagate --neighbor-scoring indegree output/Evolocumab-peripheral.pklz output/Evolocumab-peripheral-scored-indegree.pklz
python src/score.py --article-scoring propagate --neighbor-scoring sum output/Evolocumab-peripheral.pklz output/Evolocumab-peripheral-scored-sum.pklz
```

####Evolocumab-peripheral-scored-*.xgmml
```
python src/xgmml.py output/Evolocumab-peripheral-scored-indegree.pklz output/Evolocumab-peripheral-scored-indegree.xgmml
python src/xgmml.py output/Evolocumab-peripheral-scored-sum.pklz output/Evolocumab-peripheral-scored-sum.xgmml
```
Network properties:
* 1598 articles (1992-2015)
* 7656 authors
* 4622 institutions
* 23 grantagencies
