

import json
import datetime
import logging
import functools
import werkzeug.wrappers
from .common import valid_response, invalid_response
from odoo import http
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.http import request

_logger = logging.getLogger(__name__)

def validate_token(func):
    """Decorator to validate API access token"""
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        
        access_token_data = request.env["api.access_token"].sudo().search(
            [("token", "=", access_token)], order="id DESC", limit=1
        )
        
        if not access_token_data or not access_token_data.is_valid():
            return invalid_response("access_token", "token seems to have expired or invalid", 401)
        
        request.update_env(user=access_token_data.user_id)
        return func(self, *args, **kwargs)
    
    return wrap


class DentalClinicAPI(http.Controller):
    
    @http.route("/api/login", methods=["POST"], type="json", auth="none", csrf=False, cors="*")
    def api_login(self, **kw):
        """
        Login endpoint for API access
        Expected JSON body: {"db": "database", "login": "username", "password": "password"}
        """
        try:
            db = kw.get("db")
            username = kw.get("login")
            password = kw.get("password")
            
            if not all([db, username, password]):
                return invalid_response(
                    "missing_credentials", 
                    "db, login, and password are required", 
                    400
                )
            
            # Authenticate user
            uid = request.session.authenticate(db, username, password)
            if not uid:
                return invalid_response(
                    "authentication_failed",
                    "Invalid credentials",
                    401
                )
            
            # Generate access token
            user = request.env["res.users"].sudo().browse(uid)
            access_token = request.env["api.access_token"].sudo().create_token(user.id)
            
            return {
                "success": True,
                "data": {
                    "uid": uid,
                    "access_token": access_token,
                    "company_id": user.company_id.id,
                    "company_name": user.company_id.name,
                    "name": user.name,
                    "email": user.email,
                }
            }
            
        except Exception as e:
            _logger.error(f"Login error: {str(e)}")
            return invalid_response("server_error", str(e), 500)
    
    @http.route("/api/logout", methods=["POST"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def api_logout(self, **kw):
        """Logout and invalidate token"""
        try:
            access_token = request.httprequest.headers.get("access_token")
            token_record = request.env["api.access_token"].sudo().search([
                ("token", "=", access_token)
            ])
            if token_record:
                token_record.unlink()
            
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            return invalid_response("logout_error", str(e), 500)
    
    # Patient endpoints
    @http.route("/api/patients", methods=["GET"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def get_patients(self, **kw):
        """Get all patients"""
        try:
            limit = int(kw.get("limit", 100))
            offset = int(kw.get("offset", 0))
            
            patients = request.env["patient.patient"].search_read(
                [], 
                limit=limit, 
                offset=offset,
                order="create_date desc"
            )
            
            return {
                "success": True,
                "data": patients,
                "total": request.env["patient.patient"].search_count([])
            }
        except Exception as e:
            return invalid_response("fetch_error", str(e), 500)
    
    @http.route("/api/patients/<int:patient_id>", methods=["GET"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def get_patient(self, patient_id, **kw):
        """Get specific patient"""
        try:
            patient = request.env["patient.patient"].search_read(
                [("id", "=", patient_id)],
                limit=1
            )
            
            if not patient:
                return invalid_response("not_found", "Patient not found", 404)
            
            return {
                "success": True,
                "data": patient[0]
            }
        except Exception as e:
            return invalid_response("fetch_error", str(e), 500)
    
    @http.route("/api/patients", methods=["POST"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def create_patient(self, **kw):
        """Create new patient"""
        try:
            required_fields = ["patient_name", "contact_number"]
            for field in required_fields:
                if field not in kw:
                    return invalid_response(
                        "missing_field", 
                        f"Field '{field}' is required", 
                        400
                    )
            
            patient = request.env["patient.patient"].create({
                "patient_name": kw.get("patient_name"),
                "contact_number": kw.get("contact_number"),
                "date_of_birth": kw.get("date_of_birth"),
                "gender": kw.get("gender"),
                "occupation": kw.get("occupation"),
                "marital_status": kw.get("marital_status"),
                "blood_type": kw.get("blood_type"),
            })
            
            return {
                "success": True,
                "data": {
                    "id": patient.id,
                    "patient_serial": patient.patient_serial,
                    "message": "Patient created successfully"
                }
            }
        except Exception as e:
            return invalid_response("create_error", str(e), 500)
    
    @http.route("/api/patients/<int:patient_id>", methods=["PUT"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def update_patient(self, patient_id, **kw):
        """Update patient"""
        try:
            patient = request.env["patient.patient"].browse(patient_id)
            if not patient.exists():
                return invalid_response("not_found", "Patient not found", 404)
            
            update_vals = {}
            allowed_fields = [
                "patient_name", "contact_number", "date_of_birth",
                "gender", "occupation", "marital_status", "blood_type"
            ]
            
            for field in allowed_fields:
                if field in kw:
                    update_vals[field] = kw[field]
            
            patient.write(update_vals)
            
            return {
                "success": True,
                "message": "Patient updated successfully"
            }
        except Exception as e:
            return invalid_response("update_error", str(e), 500)
    
    @http.route("/api/patients/<int:patient_id>", methods=["DELETE"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def delete_patient(self, patient_id, **kw):
        """Delete patient"""
        try:
            patient = request.env["patient.patient"].browse(patient_id)
            if not patient.exists():
                return invalid_response("not_found", "Patient not found", 404)
            
            patient.unlink()
            
            return {
                "success": True,
                "message": "Patient deleted successfully"
            }
        except Exception as e:
            return invalid_response("delete_error", str(e), 500)
    
    # Appointment endpoints
    @http.route("/api/appointments", methods=["GET"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def get_appointments(self, **kw):
        """Get appointments with optional filters"""
        try:
            domain = []
            
            # Add date filters if provided
            if kw.get("date_from"):
                domain.append(("start", ">=", kw.get("date_from")))
            if kw.get("date_to"):
                domain.append(("start", "<=", kw.get("date_to")))
            if kw.get("patient_id"):
                domain.append(("patient_id", "=", int(kw.get("patient_id"))))
            
            appointments = request.env["patient.appointment"].search_read(
                domain,
                order="start desc"
            )
            
            return {
                "success": True,
                "data": appointments
            }
        except Exception as e:
            return invalid_response("fetch_error", str(e), 500)
    
    @http.route("/api/appointments", methods=["POST"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def create_appointment(self, **kw):
        """Create new appointment"""
        try:
            required_fields = ["patient_id", "start", "stop"]
            for field in required_fields:
                if field not in kw:
                    return invalid_response(
                        "missing_field",
                        f"Field '{field}' is required",
                        400
                    )
            
            appointment = request.env["patient.appointment"].create({
                "patient_id": int(kw.get("patient_id")),
                "start": kw.get("start"),
                "stop": kw.get("stop"),
                "doctor_id": kw.get("doctor_id") and int(kw.get("doctor_id")),
                "chief_complain": kw.get("chief_complain"),
                "medical_history": kw.get("medical_history"),
                "clinical_examination": kw.get("clinical_examination"),
                "name": kw.get("name", "New Appointment"),
            })
            
            return {
                "success": True,
                "data": {
                    "id": appointment.id,
                    "message": "Appointment created successfully"
                }
            }
        except Exception as e:
            return invalid_response("create_error", str(e), 500)
    
    @http.route("/api/appointments/<int:appointment_id>", methods=["PUT"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def update_appointment(self, appointment_id, **kw):
        """Update appointment"""
        try:
            appointment = request.env["patient.appointment"].browse(appointment_id)
            if not appointment.exists():
                return invalid_response("not_found", "Appointment not found", 404)
            
            update_vals = {}
            allowed_fields = [
                "start", "stop", "doctor_id", "chief_complain",
                "medical_history", "clinical_examination", "name", "state"
            ]
            
            for field in allowed_fields:
                if field in kw:
                    if field in ["doctor_id"] and kw[field]:
                        update_vals[field] = int(kw[field])
                    else:
                        update_vals[field] = kw[field]
            
            appointment.write(update_vals)
            
            return {
                "success": True,
                "message": "Appointment updated successfully"
            }
        except Exception as e:
            return invalid_response("update_error", str(e), 500)
    
    @http.route("/api/appointments/<int:appointment_id>", methods=["DELETE"], type="json", auth="none", csrf=False, cors="*")
    @validate_token
    def delete_appointment(self, appointment_id, **kw):
        """Delete appointment"""
        try:
            appointment = request.env["patient.appointment"].browse(appointment_id)
            if not appointment.exists():
                return invalid_response("not_found", "Appointment not found", 404)
            
            appointment.unlink()
            
            return {
                "success": True,
                "message": "Appointment deleted successfully"
            }
        except Exception as e:
            return invalid_response("delete_error", str(e), 500)
