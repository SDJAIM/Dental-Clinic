from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class AppointmentDentalProcedureLine(models.Model):
    _name = 'appointment.dental.procedure.line'
    _description = 'Appointment Dental Procedure Line'
    _rec_name = 'service_item_id'  # Optional, to display a proper name in tree/form views

    appointment_id = fields.Many2one(
        'patient.appointment',
        string="Appointment",
        ondelete='cascade',
        required=True,  # Recommended to avoid broken records
        index=True
    )

    tooth_no = fields.Selection(
        [(f'Tooth{i}', f'Tooth{i}') for i in range(1, 33)],
        string="Tooth number",
        tracking=True
    )

    service_item_id = fields.Many2one(
        'product.product',
        string='Procedure Name',
        domain=[('sale_ok', '=', True)],
        required=True,
        change_default=True
    )

    cost = fields.Float(
        related="service_item_id.lst_price",
        string='Procedure Cost',
        digits='Product Price',
        store=True,
        readonly=True
    )
