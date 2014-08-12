# Process description for creating an input file for Kalydeco/Ivacaftor

1. Go to the [FDA drug site](http://www.accessdata.fda.gov/scripts/cder/drugsatfda/) and search for *Kalydeco*.
1. Click on *Approval History, Letters, Reviews, and Related Documents*.
1. Under the *Approval* item (at the end), click on *Review*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188s000TOC.cfm)
1. Click on *Medical Review (PDF)*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188Orig1s000MedR.pdf)
1. Use the *poppler-util* package's *pdftotext* command to extract the text from the PDF.
1. Copy the *Literature Review/References* section of the text file to its own file `input/Ivacaftor-FDA-NDA-Medical.txt`.
1. Put the name of the drug (`Ivacaftor`) as the first line in the text file above.

# Steps to run refs.py

1. Install virtualenv: `pip install virtualenv`
1. Create `venv` in `metrics` directory: `virtualenv venv`
1. Activate `venv`: `source venv/bin/activate`
1. Install needed software: `pip install lxml requests requests-cache networkx suds python-dateutil`
1. Run refs.py: `python src/cse_refs_to_litnet.py input/Ivacaftor-FDA-NDA-Medical.txt`
