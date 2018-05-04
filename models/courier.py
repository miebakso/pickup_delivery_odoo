import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# ==========================================================================================================================

class courier_fee_setting(models.Model):

	_name =  "courier.fee.setting"
	_inherit = "chjs.dated.setting"
	_description = "Setting fee untuk courier"

	name = fields.Char('Nama Setting')
	fee_type = fields.Selection((
		('per_trip','per trip'),
		('per_address','per address')
		), 'fee_type', default="per_trip")
	trip_fee = fields.Float('Trip fee')
	address_fee = fields.Float('Address Fee')
	delivered_bonus = fields.Float('Delivered Bonus')

# ==========================================================================================================================

class hr_employee(models.Model):

	_inherit = "hr.employee"
	_description = "enployee yang merupakan courier"

	fee_setting_id = fields.Many2one('courier.fee.setting', 'setting fee', ondelete="cascade")
	courier_fee_log_ids = fields.One2many('courier.fee.log', 'courier_id', 'delivery log')

# ==========================================================================================================================

class courier_fee_log(models.Model):

	_name =  "courier.fee.log"
	_inherit = "mail.thread"
	_description = "Courier Log Fee"

	courier_id = fields.Many2one('hr.employee', 'Courier', ondelete="cascade")
	# trip_id = fields.Many2one('pickup.delivery.trip', 'Trip', ondelete="delete")
	name = fields.Char('Name', compute="_compute_name", store=True)
	total_fee = fields.Float('Total fee')
	state = fields.Selection((
			('draft','Draft'),
			('approved','Approved'),
			('paid','Paid'),
			('rejected','Rejected')
		),'State', default="draft")
	fee_type = fields.Selection((
		('per_trip','per trip'),
		('per_address','per address')
		), 'fee_type', default="per_trip")

	@api.multi
	def _compute_name(self):
		for record in self:
			self.write({
				'name': self.fee_type + ' fee for trip' + self.create_date
			})

	@api.one
	def action_approve(self):
		self.write({
			'state': 'approved',
		})


	@api.one
	def action_paid(self):
		self.write({
			'state': 'paid',
		})	

	@api.one
	def action_reject(self):
		self.write({
			'state': 'rejected',
		})

		

	def calculate_fee(trip):
		if(trip.courier_id.fee_setting_id == False):
			raise ValidationError("Courer doesn't have fee_setting_id")

		fee_total = trip.courier_id.fee_setting_id.trip_fee
		if(trip.courier_id.address_fee == 0):
			fee_total = trip.courier_id.fee_setting_id.address_fee
		executed_counter = 0
		for record in trip.trip_line_ids:
			if(record.execute_status == 'executed'):
				executed_counter = executed_counter + 1
		fee_total = fee_total + (executed_counter * trip.courier_id.fee_setting_id.devlivered_bonus)
		self.write({
			'total_fee': 'fee_total',
		})

# ==========================================================================================================================

class courier_fee_log_report(models.TransientModel):
	_name =  "courier.fee.log.report"
	_inherit = "chjs.dated.setting"
	_description = "Setting fee untuk courier"

	date_from = fields.Date('Date from')
	date_to = fields.Date('Date to')
	courier_id = fields.Many2one('hr.employee')

	
		


