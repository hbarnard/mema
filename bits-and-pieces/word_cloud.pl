
use HTML::TagCloud;



sub get_cloud_data {

    my ( $c, $db, $token ) = @_;
    my $cloud = {};

    my @records = $c->app->db->resultset('Cclite2::OmYellowpage')->search(
        undef,
        {
            columns => [qw/id subject description/]
        }
    );

    ###$c->app->log->debug('cloud data records are'  . Dumper @records) ;

    foreach my $record (@records) {
        my $data_hash_ref = { $record->get_columns };

        my @words = split( /\s/, ( $data_hash_ref->{'description'} . ' ' . $data_hash_ref->{'subject'} ) ),

          my $counter = 0;
        foreach my $word (@words) {
            $word =~ s/[^\w]$//;    #remove commas etc. etc.
            $cloud->{$word}++ if ( length($word) );
            $counter++;
        }
    }

    # reverse the word hash to give frequency -> set of words in frequency
    my $counter = 0;
    my %count;
    for my $key ( keys %$cloud ) {
        my $value = $cloud->{$key};
        push @{ $count{$value} }, $key;
    }

    # take a few of the top frequencies for the cloud
    foreach my $key ( reverse sort { $a <=> $b } keys %count ) {
        $counter++;
    }
    return $c->make_html_tag_cloud( \%count, 10, 20, undef );
}



=head3 make_html_tag_cloud

This is a nice to have,really.
FIXME: Embedded URL for ads below

=cut

sub make_html_tag_cloud {
    my $c = shift;

    my ( $keywords_hash_ref, $size_limit, $word_limit, $token ) = @_;

    my $cloud        = HTML::TagCloud->new;
    my $size_counter = 0;
    foreach my $key ( reverse sort { $a <=> $b } ( keys %$keywords_hash_ref ) ) {
        my $word_counter = 0;
        foreach my $entry ( @{ $keywords_hash_ref->{$key} } ) {
			# links to ads if a user is logged in, otherwise just 'words'
            if ( length( $c->session('login') ) > 0 ) {
                $cloud->add( $entry, "/search?value=$entry&type=ad", $key ) if ( $key > 0 && ( length($entry) > 5 ) );
            }
            else {
                $cloud->add_static( $entry, $key ) if ( $key > 0 && ( length($entry) > 5 ) );
            }

            $word_counter++;
            last if ( $word_counter == $word_limit );
        }
        $size_counter++;
        last if ( $size_counter == $size_limit );
    }
    return $cloud->html_and_css(25);
}

