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
	address = fields.Char('address', required=True, compute="_compute_address")
	request_date = fields.Datetime('Requested Date', default=lambda self: fields.datetime.now())
	state = fields.Selection([
		('requested', 'Requested'),
		('ready', 'Ready'),
		('delayed', 'Delayed'),
		('excecuted', 'Executed'),
		('canceled', 'Canceled'),
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


class pickup_delivery_request_line(models.Model):
	
	_name = 'pickup.delivery.request.line'

	_description = 'Pickup delivery request line'

	header_id = fields.Many2one('pickup.delivery.request', string="Request", ondelete="cascade")
	product_id = fields.Many2one('product.product', string="Product", required=True)
	qty = fields.Float('Quantitiy', required=True)
	notes = fields.Text('notes')

	_sql_constraints = [
		('qty','CHECK(qty > 0 )','Quantity must be greater than 0')
	]
