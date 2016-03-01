# -*- coding: utf-8 -*-
# © 2014-2016 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields


class VatReport(models.AbstractModel):
    _name = 'report.l10n_nl_tax_declaration_reporting.tax_report_template'

    @api.multi
    def render_html(self, data=None):
        self.cr = self._cr
        self.uid = self._uid
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
            'l10n_nl_tax_declaration_reporting.tax_report_template')

        res = {}
        self.period_ids = []
        self.display_detail = data['form']['display_detail']
        _chart_tax_id = data['form']['chart_tax_id']
        _chart_tax_name = self.env['account.tax.code'].browse(
            _chart_tax_id).name

        _fiscalyear_id = data['form']['fiscalyear_id']
        _fiscalyear_name = self.env['account.fiscalyear'].browse(
            _fiscalyear_id).name

        _period_from_id = data['form']['period_from']
        if _period_from_id:
            _period_from_name = self.env['account.period'].browse(
                _period_from_id).name
        else:
            _period_from_name = 'Begin fy'

        _period_to_id = data['form']['period_to']
        if _period_to_id:
            _period_to_name = self.env['account.period'].browse(
                _period_to_id).name
        else:
            _period_to_name = 'End fy'

        res['periods'] = ''
        if data['form'].get('period_from', False) and\
                data['form'].get('period_to', False):
            self.period_ids = self.env['account.period'].build_ctx_periods(
                data['form']['period_from'],
                data['form']['period_to'])
            res['periods'] = ', '.join(self.env['account.period'].browse(
                self.period_ids).mapped('name')
            )

        tax_report_lines = self._get_lines(data['form']['based_on'],
                                           data['form']['company_id'])

        self.tax_code_error = ''
        _1AO = self._get_line_value('1a', 'omzet', tax_report_lines)
        _1AB = self._get_line_value('1a', 'btw', tax_report_lines)
        _1BO = self._get_line_value('1b', 'omzet', tax_report_lines)
        _1BB = self._get_line_value('1b', 'btw', tax_report_lines)
        _1CO = self._get_line_value('1c', 'omzet', tax_report_lines)
        _1CB = self._get_line_value('1c', 'btw', tax_report_lines)
        _1DO = self._get_line_value('1d', 'omzet', tax_report_lines)
        _1DB = self._get_line_value('1d', 'btw', tax_report_lines)
        _1EO = self._get_line_value('1e', 'omzet', tax_report_lines)
        _2AO = self._get_line_value('2a', 'omzet', tax_report_lines)
        _2AB = self._get_line_value('2a', 'btw', tax_report_lines)
        _3AO = self._get_line_value('3a', 'omzet', tax_report_lines)
        _3BO = self._get_line_value('3b', 'omzet', tax_report_lines)
        _3CO = self._get_line_value('3c', 'omzet', tax_report_lines)
        _4AO = self._get_line_value('4a', 'omzet', tax_report_lines)
        _4AB = self._get_line_value('4a', 'btw', tax_report_lines)
        _4BO = self._get_line_value('4b', 'omzet', tax_report_lines)
        _4BB = self._get_line_value('4b', 'btw', tax_report_lines)
        _5BB = self._get_line_value('5b', 'btw', tax_report_lines)

        _5AB = _1AB + _1BB + _1CB + _1DB + _2AB - _4AB - _4BB
        _5CB = _5AB - _5BB

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'time_now': fields.Datetime.now(),
            'chart': _chart_tax_name,
            'fiscalyear': _fiscalyear_name,
            'start_period': _period_from_name,
            'end_period': _period_to_name,
            'basedon': data['form']['based_on'],
            '_1AO': _1AO,
            '_1AB': _1AB,
            '_1BO': _1BO,
            '_1BB': _1BB,
            '_1CO': _1CO,
            '_1CB': _1CB,
            '_1DO': _1DO,
            '_1DB': _1DB,
            '_1EO': _1EO,
            '_2AO': _2AO,
            '_2AB': _2AB,
            '_3AO': _3AO,
            '_3BO': _3BO,
            '_3CO': _3CO,
            '_4AO': _4AO,
            '_4AB': _4AB,
            '_4BO': _4BO,
            '_4BB': _4BB,
            '_5AB': _5AB,
            '_5BB': _5BB,
            '_5CB': _5CB,
            'tax_code_error': self.tax_code_error,
        }

        return report_obj.render(
            'l10n_nl_tax_declaration_reporting.tax_report_template', docargs)

    def _get_line_value(self, code, code_type, tax_report_lines):
        try:
            return filter(lambda x: x[0] == code,
                          filter(lambda x: x[1] == code_type,
                                 tax_report_lines))[0][2]
        except:
            if not self.tax_code_error:
                self.tax_code_error = \
                    "Please add (BTW) or (omzet) to tax code: " + code
            else:
                self.tax_code_error += " and " + code
            return 0

    def _get_lines(self, based_on, company_id=False,
                   parent=False, level=0, context=None):
        period_list = self.period_ids
        res = self._get_codes(based_on, company_id, parent, level,
                              period_list, context=context)
        if period_list:
            res = self._add_codes(based_on, res, period_list, context=context)
        else:
            self.cr.execute("select id from account_fiscalyear")
            fy = self.cr.fetchall()
            self.cr.execute(
                "select id from account_period where fiscalyear_id = %s",
                (fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                period_list.append(p[0])
            res = self._add_codes(based_on, res, period_list, context=context)

        tax_report_lines = list(map(lambda x: (x[1].code, 'omzet'
                                    if '(omzet)' in x[1].name
                                    else 'btw' if '(BTW)' in x[1].name
                                    else 'error', int(round(x[2]))), res))

        return tax_report_lines

    def _get_codes(self, based_on, company_id,
                   parent=False, level=0, period_list=None, context=None):
        self.cr = self._cr
        self.uid = self._uid
        obj_tc = self.env['account.tax.code']
        tax_codes = obj_tc.with_context(based_on=based_on).search([
            ('parent_id', '=', parent),
            ('company_id', '=', company_id)
        ], order='sequence')

        res = []
        for code in tax_codes:
            res.append(('.' * 2 * level, code))

            res += self._get_codes(based_on, company_id,
                                   code.id, level + 1, context=context)
        return res

    def _add_codes(self, based_on, account_list=None,
                   period_list=None, context=None):
        if context is None:
            context = {}
        if account_list is None:
            account_list = []
        if period_list is None:
            period_list = []
        res = []
        for account in account_list:
            sum_tax_add = 0
            for period_ind in period_list:
                for code in self.env['account.tax.code'].with_context(
                    period_id=period_ind,
                    based_on=based_on).browse(account[1].id
                                              ):
                    sum_tax_add = sum_tax_add + code.sum_period

            code.sum_period = sum_tax_add

            res.append((account[0], code, sum_tax_add))
        return res
