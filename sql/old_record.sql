/* 1. shop_voucher 테이블 백업 */
/* Copy old table structure */
/*
CREATE TABLE shop_voucher_2019_2nd (LIKE shop_voucher INCLUDING ALL);
 */

/* Move records into new table */
/*
INSERT INTO shop_voucher_2019_2nd
SELECT * FROM shop_voucher WHERE created < '2020-01-01';
 */

/* Delete old records */
/*
DELETE FROM shop_voucher WHERE created < '2020-01-01';
 */

/* 2. shop_orderproductvoucher 테이블 백업 */

/* 3. shop_orderproduct 테이블 백업 */

/* 4. shop_orderpayment 테이블 백업 */

/* 5. shop_order 테이블 백업 */
