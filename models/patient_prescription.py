from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date

class PatientPrescription(models.Model):
    _name = "patient.prescription"
    _description = "Patient Prescription"

    prescription_serial = fields.Char(
        string="Prescription Serial",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New Prescription")
    )
    prescription_date = fields.Date('Date Of Formulation', default=date.today())

    patient_id = fields.Many2one(related="appointment_id.patient_id", readonly=True, store=True)
    appointment_id = fields.Many2one('patient.appointment')
    appointment_id_name = fields.Char('Appointment Name', related='appointment_id.appointment_serial', readonly=True)
    prescription_line_id = fields.One2many("patient.prescription.line", "prescription_id", string="Prescription Lines")
    notes = fields.Text("Notes")

    @api.model
    def create(self, vals):
        if vals.get('prescription_serial', _('New Prescription')) == _('New Prescription'):
            vals['prescription_serial'] = self.env['ir.sequence'].next_by_code('patient.appointment.prescription.sequence') or _('New Prescription')
        return super().create(vals)

    @api.constrains('prescription_line_id')
    def _check_prescription_lines(self):
        for record in self:
            if not record.prescription_line_id:
                raise ValidationError(_("The prescription must have at least one medicine line."))


class PatientPrescriptionLine(models.Model):
    _name = "patient.prescription.line"
    _description = "Patient Prescription Line"

    prescription_id = fields.Many2one('patient.prescription', string="Prescription")
    prescription_id_name = fields.Char(related='prescription_id.prescription_serial', string='Prescription ID', readonly=True)
    medicine_trade_name = fields.Char(string="Trade Name of Medicine")
    therapeutic_regimen = fields.Char(string="Therapeutic Regimen of Medicine")
