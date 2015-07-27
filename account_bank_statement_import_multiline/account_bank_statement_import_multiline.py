# -*- coding: utf-8 -*-
# Author be-cloud (Jerome Sonnet)
# Somme code from OFX importer

import logging
import StringIO
import csv
import dateutil.parser
import base64

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)

class account_bank_statement_import(osv.TransientModel):
    _inherit = "account.bank.statement.import"

    _columns = {
        'journal_id': fields.many2one('account.journal', string='Journal', help='Accounting journal related to the bank statement you\'re importing. It has be be manually chosen for statement formats which doesn\'t allow automatic journal detection (QIF for example).'),
        'hide_journal_field': fields.boolean('Hide the journal field in the view'),
    }

    def _get_hide_journal_field(self, cr, uid, context=None):
        return context and 'journal_id' in context or False

    _defaults = {
        'hide_journal_field': _get_hide_journal_field,
    }

    def import_file(self, cr, uid, ids, context=None):
        """ Process the file chosen in the wizard, create bank statement(s) and go to reconciliation. """

        import wdb
        wdb.set_trace()

        if context is None:
            context = {}
        #set the active_id in the context, so that any extension module could
        #reuse the fields chosen in the wizard if needed (see .QIF for example)
        ctx = dict(context)
        ctx['active_id'] = ids[0]

        data_file = self.browse(cr, uid, ids[0], context=ctx).data_file

        # Parse the file and build a list of statement organised as a tree [currency_code][account_number][statement_id]
        all_statements = self._parse_file(cr, uid, base64.b64decode(data_file).decode("ISO_8859")[3:], context=ctx)
        all_statement_ids = []
        all_notifications = []
        for currency_code, account_number, stmts_vals in currency_codes, account_numbers, stmts_vals_list:
            # Check raw data
            self._check_parsed_data(cr, uid, stmts_vals, context=ctx)
            # Try to find the bank account and currency in odoo
            currency_id, bank_account_id = self._find_additional_data(cr, uid, currency_code, account_number, context=ctx)
            # Try to find the journal
            journal_id = self._get_journal(cr, uid, currency_id, bank_account_id, account_number, context=ctx)
            # If no journal found, ask the user about creating one
            if not journal_id:
                return self._journal_creation_wizard(cr, uid, currency_id, account_number, bank_account_id, context=ctx)
            # Prepare statement data to be used for bank statements creation
            stmts_vals = super(account_bank_statement_import, self)._complete_stmts_vals(cr, uid, stmts_vals, journal_id, account_number, context=context)
            # Create the bank statements
            statement_ids, notifications = super(account_bank_statement_import, self)._create_bank_statements(cr, uid, stmts_vals, context=context)
            all_statement_ids.append(statement_ids)
            all_notifications.append(notifications)

        # Finally dispatch to reconciliation interface
        model, action_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'action_bank_reconcile_bank_statements')
        action = self.pool[model].browse(cr, uid, action_id, context=context)
        return {
            'name': action.name,
            'tag': action.tag,
            'context': {
                'statement_ids': all_statement_ids,
                'notifications': all_notifications
            },
            'type': 'ir.actions.client',
        }

    def _check_csv(self, cr, uid, file, context=None):
        try:
            dict = csv.DictReader(file, delimiter=';', quotechar='"')
        except:
            return False
        return dict

    def _parse_file(self, cr, uid, data_file, context=None):
        csv = self._check_csv(cr, uid, StringIO.StringIO(data_file), context=context)
        if not csv:
            return super(account_bank_statement_import, self)._parse_file(cr, uid, data_file, context=context)
        all_statements = {}
        try:
            for line in csv:
                currency = line['Statement currency']
                account_num = line['Account']
                statement_id = line['Statement number']
                vals_line = {
                    'date': dateutil.parser.parse(line['Entry date'], fuzzy=True).date(),
                    'name': line['Counterparty name']+line['Transaction motivation'],
                    'ref': line['Bank reference'],
                    'amount': float(line['Transaction amount'].replace(',','.')),
                    'unique_import_id': line['Bank reference'],
                    #'bank_account_id': bank_account_id,
                    #'partner_id': partner_id,
                }
                if (currency , account_num ,statement_id) in all_statements:
                    all_statements[currency , account_num ,statement_id].append(vals_line)
                else:
                    all_statements[currency , account_num ,statement_id] = [vals_line]
        except Exception, e:
            raise UserError(_("The following problem occurred during import. The file might not be valid.\n\n %s" % e.message))
        return all_statements


        vals_bank_statement = {
            'name': ofx.account.routing_number,
            'transactions': transactions,
            # WARNING: the provided ledger balance is not necessarily the ending balance of the statement
            # see https://github.com/odoo/odoo/issues/3003
            'balance_start': float(ofx.account.statement.balance) - total_amt,
            'balance_end_real': ofx.account.statement.balance,
        }
