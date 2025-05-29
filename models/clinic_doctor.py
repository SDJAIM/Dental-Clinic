from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

from datetime import date, timedelta

class ClinicDoctor(models.Model):
    _name = "clinic.doctor"
    _rec_name = "doctor_name"
    _order = "doctor_name"

    doctor_name = fields.Char("Doctor Name", required=True)
    specialty = fields.Char("Specialty")
    license_number = fields.Char("Medical License Number")
    active = fields.Boolean(default=True)

    appointments = fields.One2many('patient.appointment', 'doctor_id', string="Appointments")
