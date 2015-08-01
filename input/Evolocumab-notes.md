####Evolocumab-FDA-NDA-Medical.txt
As of July 30, 2015, evolocumab (Repatha) has not been approved by FDA, but there are plenty of references to work with in the clicinal trials and the FDA Briefing Document:
* https://clinicaltrials.gov/ct2/results?term=evolocumab&Search=Search
* http://www.fda.gov/downloads/AdvisoryCommittees/CommitteesMeetingMaterials/Drugs/EndocrinologicandMetabolicDrugsAdvisoryCommittee/UCM450072.pdf

####Evolocumab-core.pklz
```
python src/topdown.py --format cse --levels 2 input/Evolocumab-FDA-NDA-Medical.txt output/Evolocumab-core.pklz
```

####Evolocumab-core.xgmml
```
python src/xgmml.py output/Evolocumab-core.pklz output/Evolocumab-core.xgmml
```
Network properties:
* 1548 articles (1950-2015)
* 7350 authors
* 4846 institutions
* 37 grantagencies


####Evolocumab-Pubmed-Search-PMIDs.txt
For the peripheral network, we will try sampling from the following search term:
* ldl cholesterol reduction (9722 hits spanning 1971-2015; took 200 pmids from every 6th page:1,7,13,19,...)

####Evolocumab-peripheral.pklz
```
python src/topdown.py --format pmid --dont-search-trials --levels 2 input/Evolocumab-Pubmed-Search-PMIDs.txt output/Evolocumab-peripheral.pklz
```

####Evolocumab-peripheral.xgmml
```
python src/xgmml.py output/Evolocumab-peripheral.pklz output/Evolocumab-peripheral.xgmml
```
Network properties:
* # articles (yyyy-yyyy)
* # authors
* # institutions
* # grantagencies
