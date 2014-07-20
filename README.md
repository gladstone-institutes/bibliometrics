# Process description for Kalydeco

1. Go to the [FDA drug site](http://www.accessdata.fda.gov/scripts/cder/drugsatfda/) and search for *Kalydeco*.
1. Click on *Approval History, Letters, Reviews, and Related Documents*.
1. Under the *Approval* item (at the end), click on *Review*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188s000TOC.cfm)
1. Click on *Medical Review (PDF)*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188Orig1s000MedR.pdf)
1. Use the *poppler-util* package's *pdftotext* command to extract the text from the PDF.
1. Copy the *Literature Review/References* section of the text file to its own file `Kalydeco/Medical Review References.txt`.
1. Run the *refs.py* script, which reads from `Kalydeco/Medical Review References.txt`.

# Steps to run refs.py

1. Install virtualenv: `pip install virtualenv`
1. Create `venv` in `metrics` directory: `virtualenv venv`
1. Activate `venv`: `source venv/bin/activate`
1. Install needed software: `pip install nltk lxml requests networkx`
1. Run refs.py: `python refs.py Kalydeco/FDA*.txt Kalydeco/pubmed*.txt`
