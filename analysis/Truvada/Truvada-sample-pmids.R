## Takes xml output from an eutils query and makes random, exclusive samples of pmids for peripheral network anlaysis

install.packages("XML")
library(XML)

#read in xml file
xml=xmlParse("Truvada-peripheral-pubs.xml")

#extract pmids as a list
list=xpathApply(xml, "//Id", xmlValue)

#split list into random, exclusive sets of 5000
sets=split(sample(list),rep(1:(length(list)/5000+1), each=5000))

#write out 5 of these sets as peripheral pmids files
for(i in 1:5){
    f=paste0("Truvada-Pubmed-Search-PMIDs",i,".txt")
    fileConn=file(f)
    writeLines(as.character(sets[[i]]), fileConn)
    close(fileConn)
}
