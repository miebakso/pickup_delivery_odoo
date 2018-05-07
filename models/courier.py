import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)

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

	courier_id = fields.Many2one('hr.employee', 'Courier', ondelete="cascade", required=True)
	trip_id = fields.Many2one('pickup.delivery.trip', 'Trip', ondelete="cascade", required=True)
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
	@api.depends('name' , 'fee_type' , 'create_date')
	def _compute_name(self):
		for record in self:
			record.name =  str(record.fee_type) + ' fee for trip ' + record.create_date
	

	@api.one
	def action_approve(self):
		self.write({
			'state': 'approved',
		})

	@api.multi
	def action_approve_all(self):
		test1 = self.env['courier.fee.log'].search([])
		_logger.debug(len(test1))
		context = dict(self._context or {})
		invoices = self.browse(context.get('active_ids'))
		test = self.env['courier.fee.log'].search([])
		_logger.debug(len(test))
		for record in invoices:
			# _logger.debug(record)
			record.write({'state' : 'approved'})

		test2 = self.env['courier.fee.log'].search([])
		_logger.debug(len(test2))
		return True

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

		

	def calculate_fee(self, trip):
		if(trip.courier_id.fee_setting_id == False):
			raise ValidationError("Courer doesn't have fee_setting_id")

		if(trip.courier_id.fee_setting_id.trip_fee ):
			fee_total = trip.courier_id.fee_setting_id.address_fee
			_logger.debug("==================================================="+fee_total)
		else:
			fee_total = trip.courier_id.fee_setting_id.trip_fee

		executed_counter = 0
		for record in trip.trip_line_ids:
			if(record.execute_status == 'executed'):
				executed_counter = executed_counter + 1
		fee_total = fee_total + (executed_counter * trip.courier_id.fee_setting_id.delivered_bonus)
		self.write({
			'total_fee': 'fee_total',
		})

# ==========================================================================================================================

class courier_fee_log_report(models.TransientModel):
	_name =  "courier.fee.log.report"
	_inherit = "chjs.dated.setting"
	_description = "Setting fee untuk courier"

	name = fields.Char('Nama')
	date_from = fields.Date('Date from')
	date_to = fields.Date('Date to')
	courier_id = fields.Many2one('hr.employee','Courier ID' , domain=[('fee_setting_id' ,'!=',False)])

	
		
# ==========================================================================================================================


# class ClassABCD(ReportXlsx):

# 	def generate_xlsx_report(self, workbook, data, lines):
# 		current_date = strftime("%Y-%m-%d", gmtime())
# 		logged_users = self.env['res.users'].search([('id', '=', data['create_uid'][0])])
# 		sheet = workbook.add_worksheet()
# 		# add the rest of the report code here