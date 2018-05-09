function loadTab(element, mode) {
	var state = $(element).data('state');
	var pcont_el = $('#' + mode + '_content');

	$('.' + mode + '_tab').each(function (index) {
		$(this).parent().removeClass('active');
	});
	$(this).parent().addClass('active');
	pcont_el.empty();

	$.ajax({
		url: (mode == 'pickup' ? 'pickups' : 'deliveries') + '/state/' + state,
		type: 'get',
		dataType: 'html',
		traditional: true,
		success: function (response) {
			pcont_el.html(response);
		},
		error: function (response) {
			pcont_el.append('<h1>Tidak ada pengantaran/penjemputan yang ada.</h1>')
		}
	});
}

$(document).ready(function () {
	$('[name=request_date]').datetimepicker({
		format: 'YYYY-MM-DD HH:mm:ss',
	});

	$('.pickup_tab').on('click', function () {
		loadTab($(this), 'pickup');
	});

	$('.delivery_tab').on('click', function () {
		loadTab($(this), 'delivery');
	});

	$("a.pickup_tab[data-state='requested']").click();
	$("a.delivery_tab[data-state='requested']").click();

	$('.add-line').on('click', function () {
		var lines = $('.lines')

		$.ajax({
			url: '/pickups/request/add-line',
			type: 'get',
			dataType: 'html',
			traditional: true,
			success: function (response) {
				lines.append(response);
			},
			error: function (response) {
				lines.append('Error on request');
			}
		});
	});

	$('.lines').on('click', '.delete-line', function () {
		$(this).parent().parent().parent().remove();
	});
});