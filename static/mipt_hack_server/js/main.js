var HACK;

$( document ).ready( function () {

	HACK = ( function () {

		var $loginForm = $( "#loginForm" );

		var regEmail = /.+@.+\..+/i;

		var _init = function () {
			console.log( "HACK is running." );

			_addListener();
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

			$loginForm.find( "[data-type=submit]" ).click( function ( event ) {
				event.preventDefault();

				var checkin = true;

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

			$loginForm.find( "input" ).on( "focus", function ( event ) {
				$( this ).parent( ".form-group" ).removeClass( "has-error" );
			} );

		};

		return {
			init: _init,
		};

	}() );

	HACK.init();
} );
