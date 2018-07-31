# latex Makefile
texpath=/usr/texbin/
#TEXINPUTS=.:/Users/adam/papers/latexfiles:
LATEX=${texpath}latex
PDFLATEX=${texpath}pdflatex -halt-on-error
BIBTEX=${texpath}bibtex
DVIPS=${texpath}dvips
TARGETS= current_research.ps


all: cv cv_nopubs pubs cv_terse cv_terse_withobs
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
	python update_journals.py
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

cv_nsfstyle: clean
	${PDFLATEX} cv_nsfstyle.tex
	#${BIBTEX} cv_nsfstyle
	${PDFLATEX} cv_nsfstyle.tex
	#${BIBTEX} cv_nsfstyle
	#${PDFLATEX} cv_nsfstyle.tex

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

