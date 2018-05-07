{
	'name': 'Pickup Delivery',
	'version': '1.0',
	'author': 'Christyan Juniady and Associates',
	'maintainer': 'Christyan Juniady and Associates',
	'category': 'General',
	'sequence': 21,
	'website': 'http://www.chjs.biz',
	'summary': '',
	'description': """
		
	""",
	'author': 'Christyan Juniady and Associates',
	'images': [
	],
	'depends': ['base','web','account','chjs_dated_setting','hr','mail','fleet'],	
	'data': [
		'views/pickup_delivery_view.xml',
		'views/courier.xml',
		'views/sequence.xml',
		'reports/pickup_delivery.xml',
		'reports/report_print_trip_line.xml',
	],
	'demo': [
	],
	'test': [
	],
	'installable': True,
	'application': False,
	'auto_install': False,
	'qweb': [
	 ],
}