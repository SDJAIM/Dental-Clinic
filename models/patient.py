from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class Patient(models.Model):
    _name = "patient.patient"
    _inherit = ['mail.thread']
    _rec_name = "patient_name"

    patient_serial = fields.Char(
        string="Patient Serial",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New Patient")
    )

    patient_name = fields.Char(string='Patient Name', required=True)
    contact_number = fields.Char(string='Contact Number', tracking=True)

    appointment_id = fields.One2many('patient.appointment', 'patient_id', string="Appointments")
    date_of_birth = fields.Date(string='Date Of Birth', default=lambda self: fields.Date.today())

    age = fields.Char(string='Age In Years', compute="compute_age", store=True)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender", tracking=True)

    occupation = fields.Char(string='Occupation')

    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
    ], string="Marital Status", tracking=True)

    blood_type = fields.Selection([
        ('a-', 'A without Rh-factor'),
        ('a+', 'A with Rh-factor'),
        ('b-', 'B without Rh-factor'),
        ('b+', 'B with Rh-factor'),
    ], string="Blood Type", tracking=True)

    qstn_1 = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Medical History (Q1)")

    qstn_1_note = fields.Char(string="Q1 Notes")

    qstn_2 = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Medical History (Q2)")

    qstn_2_note = fields.Char(string="Q2 Notes")

    patient_prescriptions = fields.One2many('patient.prescription', 'patient_id', string="Prescriptions")

    @api.depends('date_of_birth')
    def compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                age = date.today() - rec.date_of_birth
                age_in_years = int(age.days // 365.2425)
                rec.age = f"{age_in_years} Years Old"
            else:
                rec.age = ""

    @api.model
    def create(self, vals):
        if vals.get('patient_serial', _('New Patient')) == _('New Patient'):
            vals['patient_serial'] = self.env['ir.sequence'].next_by_code('patient.sequence') or _('New Patient')
        return super(Patient, self).create(vals)

    _sql_constraints = [
        ('unique_patient_name_dob',
         'unique(patient_name, date_of_birth)',
         _('A patient with this name and date of birth already exists.'))
    ]
