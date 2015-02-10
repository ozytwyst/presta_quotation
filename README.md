# presta_quotation
Quotation from prestashop to openerp

Tables needed:

CREATE TABLE prestashop.line_quotation
(
  id serial NOT NULL,
  id_order integer,
  product_id integer,
  qty integer,
  product_price_unit numeric,
  CONSTRAINT line_quotation_pkey PRIMARY KEY (id)
);

CREATE TABLE prestashop.quotation
(
  id serial NOT NULL,
  id_sale_order integer,
  id_order integer,
  email character varying,
  invoice_id integer,
  invoice_name character varying,
  invoice_street character varying,
  invoice_street2 character varying,
  invoice_zip character varying,
  invoice_city character varying,
  shipping_id integer,
  shipping_name character varying,
  shipping_street character varying,
  shipping_street2 character varying,
  shipping_zip character varying,
  shipping_city character varying,
  CONSTRAINT quotation_pkey PRIMARY KEY (id)
);
