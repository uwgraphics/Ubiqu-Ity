/* jQuery Scroll View Plugin - By Joe Kohlmann
 * by Joe Kohlmann <jkohlmann@wisc.edu>
 * MIT Licensed: http://opensource.org/licenses/mit-license.php
 */


(function( $ ){
	// Array Remove - By John Resig (MIT Licensed)
	// http://ejohn.org/blog/javascript-array-remove/
	Array.prototype.remove = function(from, to) {
		var rest = this.slice((to || from) + 1 || this.length);
		this.length = from < 0 ? this.length + from : from;
		return this.push.apply(this, rest);
	};

	// These are DOM elements.
	scrollViews = [];

	function resizeScrollBoxes() {
		$(scrollViews).each(function() {
			var scrollViewHeight = $(this).height();
			var scrollViewContentHeight = $(".content", this).height();

			// var scrollBoxHeight = scrollViewHeight / scrollViewContentHeight * 100 + "%";

			var linkedScrollViews = $(this).data("linked.scrollView");
			$(linkedScrollViews).each(function() {
				var $scrollBox = $(".scrollBox", this);
				var scrollBoxHeight = $(".content", this).height() * scrollViewHeight / scrollViewContentHeight;
				$scrollBox.css("height", scrollBoxHeight);
			});
		});
	}

	function scrollLinkedViews() {
		var linkedScrollViews = $(this).data("linked.scrollView");
		// console.log("Scrolling main view + " + linkedScrollViews.length + " linked views");

		var scrollPosition = this.scrollTop;
		var scrollRatio = ( scrollPosition + $(this).height() * scrollPosition / $(".content", this).height() ) / $(".content", this).height();

		$(linkedScrollViews).each(function() {
			// Update scrollTop for linked scroll views.
			var linkedScrollPosition = scrollRatio * ($(".content", this).height() - $(this).height() );
			$(this).get(0).scrollTop = linkedScrollPosition;

			// Update transform for scroll boxes of linked scroll views.
			var scrollBoxPosition = scrollRatio * ($(".content", this).height() - $(".scrollBox", this).height() );
			$(".scrollBox", this).css("top", scrollBoxPosition + "px");
			// $(".scrollBox", this).css("transform", "translate(0," + scrollBoxPosition + "px)");

			$("img", this).css("transform-origin", "50%," + scrollRatio * 100 + "%)");
		});
	}


	function dragScrollBox(e, dd) {
		var $scrollView = $(this).data("main.scrollView");

		// To do: compensate for the vertical position on the scroll box at which the user clicks.
		var mouseRelativeY = e.pageY - this.offsetTop - $(this).parent().parent().get(0).offsetTop;

		var proportionalDeltaY = (dd.deltaY) * $(".content", $scrollView).height() / $(this).parent().parent().height();
		if ($(this).parent().height() < $(this).parent().parent().height()) {
			proportionalDeltaY = (dd.deltaY) * $(".content", $scrollView).height() / $(this).parent().height();
		}
		$scrollView.get(0).scrollTop = $(this).data("startMainPosition.scrollView") + proportionalDeltaY;
	}

	function checkElement($element) {
		if ( ! $(".content", $element).get(0) ) {
			throw "Missing .content: things might not work right.";
		}

		if ( $(".content", $element).css("position") != "relative" ) {
			throw "Element's .content doesn't use relative positioning. Scroll boxes (if enabled) will behave erratically.";
		}
	}

	// Some global event setup.
	$(window).on("resize.scrollView", resizeScrollBoxes);

	var scrollEvent = "scroll";
	// if (Modernizr.touch) {
	// 	scrollEvent = "scrollstop";
	// }

	$.fn.scrollView = function(options) {

		var settings = $.extend({
			// These should be jQuery objects or DOM elements
			"linked": [],
			"linkedOptions": {}
		}, options);

		return this.each(function() {
			var $this = $(this);

			try {
				checkElement($this);
			} catch(err) {
				console.log(err);
			}

			$this.data("linked.scrollView", []).on(scrollEvent + ".scrollView", scrollLinkedViews);
			scrollViews.push( $this.get(0) );

			$(settings["linked"]).linkToScrollView($this.get(0), settings["linkedOptions"]);
		});
	};

	$.fn.linkToScrollView = function(mainScrollView, options) {

		var settings = $.extend({
			// These should be DOM elements.
			"showScrollBox": true,
			"dragScrollBox": true,
			"scrollBoxZIndex": null
		}, options);

		return this.each(function() {
			var $this = $(this);

			// Link this element to the specified main scroll view (or rather, the first one only; we don't support linking to multiple scroll views).
			var $scrollView = $( $(mainScrollView).get(0) );
			var scrollViewHeight = $scrollView.height();
			var scrollViewContentHeight = $(".content", $scrollView).height();
			var scrollBoxHeight = scrollViewHeight / scrollViewContentHeight * 100 + "%";

			if ( $.inArray($scrollView, scrollViews) ) {
				var linkedScrollViews = $scrollView.data("linked.scrollView");
				var arrayIndex = $.inArray($this.get(0), linkedScrollViews);

				if ( arrayIndex < 0 ) {
					linkedScrollViews.push( $this.get(0) );
				} else {
					throw "Attempting to link an element to a scroll view twice!";
				}
			} else {
				throw "Attempting to link an element to another element that is not a scrollView.";
			}

			// Scroll box setup.
			var $content = $(".content", $this);
			var $scrollBox = $(".scrollBox", $content);

			if (settings["showScrollBox"]) {
				// Create .scrollBox if it doesn't exist.
				if (! $scrollBox.get(0) ) {
					$scrollBox = $("<div class='scrollBox'></div>").prependTo($content);
					$this.data("createdScrollBox", true);
				}
				// Set scroll box height.
				$scrollBox.css("height", scrollBoxHeight).data("main.scrollView", $scrollView);
			}

			if (settings["dragScrollBox"]) {
				$scrollBox.addClass("draggable").on("draginit.scrollView", function() {
					$(this).data("startMainPosition.scrollView", $(this).data("main.scrollView").get(0).scrollTop);
					$("body").addClass("dragging");
				}).on("drag.scrollView", dragScrollBox)
				.on("dragend.scrollView", function() {
					$(this).removeData("startMainPosition.scrollView");
					$("body").removeClass("dragging");
				});
			}

			if (settings["scrollBoxZIndex"] !== null) {
				$scrollBox.css("z-index", settings["scrollBoxZIndex"]);
			}
		});

	};

	$.fn.unlinkFromScrollView = function(mainScrollView) {

		return this.each(function() {
			var $this = $(this);

			var $scrollView = $( $(mainScrollView).get(0) );

			if ( $.inArray($scrollView, scrollViews) ) {
				var linkedScrollViews = $scrollView.data("linked.scrollView");
				var arrayIndex = $.inArray($this.get(0), linkedScrollViews);

				if ( arrayIndex >= 0 ) {
					// John Resig's Array.prototype.remove() method.
					linkedScrollViews.remove(arrayIndex);
					if ( $this.data("createdScrollBox") ) {
						$(".scrollBox", $this).remove();
					}
				} else {
					throw "Attempting to unlink an element from a scroll view the former isn't linked to.";
				}
			} else {
				throw "Attempting to unlink an element from an element that is not a scrollView.";
			}
		});

	};

})( jQuery );
