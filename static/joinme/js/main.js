var JM;

$( document ).ready( function () {

	JM = ( function () {

		var $loginForm = $( "#loginForm" );

		var regEmail = /.+@.+\..+/i;

		var _init = function () {
			console.log( "JM is running." );

			_addListener();

			_addHashLink();

			$( "nav a[href='" + window.location.pathname + "']" ).parents( "li" ).addClass( "active" );
		};

		var _addListener = function () {

			$( "[data-fire]" ).click( function () {
				var fire = $( this ).data( "fire" );
				if ( fire == "totop" ) {
					$( "html, body" ).animate( { scrollTop: 0 } );
				}
				if ( fire == "print" ) {
					window.print();
				}
			} );

			$( ".category, .event" )
				.on( "click", _openCatEv )
				.hover( function() {
					$( this ).addClass( "shadow-z-4" );
				}, function() {
					$( this ).removeClass( "shadow-z-4" );
				} );

			$loginForm.find( "[data-type=submit]" ).click( function ( event ) {
				event.preventDefault();

				$( this ).parent( ".form-group" ).removeClass( "has-error has-success" );
				var $email = $( this ).parents( "#loginForm" ).find( "input[name=email]" );
				var $password = $( this ).parents( "#loginForm" ).find( "input[name=password]" );

				if ( $email !== undefined ) {
					if ( !regEmail.test( $email.val() ) ) {
						$email.parent( ".form-group" ).addClass( "has-error" );
					} else {
						$email.parent( ".form-group" ).addClass( "has-success" );
					}
				}

				if ( $password.val().length == 0 ) {
					$password.parent( ".form-group" ).addClass( "has-error" );
				} else {
					$password.parent( ".form-group" ).addClass( "has-success" );
				}

				if ( $loginForm.find( ".form-group.has-success" ).length == 2 ) {
					$loginForm.submit();
				}
			} );

			$loginForm.find( "input" ).on( "focus", function () {
				$( this ).parent( ".form-group" ).removeClass( "has-error" );
			} );

		};

		var _addHashLink = function() {

			var search = $( "form[role=search]" ).attr( "action" );

			function hasher ( str, param, offset, initial ) {
				var query = encodeURIComponent( str );
				return "<a href='" + search + "?q=" + query + "'>" + str + "</a>";
			}

			$( ".event" ).each( function( index, element ) {
				var $text = $( element ).find( ".panel-body > div:first" );
				var text = $text.text();
				var regexp = /(\#\w+)/g;
				var new_string = text.replace( regexp, hasher );
				$text.html( new_string );
			} );
		};

		var _openCatEv = function () {
			var $link = $( this ).find( ".panel-footer a" );
			var url = "";
			if ( $link.length > 0 ) {
				url = $link.eq( 0 ).attr( "href" );
				window.location.pathname = url;
			}
		};

		return {
			init: _init
		};

	}() );

	JM.init();
} );
