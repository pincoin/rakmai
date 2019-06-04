/* last 30 days */
select
  date_trunc('day', modified) AS "Day",
  sum(total_selling_price)
from shop_order
where status = '4' and modified > now() - interval '1 month'
group by 1
order by 1;


/* last 12 months */
select
  date_trunc('month', modified) AS "Month",
  sum(total_selling_price)
from shop_order
where status = '4' and modified > now() - interval '1 year'
group by 1
order by 1;
