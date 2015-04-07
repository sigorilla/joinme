var HACK;

$( document ).ready( function() {

	HACK = ( function() {

		var _init = function() {
			console.log( "HACK is running." );

			_addListener();
		};

		var _addListener = function() {

			$( "[data-fire]" ).click( function() {
				var fire = $( this ).data( "fire" );
				if ( fire == "totop" ) {
					$( "html, body" ).animate( { scrollTop: 0 } );
				}
				if ( fire == "print" ) {
					window.print();
				}
			} );

		};

		return {
			init: _init,
		};

	}() );

	HACK.init();
} );
