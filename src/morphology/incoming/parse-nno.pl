#!/bin/env perl

sub reinsk_og_omform_taggar
{
	my ( $taggstreng ) = @_ ;
	$taggstreng =~ s/\+/_/;  # replace tag-internal + with _
	$taggstreng =~ s/< /</;  # remove space within subtags
	$taggstreng =~ s/ >/>/;  # remove space within subtags
	$taggstreng =~ s/<\./</; # correct faulty tags beginning with .
	$taggstreng =~ s/\.>/>/; # correct faulty tags ending in .
	$taggstreng =~ s/\(/\//; # correct faulty tags with (
	$taggstreng =~ s/<>//;   # Remove empty tags
	$taggstreng =~ s/ \. / /;# Remove single full stops
	$taggstreng =~ s/\s+/ /g;# Slå i hop fleire mellomrom
	@alle_taggar = split / /, $taggstreng ;
	foreach ( @alle_taggar ) {  
		$_ =~ s/^/+/;  
	}
	my $ferdige_taggar = join ('', @alle_taggar) ;
	return $ferdige_taggar ;
}

sub skjerm_spesialteikn
{
	my ( $ord ) = @_ ;
	$ord =~ s/%/%%/g;
	$ord =~ s/ /% /g;
	return $ord ;
}

while (<>)
{
	my ($ID, $lemma, $ordform, $taggar, $paradigme, $paradigmeline) = split /\t/;
	$lemma = skjerm_spesialteikn( $lemma ) ;
	$ordform = skjerm_spesialteikn( $ordform ) ;
	my $nytaggar = reinsk_og_omform_taggar ( $taggar ) ;
	print "$lemma$nytaggar:$ordform K ;\n";
}
