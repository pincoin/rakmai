insert into shop_legacyorderproduct(customer_id_id, product_name)
select
  o.customer_id,
  op.model
from opencart_order o
  inner join opencart_order_product op
    on o.order_id = op.order_id
  inner join shop_legacycustomer c
    on o.customer_id = c.customer_id
where order_status_id = 3
group by o.customer_id, op.model;