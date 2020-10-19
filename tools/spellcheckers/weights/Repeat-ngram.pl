#!/bin/env perl

while (<>) {
    $string = $_ ;
    $string =~ s/^\s+//;
    $string =~ s/\s+$//;
    my ($gonger, $tekst) = split(/ /, $string, 2);
    print "$tekst" x $gonger ;
}
