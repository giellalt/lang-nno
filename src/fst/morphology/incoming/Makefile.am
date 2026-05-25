# Makefil for å konvertera frå Norsk ordbank-data til lexc.

ORDBANK_FULLFORMS_ZIP=$(srcdir)/ordbank_nn/fullformer_2012.txt.zip
ORDBANK_PARADIGMS=$(srcdir)/ordbank_nn/paradigme_nn.txt
ORDBANK_CONVERTER=$(srcdir)/convert_ordbank_nn.py
ORDBANK_STEMS_DIR=$(abs_top_srcdir)/src/fst/morphology/stems
ORDBANK_AFFIXES_DIR=$(abs_top_srcdir)/src/fst/morphology/affixes
ORDBANK_VALENCY_CG3=$(abs_top_srcdir)/src/cg3/valency.cg3

all: FORCE
	$(AM_V_GEN)python3 $(ORDBANK_CONVERTER) \
		--fullforms-zip $(ORDBANK_FULLFORMS_ZIP) \
		--paradigms $(ORDBANK_PARADIGMS) \
		--stems-dir $(ORDBANK_STEMS_DIR) \
		--affixes-dir $(ORDBANK_AFFIXES_DIR) \
		--valency-cg3 $(ORDBANK_VALENCY_CG3)

FORCE:
	@true

.PHONY: all FORCE

clean-local:
	-rm -f ordbank_nn/fullform_nn.txt
