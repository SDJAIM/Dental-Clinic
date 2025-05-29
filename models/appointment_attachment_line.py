from odoo import api, fields, models, _
from datetime import date

class AppointmentAttachmentLine(models.Model):
    _name = "appointment.attachment.line"
    _description = "Appointment Attachment Line"

    # Relación con cita, poner string descriptivo para la relación
    appointment_id = fields.Many2one('patient.appointment', string='Appointment', required=True, ondelete='cascade')

    # Fecha de carga del archivo, por defecto el día actual
    attachment_deposition_date = fields.Date('Date of Deposition', default=date.today)

    # Archivo binario para almacenar adjuntos (PDF, imagen, etc)
    file = fields.Binary(string='Attachment File')

    # Opcional: nombre del archivo o descripción
    filename = fields.Char(string="File Name")
