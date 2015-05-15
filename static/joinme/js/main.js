var JM;

$( document ).ready( function() {

	JM = ( function() {

		var $loginForm = $( "#loginForm" )
		, $commentForm = $( "form#commentForm" )
		;

		var regEmail = /.+@.+\..+/i
		, csrftoken
		;

		var _init = function() {
			console.log( "JM is running." );

			csrftoken = getCookie('csrftoken');
			$.ajaxSetup( {
				beforeSend: function( xhr, settings ) {
					if ( !csrfSafeMethod( settings.type ) && sameOrigin( settings.url ) ) {
						xhr.setRequestHeader( "X-CSRFToken", csrftoken );
					}
				}
			} );

			_addListener();

			_addHashLink();

			$( "nav a[href='" + window.location.pathname + "']" ).parents( "li" ).addClass( "active" );

			$( ".event-rating" ).rating( {
				min: 0,
				max: 5,
				step: 0.5,
				size: "xs",
				showClear: false,
				showCaption: false,
				readonly: true,
				disabled: true,
			} );
		};

		var _addListener = function() {

			$( "[data-toggle='tooltip']" ).tooltip();

			$( "[data-fire]" ).click( function() {
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
					$( this ).addClass( "shadow-z-2" );
				}, function() {
					$( this ).removeClass( "shadow-z-2" );
				} );

			$loginForm.find( "[data-type=submit]" ).click( function( event ) {
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

			$loginForm.find( "input" ).on( "focus", function() {
				$( this ).parent( ".form-group" ).removeClass( "has-error" );
			} );

			$commentForm.submit( _saveComment );

		};

		var _addHashLink = function() {

			var search = $( "form[role=search]" ).attr( "action" );

			function hasher( str, param, offset, initial ) {
				var query = encodeURIComponent( str );
				return "<a href='" + search + "?q=" + query + "'>" + str + "</a>";
			}

			$( ".event, .event-detail" ).each( function( index, element ) {
				var $text = $( element ).find( ".panel-body .lead" );
				var text = $text.html();
				var regexp = /(\#\w+)/g;
				var new_string = text.replace( regexp, hasher );
				$text.html( new_string );
			} );
		};

		var _openCatEv = function() {
			var $link = $( this ).find( ".panel-footer a" );
			var url = "";
			if ( $link.length > 0 ) {
				url = $link.eq( 0 ).attr( "href" );
				// window.location.pathname = url;
			}
		};

		var _saveComment = function( event ) {
			event.preventDefault();
			var path = location.path;
			var $message = $commentForm.find( "textarea[name=message]" );
			var message = $.trim( $message.val() );
			if ( message != "" ) {
				var output = {
					"csrfmiddlewaretoken": $commentForm.find( "input[name=csrfmiddlewaretoken]" ).val(),
					"message": message,
				};
				$.ajax( {
					type: "POST",
					url: "comment/",
					data: output,
					dataType: "json",
					success: function( data ) {
						console.log( data );
						if ( data["error"] ) {
							console.log( "Something is wrong." );
						} else {
							var $template = $( "<div class='list-group-item comment'>" + 
								"<div class='row-picture comment-user-photo'></div>" + 
								"<div class='row-content'>" + 
									"<div class='least-content comment-date'></div>" + 
									"<h4 class='list-group-item-heading comment-username'></h4>" + 
									"<p class='list-group-item-text comment-message'></p>" + 
								"</div>" + 
							"</div>" );
							$template.attr( "id", "comment-" + data["comment"]["id"] );
							if ( data["user_photo"] != "" ) {
								$template.find( ".comment-user-photo" )
								.html( "<img class='circle' src='" + data["user_photo"] + 
									"' alt='icon'>" );
							} else {
								$template.find( ".comment-user-photo" )
								.html( "<i class='mdi-social-person'></i>" );
							}
							$template.find( ".comment-username" ).text( data["username"] );
							$template.find( ".comment-date" ).text( data["comment"]["date"] );
							$template.find( ".comment-message" ).text( message );
							$( "#comments" ).find( ".well" ).remove();
							if ( $( "#comments .list-group" ).length == 0 ) {
								$( "#comments" ).prepend( "<div class='list-group'></div>" );
							}
							$( "#comments .list-group" ).append( $template );
							$( "#comments .list-group" )
							.append( "<div class='list-group-separator'></div>" );
							$message.val( "" );
						}
					},
					error: function( jqXHR, textStatus, errorThrown ) {
						console.log( jqXHR, textStatus, errorThrown );
					}
				} );
			} else {
				console.log( "Enter message!" );
			}
		};

		var getCookie = function( name ) {
			var cookieValue = null;
			if ( document.cookie && document.cookie != "" ) {
				var cookies = document.cookie.split( ";" );
				for ( var i = 0; i < cookies.length; i++ ) {
					var cookie = jQuery.trim( cookies[ i ] );
					// Does this cookie string begin with the name we want?
					if ( cookie.substring( 0, name.length + 1 ) == ( name + "=" ) ) {
						cookieValue = decodeURIComponent( cookie.substring( name.length + 1 ) );
						break;
					}
				}
			}
			return cookieValue;
		};

		var csrfSafeMethod =function( method ) {
			return ( /^(GET|HEAD|OPTIONS|TRACE)$/.test( method ) );
		};

		var sameOrigin = function( url ) {
			var host = document.location.host;
			var protocol = document.location.protocol;
			var sr_origin = "//" + host;
			var origin = protocol + sr_origin;
			// Allow absolute or scheme relative URLs to same origin
			return ( url == origin || url.slice( 0, origin.length + 1 ) == origin + "/" ) ||
				( url == sr_origin || url.slice( 0, sr_origin.length + 1 ) == sr_origin + "/" ) ||
				// or any other URL that isn't scheme relative or absolute i.e relative.
				!( /^(\/\/|http:|https:).*/.test( url ) );
		};

		return {
			init: _init
		};

	}() );

	JM.init();
} );
