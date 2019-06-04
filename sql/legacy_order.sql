insert into shop_legacyorder(customer_id_id, last_purchased, total_order_count, last_total, max_price, average_price)
select
  o.customer_id as customer_id,
  max(date_modified) as last_purchased,
  count(order_id) as total_order_count,
  sum(case when date_modified > current_date - interval '30' day then total else 0 end) as last_total,
  max(total) as max_price,
  avg(total) as average_price
from opencart_order as o
  inner join opencart_customer as c
    on o.customer_id = c.customer_id
where order_status_id = 3
group by o.customer_id;