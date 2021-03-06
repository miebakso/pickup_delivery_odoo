from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from datetime import datetime, timedelta, date
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# ==========================================================================================================================

class pickup_delivery_request(models.Model):
	_name = 'pickup.delivery.request'

	_description = 'Pickup delivery request'

	partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete="restrict")
	name = fields.Char('Request Number')
	request_type = fields.Selection([
		('pickup', 'Pickup'),
		('delivery', 'Delivery'),
	], 'Request Type', required=True)
	address = fields.Char('Address', required=True, compute="_compute_address")
	request_date = fields.Datetime('Requested Date', default=lambda self: fields.datetime.now())
	state = fields.Selection([
		('requested', 'Requested'),
		('ready', 'Ready'),
		('delayed', 'Delayed'),
		('executed', 'Executed'),
		('cancelled', 'Cancelled'),
	], 'State', required=True, default='requested')
	executed_date = fields.Datetime('Executed Date')
	line_ids = fields.One2many('pickup.delivery.request.line','header_id', 'Request Lines')

	@api.multi
	@api.depends('partner_id', 'partner_id.street')
	def _compute_address(self):
		res_partner_env = self.env['res.partner']
		for record in self:
			record.address = res_partner_env.browse(record.partner_id.id).street


	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('pickup.delivery.request.sequence')
		return super(pickup_delivery_request, self).create(vals)

# ==========================================================================================================================

class pickup_delivery_request_line(models.Model):

	_name = 'pickup.delivery.request.line'

	_description = 'Pickup delivery request line'

	header_id = fields.Many2one('pickup.delivery.request', string="Request", ondelete="cascade")
	product_id = fields.Many2one('product.product', string="Product", required=True)
	qty = fields.Float('Quantity', required=True)
	notes = fields.Text('Notes')

	_sql_constraints = [
		('qty','CHECK(qty > 0 )','Quantity must be greater than 0')
	]

# ==========================================================================================================================

class pickup_delivery_trip(models.Model):
	_name = "pickup.delivery.trip"
	_description = "Pickup and delivery trip"

	name = fields.Char('No. Trip')
	courier_id = fields.Many2one('hr.employee', 'Courier', ondelete='restrict', required=True)
	vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', ondelete='restrict', required=True)
	departure_date = fields.Datetime('Departure Date')
	finished_date = fields.Datetime('Finished Date')
	state = fields.Selection([
		('draft', 'Draft'),
		('ready', 'Ready'),
		('on_the_way', 'On the Way'),
		('finished', 'Finished'),
		('cancelled', 'Cancelled'),
	], 'State', required=True, default='draft')
	trip_line_ids = fields.One2many('pickup.delivery.trip.line', 'trip_id', 'Trip Lines', required=True)

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('pickup.delivery.trip.sequence')
		return super(pickup_delivery_trip, self).create(vals)

	@api.multi
	def action_ready(self):
		self.write({
			'state': 'ready'
		})

	@api.multi
	def action_on_the_way(self):
		self.write({
			'state': 'on_the_way',
			'departure_date': fields.Date.context_today(self),
		})

	@api.multi
	def action_finished(self):
		for data in self:
			for record in data.trip_line_ids:
				if record.execute_status:
					print 'asd'
					if record.execute_status == 'execute':
						record.request_id.write({
							'state':'executed'
						})
					else:
						record.request_id.write({
							'state':'delayed'
						})
			data.write({
				'state': 'finished',
				'finished_date': fields.Date.context_today(self),
			})
		courier_fee = self.env['courier.fee.log']
		total_fee = courier_fee.calculate_fee(self)
		if(self.courier_id.fee_setting_id.fee_type):
			courier_fee.create({
				'courier_id': self.courier_id.id,
				'trip_id': self.id,
				'state': 'draft' ,
				'fee_type': self.courier_id.fee_setting_id.fee_type,
				'total_fee': total_fee,
			})



	@api.multi
	def action_cancelled(self):
		self.write({
			'state': 'cancelled'
		})

# ==========================================================================================================================

class pickup_delivery_trip_line(models.Model):
	_name = "pickup.delivery.trip.line"
	_description = "Pickup and Delivery Trip Line"

	trip_id = fields.Many2one('pickup.delivery.trip', 'Trip', ondelete='cascade')
	request_id = fields.Many2one('pickup.delivery.request', 'Request', ondelete='cascade', domain="[('state', 'in', ['requested','delayed'])]")
	request_desc = fields.Text('Description', compute="_compute_desc")
	address = fields.Text('Address', compute="_compute_address")
	delivery_type = fields.Selection([
		('employee', 'Employee'),
		('outsource', 'Outsource'),
	], 'Delivery Type', required=True, default='employee')
	expedition_id = fields.Many2one('pickup.delivery.expedition','Expedition')
	notes = fields.Text('Notes')
	execute_status = fields.Selection([
		('execute', 'Execute'),
		('not_execute', 'Not Execute'),
	], 'Execute Status')
	partner_pic = fields.Char('PIC')

	@api.multi
	@api.depends('request_id')
	def _compute_address(self):
		request_id_env = self.env['pickup.delivery.request']
		for record in self:
			record.address = request_id_env.browse(record.request_id.id).address

	@api.multi
	@api.depends('request_id')
	def _compute_desc(self):
		for record in self:
			tempNamaProduk = ""
			counter = 1
			for product in record.request_id.line_ids:
				tempNamaProduk = "%s %s. %s x %s pcs\n"%(tempNamaProduk,str(counter),product.product_id.name,str(product.qty))
				counter = counter + 1
			record.request_desc = "Nama Partner : %s\n Produk :\n %s "%(record.request_id.partner_id.name,tempNamaProduk)


# ==========================================================================================================================

class pickup_delivery_expedition(models.Model):
	_name = "pickup.delivery.expedition"

	name = fields.Char("Expedition")
