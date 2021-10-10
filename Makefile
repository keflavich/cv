# latex Makefile
#texpath=/usr/texbin/
texpath=""
#TEXINPUTS=.:/Users/adam/papers/latexfiles:
LATEX=${texpath}latex
PDFLATEX=${texpath}pdflatex -halt-on-error
BIBTEX=${texpath}bibtex
DVIPS=${texpath}dvips
TARGETS= current_research.ps


all: cv cv_nopubs pubs cv_terse cv_terse_withobs
	python update_journals.py
	${PDFLATEX} pubs.tex
	#gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=merged.pdf coverletter.pdf ginsburg_cv.pdf current_research.pdf proposal.pdf
	#${PDFLATEX} merged.tex

cv_nopubs:
	${PDFLATEX} cv_nopubs.tex

mwe: clean
	${PDFLATEX} mwe.tex
	${BIBTEX} mwe
	${PDFLATEX} mwe.tex
	${BIBTEX} mwe
	${PDFLATEX} mwe.tex

pubs: clean
	python add_citations.py
	python update_journals.py
	${PDFLATEX} pubs.tex
	${BIBTEX} pubs
	${PDFLATEX} pubs.tex
	${BIBTEX} pubs
	${PDFLATEX} pubs.tex

cv: clean
	${PDFLATEX} cv.tex
	${BIBTEX} cv
	${PDFLATEX} cv.tex
	${BIBTEX} cv
	${PDFLATEX} cv.tex

cv_terse_withobs:
	${PDFLATEX} cv_terse_withobs.tex
	${BIBTEX} cv_terse_withobs
	${PDFLATEX} cv_terse_withobs.tex
	${BIBTEX} cv_terse_withobs
	${PDFLATEX} cv_terse_withobs.tex

cv_terse:
	${PDFLATEX} cv_terse.tex
	${BIBTEX} cv_terse
	${PDFLATEX} cv_terse.tex
	${BIBTEX} cv_terse
	${PDFLATEX} cv_terse.tex

cv_nrao:
	${PDFLATEX} cv_nrao.tex
	${BIBTEX} cv_nrao
	${PDFLATEX} cv_nrao.tex
	${BIBTEX} cv_nrao
	${PDFLATEX} cv_nrao.tex


cv_nsfstyle: clean
	${PDFLATEX} cv_nsfstyle.tex
	#${BIBTEX} cv_nsfstyle
	${PDFLATEX} cv_nsfstyle.tex
	#${BIBTEX} cv_nsfstyle
	#${PDFLATEX} cv_nsfstyle.tex


cv_nasa_1page:
	touch biba.blah
	touch bibb.blah
	rm biba.*
	rm bibb.*
	${PDFLATEX} cv_nasa_1page.tex
	#${BIBTEX} cv_nasa_1page
	${BIBTEX} biba
	#${BIBTEX} bibb
	${PDFLATEX} cv_nasa_1page.tex
	#${BIBTEX} cv_nasa_1page
	${BIBTEX} biba
	#${BIBTEX} bibb
	${PDFLATEX} cv_nasa_1page.tex
	${PDFLATEX} cv_nasa_1page
	gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pdfwrite -dFirstPage=1 -dLastPage=1 -sOutputFile=cv_nasa_1page_b.pdf cv_nasa_1page.pdf

cv_nasa_2page:
	touch biba.blah
	touch bibb.blah
	rm biba.*
	rm bibb.*
	${PDFLATEX} cv_nasa_2page.tex
	#${BIBTEX} cv_nasa_2page
	${BIBTEX} biba
	#${BIBTEX} bibb
	${PDFLATEX} cv_nasa_2page.tex
	#${BIBTEX} cv_nasa_2page
	${BIBTEX} biba
	#${BIBTEX} bibb
	${PDFLATEX} cv_nasa_2page.tex
	${PDFLATEX} cv_nasa_2page

cv_nsf_2page: pubs
	touch biba.blah
	touch bibb.blah
	rm biba.*
	rm bibb.*
	${PDFLATEX} cv_nsf_2page.tex
	#${BIBTEX} cv_nsf_2page
	${BIBTEX} biba
	${BIBTEX} bibb
	${PDFLATEX} cv_nsf_2page.tex
	#${BIBTEX} cv_nsf_2page
	${BIBTEX} biba
	${BIBTEX} bibb
	${PDFLATEX} cv_nsf_2page.tex

cv_erc:
	${PDFLATEX} cv_erc.tex
	${BIBTEX} cv_erc
	${PDFLATEX} cv_erc.tex
	${BIBTEX} cv_erc
	${PDFLATEX} cv_erc.tex

cv_withrefs:
	${PDFLATEX} cv_withrefs.tex
	${BIBTEX} cv_withrefs
	${PDFLATEX} cv_withrefs.tex
	${BIBTEX} cv_withrefs
	${PDFLATEX} cv_withrefs.tex


clean: 
	@rm -f *.aux *.bbl *.blg *.dvi *.log *.out *.idv *.lg *.bcf

