# Makefil for å konvertera frå fullformsliste til lexc.

all: entries.lexc tags.txt

fullform.utf8.txt: ordbank_nn/fullformer_2012.txt.zip
	$(AM_V_GEN)unzip -p $< |\
		 iconv -f ISO-8859-1 -t UTF-8 |\
		 sed '/Mac OS X/,$$d' |\
		 tail +1893 \
		 > $@

tags.txt: fullform.utf8.txt $(srcdir)/Makefile.am
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
		| sed -e 's/\+normert//g' \
		| sed -e 's/\+unormert/\+Err\/Orth/g' \
		> $@
	$(AM_V_GEN)echo '+Err/Lex' >> $@

entries.lexc: fullform.utf8.txt $(srcdir)/parse-nno.pl
	$(AM_V_GEN)perl $(srcdir)/parse-nno.pl < $< \
		| sed -e 's/\+normert//g' \
		| sed -e 's/\+unormert/\+Err\/Orth/g' \
		> $@

clean-local:
	-rm -f tags.txt entries.lexc fullform.utf8.txt
	-rm -f ordbank_nn/fullform_nn.txt
