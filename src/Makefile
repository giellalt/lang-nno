# This is a makefile that builds the Northern Sami morphological parser
# *****************************************************************

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
	@xfst < /tmp/inno-fst-script
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
	@xfst < /tmp/nno-fst-script
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
	@xfst < /tmp/caseconv-script
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
	@xfst < /tmp/tok-script
	@rm -f /tmp/tok-script


# The third goal is to build nno.save
# This goal depends on twol-nno.bin and a bunch of lexicon files

nno.save: ../bin/nno.save
../bin/nno.save: ../bin/twol-nno.bin nno-lex.txt adj-nno-lex.txt \
	adv-nno-lex.txt noun-nno-lex.txt verb-nno-lex.txt \
	closed-nno-lex.txt pp-nno-lex.txt propernoun-nno-lex.txt \
	punct-nno-lex.txt
	@echo
	@echo "*** Building nno.save ***" ;
	@echo
	printf "compile-source nno-lex.txt adj-nno-lex.txt adv-nno-lex.txt \
	noun-nno-lex.txt verb-nno-lex.txt closed-nno-lex.txt \
	pp-nno-lex.txt propernoun-nno-lex.txt punct-nno-lex.txt \n\
	read-rules ../bin/twol-nno.bin \n\
	compose-result \n\
	save-result ../bin/nno.save \n\
	quit \n" > /tmp/nno-save-script
	@lexc < /tmp/nno-save-script
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
	@twolc < /tmp/twol-nno-script
	@rm -f /tmp/twol-nno-script

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
	@xfst < /tmp/tok-script
	@rm -f /tmp/tok-script


# "make clean" is there to remove the binary files at will.

clean:
	@rm -f ../bin/*.fst ../bin/*.save ../bin/*.bin




