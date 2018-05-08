import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)
import xlwt
import base64
import cStringIO
from datetime import datetime

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

	# @api.multi
	# def action_approve_all(self):
	# 	context = dict(self._context or {})
	# 	invoices = (context.get('active_ids'))
	# 	_logger.debug(invoices)
	# 	for record in invoices:
	# 		# _logger.debug(record)
	# 		fee_log = self.browse(record)
	# 		fee_log.write({'state' : 'approved'})

	# 	test2 = self.env['courier.fee.log'].search([])
	# 	_logger.debug(len(test2))
		

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
		fee_total = 0
		if(trip.courier_id.fee_setting_id):
			if(trip.courier_id.fee_setting_id.trip_fee==0):
				fee_total = trip.courier_id.fee_setting_id.address_fee
			else:
				fee_total = trip.courier_id.fee_setting_id.trip_fee
			_logger.debug(fee_total)
			executed_counter = 0
			for record in trip.trip_line_ids:
				if(record.execute_status == 'executed'):
					executed_counter = executed_counter + 1
			fee_total = fee_total + (executed_counter * trip.courier_id.fee_setting_id.delivered_bonus)
			self.write({
				'total_fee': fee_total,
			})
		else:
			raise ValidationError("Courier doesn't have fee_setting_id")
		
		return fee_total

# ==========================================================================================================================
class confirm_fee_log(models.Model):
	_name = "confirm.fee.log"
	
	@api.multi
	def action_approve_all(self):
		context = dict(self._context or {})
		invoices = self.env['courier.fee.log'].browse(context.get('active_ids'))
		_logger.debug(invoices)
		for record in invoices:
			# _logger.debug(record)
			record.write({'state' : 'approved'})

		test2 = self.env['courier.fee.log'].search([])
		_logger.debug(len(test2))

# ==========================================================================================================================

class courier_fee_log_report(models.TransientModel):
	_name =  "courier.fee.log.report"
	_inherit = "chjs.dated.setting"
	_description = "Setting fee untuk courier"

	name = fields.Char('Name')
	file_name = fields.Char('File Name')
	date_from = fields.Date('Date from')
	date_to = fields.Date('Date to')
	courier_id = fields.Many2one('hr.employee','Courier ID' , domain=[('fee_setting_id' ,'!=',False)])
	report = fields.Binary('Prepared file', filters='.xls', readonly=True)

	
	@api.multi
	def generate_xls_report(self):
		self.ensure_one()

		wb1 = xlwt.Workbook(encoding='utf-8')
		ws1 = wb1.add_sheet('Invoices Details')
		fp = cStringIO.StringIO()

		#Content/Text style
		header_content_style = xlwt.easyxf("font: name Helvetica size 20 px, bold 1, height 170;")
		sub_header_style = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170;")
		sub_header_content_style = xlwt.easyxf("font: name Helvetica size 10 px, height 170;")
		line_content_style = xlwt.easyxf("font: name Helvetica, height 170;")
		row = 1
		col = 0

		ws1.row(row).height = 500

		ws1.write_merge(row,row, 2, 6, self.courier_id.name+"'s Fee Log" , header_content_style)
		row += 2
		ws1.write(row, col+1, "From :", sub_header_style)
		ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
		row += 1
		ws1.write(row, col+1, "To :", sub_header_style)
		ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_to,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
		row += 1
		col += 1
		ws1.write(row,col,"Courier",sub_header_style)
		ws1.write(row+1,col,"Number of Trip",sub_header_style)
		ws1.write(row+2,col,"Total Fee",sub_header_style)
		ws1.write(row+3,col,"Paid",sub_header_style)

		col += 1
		#Searching for customer invoices
		fee_logs = self.env['courier.fee.log'].search([('courier_id','=',self.courier_id.id),('state','!=','rejected'),('create_date','>=',self.date_from),('create_date','<=',self.date_to)])
		all_inv_total = 0
		total_fee=0
		no_trip =0
		paid = 0
		for record in fee_logs:
			no_trip += 1
			total_fee += record.total_fee
			if(record.state == 'paid'):
				paid +=  record.total_fee


		ws1.write(row,col,self.courier_id.name,line_content_style)
		ws1.write(row+1,col,no_trip,line_content_style)
		ws1.write(row+2,col,total_fee,line_content_style)
		ws1.write(row+3,col,paid,line_content_style)
	
		wb1.save(fp)
		out = base64.encodestring(fp.getvalue())
		self.write({'report': out, 'file_name':str(self.courier_id.name)+"'s report "+str(self.date_from)+' to '+str(self.date_to)+'.xls'})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'courier.fee.log.report',
			'view_mode': 'form',
			'view_type': 'form',
			'res_id': self.id,
			'views': [(False, 'form')],
			'target': 'new',
		}
# ==========================================================================================================================

