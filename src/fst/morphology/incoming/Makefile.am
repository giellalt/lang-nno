# Makefil for å konvertera frå Norsk ordbank-data til lexc.

all: generated_nn_lexc/stems/nouns.lexc generated_nn_lexc/stems/verbs.lexc generated_nn_lexc/stems/adjectives.lexc generated_nn_lexc/affixes/nouns.lexc generated_nn_lexc/affixes/verbs.lexc generated_nn_lexc/affixes/adjectives.lexc

generated_nn_lexc/.stamp: ordbank_nn/fullformer_2012.txt.zip ordbank_nn/paradigme_nn.txt $(srcdir)/convert_ordbank_nn.py
	$(AM_V_GEN)python3 $(srcdir)/convert_ordbank_nn.py --out-dir generated_nn_lexc
	$(AM_V_GEN)touch $@

generated_nn_lexc/stems/nouns.lexc generated_nn_lexc/stems/verbs.lexc generated_nn_lexc/stems/adjectives.lexc generated_nn_lexc/affixes/nouns.lexc generated_nn_lexc/affixes/verbs.lexc generated_nn_lexc/affixes/adjectives.lexc: generated_nn_lexc/.stamp
	@true

clean-local:
	-rm -rf generated_nn_lexc
	-rm -f ordbank_nn/fullform_nn.txt
