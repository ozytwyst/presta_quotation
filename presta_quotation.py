# -*- coding: utf-8 -*-
##############################################################################
#
#    prestashop_quotation module for OpenERP, Create quotation from prestashop imports
#    Copyright (C) 2015 ozytwyst Julien Thomazeau <ozydev@julienthomazeau.fr>
#
#    This file is a part of prestashop_quotation
#
#    prestashop_quotation is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    prestashop_quotation is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from mail.mail_message import mail_message


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

class sale_order(osv.osv):
    _inherit = 'sale.order'
    def import_presta(self, cr, uid, *args):
        # On récupere les devis non enregistrés
        cr.execute("""SELECT * FROM prestashop.quotation WHERE id_sale_order IS NULL""")
        context = {}
        ids = {}
        orders = cr.dictfetchall();
        for presta_order in orders:
            vals = {
                'order_line' : []
            }
            # On recherche le client
            cr.execute(""" SELECT case when (SELECT id from res_partner WHERE email like %s and parent_id is null and active = true limit 1) is null then (SELECT id from res_partner WHERE id = (SELECT parent_id FROM res_partner WHERE email like %s limit 1)) else (SELECT id from res_partner WHERE email like %s and parent_id is null and active = true limit 1) end as partner_id """, (presta_order['email'], presta_order['email'],presta_order['email']))
            partner = cr.dictfetchone()
            # Si le client n'existe pas, on le créé
            if partner['partner_id'] is None:
                partner_vals = {
                 'name': presta_order['invoice_name'],
                 'street': presta_order['invoice_street'],
                 'street2': presta_order['invoice_street2'],
                 'zip': presta_order['invoice_zip'],
                 'city': presta_order['invoice_city'],
                 'country_id':413
                }
                new_partner = self.pool.get('res.partner')
                partner['partner_id'] = new_partner.create(cr, uid, partner_vals,context)
                if presta_order['invoice_id'] != presta_order['shipping_id']:
                    delivery_vals = {
                     'name': presta_order['shipping_name'],
                     'street': presta_order['shipping_street'],
                     'street2': presta_order['shipping_street2'],
                     'zip': presta_order['shipping_zip'],
                     'city': presta_order['shipping_city'],
                     'type': 'delivery',
                     'parent_id': partner['partner_id'],
                     'country_id':413 #id de la france
                    }
                    delivery_partner = self.pool.get('res.partner')
                    delivery_partner.create(cr,uid,delivery_vals,context)
            # On recupere les infos du client
            vals['partner_id'] = partner['partner_id']
            # On met a jour l'entete
            partner_infos = self.onchange_partner_id(cr, uid, ids, partner['partner_id'], context)
            vals.update(partner_infos['value'])
            # On recupere les lignes du devis
            cr.execute(""" SELECT * FROM prestashop.line_quotation WHERE id_order = """ + str(presta_order['id_order']))
            lines = cr.dictfetchall();
            for line in lines:
                line_vals = {
                    'product_uom_qty': line['qty'],
                    'product_uom': 1,
                    'product_id': line['product_id'],
                    'price_unit': line['product_price_unit'],
                    'name': 'tmp_name'
                }
                # on ajoute les lignes au devis 
                vals['order_line'].append((0,0,line_vals))
            # on créé le devis
            order_id = self.create(cr, uid, vals,context)
            order = self.pool.get('sale.order').browse(cr, uid, order_id, context=context)
            warning = ''
            # on parcourt les lignes pour mettre a jour le nom, les taxes et verifier le prix
            for line in order.order_line:
                order_line_infos = line.product_id_change(pricelist=order.pricelist_id.id,partner_id=order.partner_id.id,product=line.product_id.id ,update_tax=True, fiscal_position=order.fiscal_position.id, context=None)
                order_line_infos['value']['tax_id'] = [[6, False, order_line_infos['value']['tax_id']]]
                price_open = order_line_infos['value']['price_unit']
                price_presta = line.price_unit
                if  not price_open - 0.05 <= price_presta <= price_open + 0.05:
                    warning = warning + '<div>' + line.product_id.name + ' -> Le prix differe de plus de 0.05 centimes. Prix de la liste de prix : ' + str(price_open) + '</div>'
                order_line_infos['value']['price_unit'] = line.price_unit
                line.write(order_line_infos['value'])
            # si il y a des différences de prix de plus ou moins 0,05 centimes, on créé une note
            if not warning == '':
                message_values = {
                    'body' : warning,
                    'res_id' : order.id,
                    'model': 'sale.order',
                    'type' : 'comment'
                }
                mail = self.pool.get('mail.message')
                mail_message.create(mail,cr, uid, message_values, context=context)
            cr.execute('UPDATE prestashop.quotation SET id_sale_order = ' + str(order.id) + ' WHERE id_order = ' + str(presta_order['id_order']))
        return True


