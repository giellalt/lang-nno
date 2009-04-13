# This is a makefile that builds the Northern Sami morphological parser
# *****************************************************************

LEX=nno-lex.txt adj-nno-lex.txt \
    adv-nno-lex.txt noun-nno-lex.txt verb-nno-lex.txt \
    closed-nno-lex.txt pp-nno-lex.txt propernoun-nno-lex.txt \
    punct-nno-lex.txt \
	abbr-nno-lex.txt


XFST = xfst #-utf8
LEXC = lexc #-utf8
TWOLC = twolc #-utf8

ifeq (victorio.uit.no, $(shell hostname))
XFST = /opt/sami/xerox/c-fsm/ix86-linux2.6-gcc3.4/bin/fst -utf8
LEXC = /opt/sami/xerox/bin/lexc -utf8
TWOLC = /opt/sami/xerox/bin/twolc -utf8
endif


# The ultimate goal is to build inno.fst, the generator
# This goal depends on nno.save being up to date.

inno.fst: ../bin/inno.fst
../bin/inno.fst: ../bin/nno.fst ../bin/nno.save ../bin/tok.fst \
	../bin/allcaps.fst
	@echo
	@echo "*** Building the inverse inno.fst ***"
	@echo
	@printf "load ../bin/nno.save \n\
	invert net \n\
	save stack ../bin/inno.fst \n\
	quit \n" > /tmp/inno-fst-script
	$(XFST) < /tmp/inno-fst-script
	@rm -f /tmp/inno-fst-script

 
# The first goal is to build nno.fst, the analyzer.
# This goal depends on nno.save and caseconv.fst being up to date

nno.fst: ../bin/nno.fst
../bin/nno.fst: ../bin/nno.save ../bin/caseconv.fst ../bin/allcaps.fst \
	../bin/tok.fst
	@echo
	@echo "*** Building nno.fst ***" ;
	@echo
	@printf "read regex @\"../bin/nno.save\" .o. \
	@\"../bin/caseconv.fst\" ; \n\
	save stack ../bin/nno.fst \n\
	quit \n" > /tmp/nno-fst-script
	$(XFST) < /tmp/nno-fst-script
	@rm -f /tmp/nno-fst-script


# The second goal is to build the caseconv.fst file
# This goal depends on case.regex

caseconv.fst: ../bin/caseconv.fst
../bin/caseconv.fst: case.regex
	@echo
	@echo "*** Building caseconv.fst ***" ;
	@echo
	@printf "read regex < case.regex \n\
	save stack ../bin/caseconv.fst \n\
	quit \n" > /tmp/caseconv-script
	$(XFST) < /tmp/caseconv-script
	@rm -f /tmp/caseconv-script


# This goal depends on allcaps.regex

allcaps.fst: ../bin/allcaps.fst
../bin/allcaps.fst: allcaps.regex
	@echo
	@echo "*** Building allcaps.fst ***" ;
	@echo
	@printf "source allcaps.regex \n\
	save stack ../bin/allcaps.fst \n\
	quit \n" > /tmp/tok-script
	$(XFST) < /tmp/tok-script
	@rm -f /tmp/tok-script


# The third goal is to build nno.save
# This goal depends on twol-nno.bin and a bunch of lexicon files

nno.save: ../bin/nno.save
../bin/nno.save: ../bin/twol-nno.bin nno-lex.txt adj-nno-lex.txt \
	adv-nno-lex.txt noun-nno-lex.txt verb-nno-lex.txt abbr-nno-lex.txt \
	closed-nno-lex.txt pp-nno-lex.txt propernoun-nno-lex.txt \
	punct-nno-lex.txt
	@echo
	@echo "*** Building nno.save ***" ;
	@echo
	printf "compile-source nno-lex.txt adj-nno-lex.txt adv-nno-lex.txt \
	noun-nno-lex.txt verb-nno-lex.txt closed-nno-lex.txt abbr-nno-lex.txt \
	pp-nno-lex.txt propernoun-nno-lex.txt punct-nno-lex.txt \n\
	read-rules ../bin/twol-nno.bin \n\
	compose-result \n\
	save-result ../bin/nno.save \n\
	quit \n" > /tmp/nno-save-script
	$(LEXC) < /tmp/nno-save-script
	rm -f /tmp/nno-save-script


# The fourth goal is to build twol-nno.bin
# This goal depends on twol-nno.txt

twol-nno.bin: ../bin/twol.nno.bin
../bin/twol-nno.bin: twol-nno.txt
	@echo
	@echo "*** Building twol-nno.bin ***" ;
	@echo
	@printf "read-grammar twol-nno.txt \n\
	compile \n\
	save-binary ../bin/twol-nno.bin \n\
	quit \n" > /tmp/twol-nno-script
	$(TWOLC) < /tmp/twol-nno-script
	@rm -f /tmp/twol-nno-script


# Here we make the abbrevation file for our current preprocessor, 
# the perl-based preprocess (located in the script catalogue)
# This target is not yet in use.

empty:=
comma:=,
space:=$(empty) $(empty)
ABBRSRCS=$(subst $(space),$(comma),$(LEX))

scripts=$(HOME)/svnredone/gt/script

abbr: ../bin/abbr.txt
../bin/abbr.txt: $(scripts)/abbr-extract $(scripts)/langTools/Util.pm $(LEX)
	@echo
	@echo "*** Extracting abbreviations from abbr-kal-lex.txt to abbr.txt ***" ;
	@echo
	@perl -I $(scripts) $(scripts)/abbr-extract \
		--output=$@ \
		--abbr_lex=abbr-nno-lex.txt \
		--lex=$(ABBRSRCS)


# Here we include a preprocessor.
# This goal depends on tok.txt

tok.fst: ../bin/tok.fst 
../bin/tok.fst: tok.txt
	@echo
	@echo "*** Building the tokenizer tok.fst ***" ;
	@echo
	@printf "source tok.txt \n\
	save stack ../bin/tok.fst \n\
	quit \n" > /tmp/tok-script
	$(XFST) < /tmp/tok-script
	@rm -f /tmp/tok-script


# "make clean" is there to remove the binary files at will.

clean:
	@rm -f ../bin/*.fst ../bin/*.save ../bin/*.bin




