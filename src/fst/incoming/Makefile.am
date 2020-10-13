# Makefil for å konvertera frå fullformsliste til lexc.

all: ../root.lexc

fullform.utf8.txt: ordbank_nn/fullform_nn.txt
	iconv -f ISO-8859-1 -t UTF-8 $< | tail +27 > $@

tags.txt: fullform.utf8.txt Makefile
	cut -f4 < $<    \
		| tr '+' '_' \
		| sed -e 's/< /</'  \
		| sed -e 's/ >/>/'  \
		| sed -e 's/<\./</' \
		| sed -e 's/\.>/>/' \
		| tr '(' '/' \
		| tr ' ' '\n' \
		| grep -v '^$$'\
		| grep -v '^<>$$'\
		| sort | uniq   \
		| grep -v '^\.'  \
		| grep -v '\.$$'  \
		| sed -e 's/</%</g' \
		| sed -e 's/>/%>/g' \
		| sed -e 's/^/+/g' \
		> $@

entries.lexc: fullform.utf8.txt parse-nno.pl
	perl parse-nno.pl < $< \
		| sed -e 's/\+normert//g' \
		| sed -e 's/\+unormert/\+Err\/Orth/g' \
		> $@

../root.lexc: tags.txt entries.lexc
	echo "Multichar_Symbols" > $@
	echo                    >> $@
	cat $<                  >> $@
	echo                    >> $@
	echo "+Symbol !!≈ * @CODE@ = symbols in the text, like £, €, ©" >> $@
	echo                    >> $@
	echo "LEXICON Root"     >> $@
	echo " Punctuation ;"   >> $@
	echo " Symbols ;"       >> $@
	echo " Entries ;"       >> $@
	echo                    >> $@
	echo "LEXICON Entries"  >> $@
	cat entries.lexc        >> $@

clean-local:
	-rm -f tags.txt entries.lexc fullform.utf8.txt
