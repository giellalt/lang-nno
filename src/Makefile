# This is a makefile that builds the Northern Sami morphological parser
# *****************************************************************

LEX=nno-lex.txt \
	adj-nno-lex.txt \
    adv-nno-lex.txt \
    noun-nno-lex.txt \
    verb-nno-lex.txt \
    closed-nno-lex.txt \
    pp-nno-lex.txt \
    propernoun-nno-lex.txt \
    punct-nno-lex.txt \
	abbr-nno-lex.txt


#ifeq (victorio.uit.no, $(shell hostname))
#XFST = /opt/sami/xerox/c-fsm/ix86-linux2.6-gcc3.4/bin/fst -utf8
#LEXC = /opt/sami/xerox/bin/lexc -utf8
#TWOLC = /opt/sami/xerox/bin/twolc -utf8
#endif

XFST = xfst
LEXC = lexc
TWOLC = twolc


# Directories:
scripts=$(GTHOME)/gt/script

# The ultimate goal is to build inno.fst, the generator
# This goal depends on nno.save being up to date.

inno.fst: ../bin/inno.fst
../bin/inno.fst: ../bin/nno.fst \
				../bin/nno.save \
				../bin/tok.fst \
				../bin/nno-num.fst \
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
# This goal depends on nno.save and inituppercase.fst being up to date

nno.fst: ../bin/nno.fst
../bin/nno.fst: ../bin/nno.save \
				../bin/inituppercase.fst \
				../bin/allcaps.fst \
				../bin/tok.fst
	@echo
	@echo "*** Building nno.fst ***" ;
	@echo
	@printf "read regex @\"../bin/nno.save\" .o. \
	@\"../bin/inituppercase.fst\" ; \n\
	save stack ../bin/nno.fst \n\
	quit \n" > /tmp/nno-fst-script
	$(XFST) < /tmp/nno-fst-script
	@rm -f /tmp/nno-fst-script


# The second goal is to build the inituppercase.fst file
# This goal depends on inituppercase.regex

inituppercase.fst: ../bin/inituppercase.fst
../bin/inituppercase.fst: inituppercase.regex
	@echo
	@echo "*** Building inituppercase.fst ***" ;
	@echo
	@printf "read regex < inituppercase.regex \n\
	save stack ../bin/inituppercase.fst \n\
	quit \n" > /tmp/inituppercase-script
	$(XFST) < /tmp/inituppercase-script
	@rm -f /tmp/inituppercase-script


# This goal depends on allcaps.xfst

allcaps.fst: ../bin/allcaps.fst
../bin/allcaps.fst: allcaps.xfst
	@echo
	@echo "*** Building allcaps.fst ***" ;
	@echo
	@printf "source allcaps.xfst \n\
	save stack ../bin/allcaps.fst \n\
	quit \n" > /tmp/tok-script
	$(XFST) < /tmp/tok-script
	@rm -f /tmp/tok-script


# The third goal is to build nno.save
# This goal depends on twol-nno.bin and a bunch of lexicon files

nno.save: ../bin/nno.save
../bin/nno.save: ../bin/twol-nno.bin $(LEX)
	@echo
	@echo "*** Building nno.save ***" ;
	@echo
	printf "compile-source $(LEX) \n\
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

abbr: ../bin/abbr.txt
../bin/abbr.txt: $(scripts)/abbr-extract.pl \
				 $(scripts)/langTools/Util.pm \
				 $(LEX)
	@echo
	@echo "*** Extracting abbreviations from abbr-nno-lex.txt to abbr.txt ***" ;
	@echo
	@perl -I $(scripts) $(scripts)/abbr-extract.pl \
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


nno-num.fst: ../bin/nno-num.fst
../bin/nno-num.fst: nno-num.txt
	@echo
	@echo "*** Building $(notdir $@) ***" ;
	@echo
	$(XFST) -e "read lexc < $< " \
		-e "save stack   $@ " \
		-stop



# "make clean" is there to remove the binary files at will.

clean:
	@rm -f ../bin/*.fst ../bin/*.save ../bin/*.bin
