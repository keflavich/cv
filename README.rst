Adam Ginsburg's CV
------------------

The cv consists of a master file, `cv.tex`, and a number of files that can be
input.  The setup is designed to allow me to make smaller version of the cv for
various different applications, e.g., those that require that publications be
in a separate document or those that specify page limits.

The .bib file is customized to have ``\myname{}`` surrounding all instances
of my name so they can be bolded in the compiled cv.

``add_citations.py`` goes through mybib and queries ADS to determine the # of
citations each publication has, then it adds that information in a new field in
the `cv_cites.bib` file (which isn't tracked because it's generated).  

A custom .bst file, ``apj_revchron.bst``, prints the cited articles in reverse
chronological order including their # of citations if the field is available.

oy
