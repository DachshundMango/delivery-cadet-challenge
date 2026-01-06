UPDATE sales_customers SET "customerID" = "customerID" - 1000000;

INSERT INTO sales_suppliers ("supplierID", "name", "ingredient", "continent", "city", "district", "size", "longitude", "latitude", "approved") SELECT DISTINCT f."supplierID", 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 0, 0, 'N' FROM sales_franchises f WHERE f."supplierID" NOT IN (SELECT "supplierID" FROM sales_suppliers) ON CONFLICT ("supplierID") DO NOTHING;

ALTER TABLE "sales_franchises" ADD CONSTRAINT "fk_sales_franchises_supplierID" FOREIGN KEY ("supplierID") REFERENCES "sales_suppliers"("supplierID");

ALTER TABLE "sales_transactions" ADD CONSTRAINT "fk_sales_transactions_customerID" FOREIGN KEY ("customerID") REFERENCES "sales_customers"("customerID");

ALTER TABLE "sales_transactions" ADD CONSTRAINT "fk_sales_transactions_franchiseID" FOREIGN KEY ("franchiseID") REFERENCES "sales_franchises"("franchiseID");

ALTER TABLE "media_customer_reviews" ADD CONSTRAINT "fk_media_customer_reviews_franchiseID" FOREIGN KEY ("franchiseID") REFERENCES "sales_franchises"("franchiseID");

ALTER TABLE "media_gold_reviews_chunked" ADD CONSTRAINT "fk_media_gold_reviews_chunked_franchiseID" FOREIGN KEY ("franchiseID") REFERENCES "sales_franchises"("franchiseID");

SQL> done
