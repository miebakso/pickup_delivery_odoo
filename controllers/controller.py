from openerp import http
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta, date
import re, werkzeug, json

class WebController(http.Controller):

# ==========================================================================================================================

	@http.route('/pickups', auth="user", type="http", website=True)
	def pickup_index(self, **kw):
		return http.request.render('pickup_delivery.pickup_index', {})

# ==========================================================================================================================

	@http.route('/pickups/request', auth="user", type="http", website=True)
	def pickup_request_index(self, **kw):
		product_model = http.request.env['product.product']
		return http.request.render('pickup_delivery.pickup_request_index', {
			'products': product_model.search([])
		})

# ==========================================================================================================================

	@http.route('/pickups/request/add-line', auth="user", type="http", website=True)
	def pickup_request_add_line(self, **kw):
		product_model = http.request.env['product.product']
		return http.request.render('pickup_delivery.pickup_request_line', {
			'products': product_model.search([])
		})

# ==========================================================================================================================

	@http.route('/pickups/request/submit', auth="user", methods=['POST'], type="http", website=True)
	def pickup_request_submit(self, **kw):
		pickup_request_model = http.request.env['pickup.delivery.request']
		pickup_request_line_model = http.request.env['pickup.delivery.request.line']

		pickup_obj = pickup_request_model.create({
			'partner_id': int(http.request.env.user.partner_id.id),
			'request_type': 'pickup',
			'request_date': datetime.strptime(kw['request_date'], DEFAULT_SERVER_DATETIME_FORMAT),
			'state': 'requested',
		})

		values = {
			'product_id': http.request.httprequest.form.getlist('product_id[]'),
			'qty': http.request.httprequest.form.getlist('qty[]'),
			'notes': http.request.httprequest.form.getlist('notes[]'),
		}
		lines = []
		i = 0
		while(i < len(values['product_id'])):
			pickup_lines_obj = pickup_request_line_model.create({
				'header_id': pickup_obj.id,
				'product_id': values['product_id'][i],
				'qty': values['qty'][i],
				'notes': values['notes'][i],
			})
			lines.append(pickup_lines_obj.id)
			i += 1

		pickup_obj.write({
			'line_ids': pickup_lines_obj,
		})

		return werkzeug.utils.redirect('/pickups')

# ==========================================================================================================================

	@http.route('/pickups/state/<string:state>', auth="user", type="http", website=True)
	def pickup_state(self, state, **kw):
		user_id = int(http.request.env.user.partner_id.id)

		request_model = http.request.env['pickup.delivery.request']
		if state == 'history':
			state = ('state','in',['executed','cancelled'])
		else:
			state = ('state','=',state)
		pickups = request_model.search([('partner_id','=',user_id),('request_type','=','pickup'),state])

		return http.request.render('pickup_delivery.pickup_list_inner', {
			'pickups': pickups,
		})

# ==========================================================================================================================

	@http.route('/deliveries', auth="user", type="http", website=True)
	def delivery_index(self, **kw):
		return http.request.render('pickup_delivery.delivery_index', {})

# ==========================================================================================================================

	@http.route('/deliveries/state/<string:state>', auth="user", type="http", website=True)
	def delivery_state(self, state, **kw):
		user_id = int(http.request.env.user.partner_id.id)

		request_model = http.request.env['pickup.delivery.request']
		if state == 'history':
			state = ('state','in',['executed','cancelled'])
		else:
			state = ('state','=',state)
		deliveries = request_model.search([('partner_id','=',user_id),('request_type','=','delivery'),state])

		return http.request.render('pickup_delivery.delivery_list_inner', {
			'deliveries': deliveries,
		})