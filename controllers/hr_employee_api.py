# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, Controller, Response
from odoo.addons.web.controllers.main import serialize_exception
import json
import uuid


class EmployeeApi(Controller):
    _references_per_page = 20
    _fields = ['name', 'active', 'category_ids', 'address_home_id', 'country_id', 'gender', 'marital', 'birthday',
                  'work_phone', 'mobile_phone', 'work_email', 'work_location', 'department_id', 'parent_id', 'user_id']

    @http.route('/api/v1/login', auth='none', type='json', methods=['POST'], csrf=False)
    @serialize_exception
    def api_login(self, **post):
        content = {}
        if post.get('username') and post.get('password'):
            session = http.request.session
            user_id_login = http.request.session.authenticate(
                session['db'], post['username'], post['password'])
            if not user_id_login:
                content['message'] = 'Invalid username or password'
                return content
            users = request.env['res.users'].sudo().search([('id', '=', user_id_login)])
            if users:
                for user in users:
                    uid_ = user['id']
                    self.set_new_token(uid_)
                    content = {
                        'name': user['name'],
                        'token': user['api_token']
                    }
            return content

    @staticmethod
    def set_new_token(uid_):
        token = uuid.uuid4().hex
        check_token = http.request.env['res.users'].search(
            [('api_token', '=', token)])
        while check_token:
            token = uuid.uuid4().hex
            check_token = http.request.env['res.users'].search(
                [('api_token', '=', token)])
        http.request.env['res.users'].browse(uid_).sudo().write({'api_token': token})

    @http.route(['/api/v1/employees',
                 '/api/v1/employees/page/<int:page>'],
                 auth='public', type='http', methods=['GET'])
    def index(self, page=None, **kw):
        empls = request.env['hr.employee'].sudo()
        domain = []
        search_value = kw.get('search')
        if search_value:
            domain += [
                '|',
                ('name', 'ilike', search_value),
            ]

        employees = empls.search(domain).read(fields=self._fields)
        if page:
            offset = (page - 1) * self._references_per_page if page else 0
            employees = empls.search(domain, offset=offset, limit=self._references_per_page).\
                read(fields=self._fields)

        if len(employees) <= 0:
            return Response(json.dumps({'error': True, 'message': 'Record not found'}))

        return Response(json.dumps(employees),
                        content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/v1/employees/<int:id>', auth='public',
                type="http", methods=['GET'])
    def read(self, id, **kw):
        empl = request.env['hr.employee'].sudo().search([('id', '=', int(id))]).read(fields=self._fields)
        if len(empl) <= 0:
            return Response(json.dumps({'error': True, 'message': 'Record not found'}))
        return Response(json.dumps(empl), content_type='application/json;charset=utf-8', status=200)

    @http.route('/api/v1/employees', auth='public',
                type='json', methods=['POST'], csrf=False)
    def create(self, **kw):
        auth_token = request.httprequest.headers.get('Authorization')
        if not auth_token:
            return {'error': True, 'message': 'No authention token'}
        user = request.env['res.users'].sudo().search([('api_token', '=', auth_token)])
        if not user:
            return {'error': True, 'message': 'Invalid Token! Please try again'}
        if not request.httprequest.data:
            return {'error': True, 'message': 'Invalid Params! Please try again'}
        emp_data = http.request.params
        try:
            request.env['hr.employee'].sudo().create(emp_data)
        except:
            return {'error': True, 'message': 'Create error! Check your data'}
        return {'error': False, 'message': 'Create success'}

    @http.route('/api/v1/employees/<int:id>', auth='public', type='json', csrf=False, methods=['PUT'])
    def update(self, id, **kw):
        empl = request.env['hr.employee'].sudo().search([('id', '=', int(id))])
        if not empl:
            return {'error': True, 'message': 'Record not found'}
        if not http.request.params:
            return {'error': True, 'message': 'No params'}
        empl_data = http.request.params
        print(empl_data)
        try:
            empl.write(empl_data)
        except:
            return Response(json.dumps({'error': True, 'message': 'Update Error'}))

        return {'error': False, 'message': 'Update success'}

    @http.route('/api/v1/employees/<int:id>', auth='public', type='http', csrf=False, methods=['DELETE'])
    def delete(self, id):
        employee = request.env['hr.employee'].sudo().search([('id', '=', int(id))])
        auth_token = request.httprequest.headers.get('Authorization')
        user = request.env['res.users'].sudo().search([('api_token', '=', auth_token)])
        if not user:
            return Response(json.dumps({'error': True, 'message': 'No Authention! Try to login'}))
        if not employee:
            return Response(json.dumps({'error': True, 'message': 'Record not found'}))
        try:
            employee.write({'active': False})
        except:
            return Response(json.dumps({'error': True, 'message': 'Delete error'}))
        return Response(json.dumps({'error': False, 'message': 'Delete Success'}))











