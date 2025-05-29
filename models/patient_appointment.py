from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class PatientAppointment(models.Model):
    _name = "patient.appointment"
    _inherit = ["mail.thread"]
    _rec_name = "appointment_serial"
    _description = "Patient Clinic Appointment"

    appointment_serial = fields.Char(
        string="Appointment Serial", required=True, copy=False, readonly=True,
        index=True, default=lambda self: _("New Appointment")
    )

    patient_id = fields.Many2one('patient.patient', string="Patient Name", tracking=True)
    contact_number = fields.Char('Contact Number', tracking=True)

    appointment_status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Appointment Confirmed'),
        ('in_exam', 'Examination'),
        ('completed_exam', 'Examination Completed'),
        ('completed_appointment', 'Appointment Completed'),
        ('cancelled', 'Appointment Cancelled'),
    ], string="Appointment Status", default='draft', tracking=True)

    appointment_type = fields.Selection([
        ('reserve', 'Reserved Appointment'),
        ('in_person', 'Walk-in Appointment'),
    ], string="Appointment Reservation Type", tracking=True)

    doctor_id = fields.Many2one('clinic.doctor', string="Doctor Name", tracking=True)
    procedure_line_id = fields.One2many('dental.procedure.line', 'appointment_id', string='Procedures')
    chief_complaints = fields.Text("Chief Complains/Notes")
    appointment_attachment_line_id = fields.One2many('appointment.attachment.line', 'appointment_id')
    patient_appointment_prescription_id = fields.One2many('patient.prescription', 'appointment_id')

    name = fields.Char('Meeting Subject')

    start = fields.Datetime(
        'Start', required=True, tracking=True, default=fields.Datetime.now,
        help="Start date of the appointment"
    )

    stop = fields.Datetime(
        'Stop', required=True, tracking=True,
        compute='_compute_stop', store=True,
        help="End date of the appointment"
    )

    allday = fields.Boolean('All Day', default=False)

    duration = fields.Float(
        'Duration (hours)', compute='_compute_duration', store=True, readonly=False,
        help="Duration of the appointment in hours"
    )

    user_id = fields.Many2one('res.users', string='Assistant Name', default=lambda self: self.env.user)

    @api.depends('start', 'duration')
    def _compute_stop(self):
        for record in self:
            if record.start:
                record.stop = record.start + timedelta(minutes=round((record.duration or 1.0) * 60))
                if record.allday:
                    record.stop -= timedelta(seconds=1)
            else:
                record.stop = False

    def _get_duration(self, start, stop):
        if not start or not stop:
            return 0
        return round((stop - start).total_seconds() / 3600, 2)

    @api.depends('stop', 'start')
    def _compute_duration(self):
        for record in self.with_context(dont_notify=True):
            record.duration = self._get_duration(record.start, record.stop)

    @api.constrains('start', 'stop')
    def _check_dates(self):
        for record in self:
            if record.stop and record.start and record.stop < record.start:
                raise ValidationError(_("End time cannot be earlier than start time."))

    @api.model
    def create(self, vals):
        if vals.get('appointment_serial', _('New Appointment')) == _('New Appointment'):
            vals['appointment_serial'] = self.env['ir.sequence'].next_by_code('patient.appointment.sequence') or _('New Appointment')
        return super(PatientAppointment, self).create(vals)
