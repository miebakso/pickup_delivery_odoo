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

# ==========================================================================================================================

class pickup_delivery_trip(models.Model):
    _name = "pickup.delivery.trip"
    _description = "Pickup and delivery trip "

    name = fields.Char('No. Trip', require=True)
    courier_id = fields.Many2one('hr.employee', 'Courier', ondelete='restrict', require=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', ondelete='restrict', require=True)
    departure_date = fields.Datetime('Departure Date')
    finished_date = fields.Datetime('Finished Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('on_the_way', 'On The Way'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ], 'State', required=True, default='draft')
    trip_line_ids = fields.One2many('pickup.delivery.trip.line', 'trip_id', 'Trip Lines', required=True)

    @api.one
    def action_ready(self):
        self.write({
            'state': 'ready'
        })

    @api.one
    def action_on_the_way(self):
        self.write({
            'state': 'on_the_way',
            'departure_time': fields.Date.context_today(self),
        })

    @api.one
    def action_finished(self):
        self.write({
            'state': 'finished',
            'finished_time': fields.Date.context_today(self),
        })

    @api.one
    def action_cancelled(self):
        self.write({
            'state': 'cancelled'
        })

# ==========================================================================================================================


class pickup_delivery_trip_line(models.Model):
    _name = "pickup.delivery.trip.line"
    _description = "Pickup and Delivery Trip Line"

    trip_id = fields.Many2one('pickup.delivery.trip', 'Trip', ondelete='cascade')
    request_id = fields.Many2one('pickup.delivery.request', 'Request', ondelete='cascade', domain=[('state', '=', 'ready'), ('state', '=', 'delayed')])
    request_desc = fields.Text('Description')
    address = fields.Text('Address')
    delivery_type = fields.Selection([
        ('employee', 'Employee'),
        ('outsource', 'Outsource'),
    ], 'Delivery Type', required=True, default='employee')
    # expedition_id =
    notes = fields.Text('Notes')
    execute_status = fields.Selection([
        ('execute', 'Execute'),
        ('not_execute', 'Not Execute'),
    ], 'Execute Status')
    partner_pic = fields.Char('PIC')
