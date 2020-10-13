# Makefil for å konvertera frå fullformsliste til lexc.

all: ../root.lexc

fullform.utf8.txt: ordbank_nn/fullform_nn.txt
	$(AM_V_GEN)iconv -f ISO-8859-1 -t UTF-8 $< | tail +27 > $@

tags.txt: fullform.utf8.txt Makefile.am
	$(AM_V_GEN)cut -f4 < $<    \
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

entries.lexc: fullform.utf8.txt $(srcdir)/parse-nno.pl
	$(AM_V_GEN)perl $(srcdir)/parse-nno.pl < $< \
		| sed -e 's/\+normert//g' \
		| sed -e 's/\+unormert/\+Err\/Orth/g' \
		> $@

../root.lexc: tags.txt entries.lexc
	$(AM_V_GEN)echo "Multichar_Symbols" > $@
	$(AM_V_GEN)echo                    >> $@
	$(AM_V_GEN)cat $<                  >> $@
	$(AM_V_GEN)echo                    >> $@
	$(AM_V_GEN)echo "+Symbol !!≈ * @CODE@ = symbols in the text, like £, €, ©" >> $@
	$(AM_V_GEN)echo                    >> $@
	$(AM_V_GEN)echo "LEXICON Root"     >> $@
	$(AM_V_GEN)echo " Punctuation ;"   >> $@
	$(AM_V_GEN)echo " Symbols ;"       >> $@
	$(AM_V_GEN)echo " Entries ;"       >> $@
	$(AM_V_GEN)echo                    >> $@
	$(AM_V_GEN)echo "LEXICON Entries"  >> $@
	$(AM_V_GEN)cat entries.lexc        >> $@

clean-local:
	-rm -f tags.txt entries.lexc fullform.utf8.txt
