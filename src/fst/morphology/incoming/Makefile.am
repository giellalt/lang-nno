# Makefil for å konvertera frå Norsk ordbank-data til lexc.

all: FORCE
	$(AM_V_GEN)python3 $(srcdir)/convert_ordbank_nn.py --stems-dir ../stems --affixes-dir ../affixes

FORCE:
	@true

.PHONY: all FORCE

../stems/nouns.lexc \
../stems/propernouns.lexc \
../stems/adjectives.lexc \
../stems/verbs.lexc \
../affixes/nouns.lexc \
../affixes/propernouns.lexc \
../affixes/adjectives.lexc \
../affixes/verbs.lexc: ordbank_nn/fullformer_2012.txt.zip ordbank_nn/paradigme_nn.txt $(srcdir)/convert_ordbank_nn.py
	$(AM_V_GEN)python3 $(srcdir)/convert_ordbank_nn.py --stems-dir ../stems --affixes-dir ../affixes

clean-local:
	-rm -f ordbank_nn/fullform_nn.txt
