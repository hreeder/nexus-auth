timers = {};

function add_timer(i, timer) {
	if (!(timer["id"] in timers)) {
		timers[timer["id"]] = countdown(
			function(ts) {
				var style = "<font>";
				if (new Date(timer["time"] * 1000) < new Date()) {
					var style="<font color='red'>"
					if (ts.hours > 2) {
						tr = $("#"+timer["id"])
						tr.fadeOut("slow", function() {
							tr.remove();
							window.clearInterval(timers[timer["id"]]);
						});
						console.log("fading out timer "+timer["id"])
					}
				}
				document.getElementById("remaining." + timer["id"]).innerHTML = style+ts.days+"d "+ts.hours+"h "+ts.minutes+"m "+ts.seconds+"s </font>";
			},
			new Date(timer["time"] * 1000),
			countdown.DAYS|countdown.HOURS|countdown.MINUTES|countdown.SECONDS);
	}
}

function timer_to_row(i, timer) {
	if ($("#"+timer["id"]).length == 0) {
		timer["real_time"] = new Date(timer["time"] * 1000).toISOString();
		var template = $("#timer_template").html();
		var completed = Mustache.to_html(template, timer);
		$('#timers tr:last').after(completed);
	}
}

function load_timers() {
	console.log("trying to load new timers");
	timers_data = [];
	$.getJSON("api/timers", function(data) {
		timers_data = data;
		$.each(timers_data, timer_to_row);
		$.each(timers_data, add_timer);
	})
}
