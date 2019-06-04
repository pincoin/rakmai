insert into shop_legacycustomer(customer_id, email, last_name, first_name, date_joined, phone)
select
  distinct(c.customer_id),
  c.email,
  c.lastname,
  c.firstname,
  c.date_added,
  cv.cellphone
from opencart_order o
  inner join opencart_customer c
    on o.customer_id = c.customer_id
  left outer join opencart_customer_verified cv
    on c.customer_id = cv.customer_id and cv.result_code = 'B000'
where order_status_id = 3;