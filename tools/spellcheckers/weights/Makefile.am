## Process this file with automake to produce Makefile.in
## Copyright: Sámediggi/Divvun/UiT
## Licence: GPL v3+


GIELLA_RAW_DESKTOP_SPELLER_CORPUS=spellercorpus.raw.txt
GIELLA_CLEAN_DESKTOP_SPELLER_CORPUS=spellercorpus.clean.txt

GIELLA_RAW_MOBILE_SPELLER_CORPUS=$(GIELLA_RAW_DESKTOP_SPELLER_CORPUS)
GIELLA_CLEAN_MOBILE_SPELLER_CORPUS=$(GIELLA_CLEAN_DESKTOP_SPELLER_CORPUS)

# Build raw corpus from ngram6:
spellercorpus.raw.txt: ngram6-1-topp1000.txt
	$(AM_V_GEN)sed -e 's/<s>//g' -e 's/<\/s>//g' < $< \
		| tr -s ' ' \
		| perl $(dir $<)/Repeat-ngram.pl \
		> $@

include $(top_srcdir)/../giella-core/am-shared/tools-spellcheckers-fstbased-desktop-weighting-dir-include.am
