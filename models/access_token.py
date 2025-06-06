import hashlib
import logging
import os
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

def random_token(length=40, prefix="access_token"):
    rbytes = os.urandom(length)
    return "{}_{}".format(prefix, hashlib.sha1(rbytes).hexdigest())

class APIAccessToken(models.Model):
    _name = "api.access_token"
    _description = "API Access Token"
    _sql_constraints = [
        ('token_unique', 'unique(token)', 'The access token must be unique.')
    ]

    token = fields.Char("Access Token", required=True, index=True)
    user_id = fields.Many2one("res.users", string="User", required=True, ondelete='cascade')
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)
    scope = fields.Char(string="Scope")

    def find_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token and access_token.has_expired():
            access_token = None

        if not access_token and create:
            expiry_dt = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(days=1)
            token_expiry_date = expiry_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "token_expiry_date": token_expiry_date,
                "token": random_token(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)
        if not access_token:
            return None
        return access_token.token

    def is_valid(self, scopes=None):
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        self.ensure_one()
        now = fields.Datetime.from_string(fields.Datetime.now())
        expiry = fields.Datetime.from_string(self.token_expiry_date)
        return now > expiry

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True
        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)
        return resource_scopes.issubset(provided_scopes)


class Users(models.Model):
    _inherit = "res.users"

    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")

    def sum_numbers(self, x, y):
        return x + y
