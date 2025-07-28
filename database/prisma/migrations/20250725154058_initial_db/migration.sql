-- CreateEnum
CREATE TYPE "TransactionType" AS ENUM ('PURCHASE', 'REFUND', 'CASHBACK', 'FEE', 'INTEREST', 'PAYMENT');

-- CreateEnum
CREATE TYPE "TransactionStatus" AS ENUM ('PENDING', 'APPROVED', 'DECLINED', 'CANCELLED', 'SETTLED');

-- CreateEnum
CREATE TYPE "AlertType" AS ENUM ('AMOUNT_THRESHOLD', 'MERCHANT_CATEGORY', 'MERCHANT_NAME', 'LOCATION_BASED', 'FREQUENCY_BASED', 'PATTERN_BASED', 'CUSTOM_QUERY');

-- CreateEnum
CREATE TYPE "NotificationMethod" AS ENUM ('EMAIL', 'SMS', 'PUSH', 'WEBHOOK');

-- CreateEnum
CREATE TYPE "NotificationStatus" AS ENUM ('PENDING', 'SENT', 'DELIVERED', 'FAILED', 'READ');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "phone_number" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "address_street" TEXT,
    "address_city" TEXT,
    "address_state" TEXT,
    "address_zipcode" TEXT,
    "address_country" TEXT DEFAULT 'US',
    "credit_limit" DECIMAL(12,2),
    "credit_balance" DECIMAL(12,2) DEFAULT 0.00,
    "location_consent_given" BOOLEAN NOT NULL DEFAULT false,
    "last_app_location_latitude" DOUBLE PRECISION,
    "last_app_location_longitude" DOUBLE PRECISION,
    "last_app_location_timestamp" TIMESTAMP(3),
    "last_app_location_accuracy" DOUBLE PRECISION,
    "last_merchant_latitude" DOUBLE PRECISION,
    "last_merchant_longitude" DOUBLE PRECISION,
    "last_transaction_timestamp" TIMESTAMP(3),
    "last_merchant_city" TEXT,
    "last_merchant_state" TEXT,
    "last_merchant_country" TEXT,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "credit_cards" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "card_number" TEXT NOT NULL,
    "card_type" TEXT NOT NULL,
    "bank_name" TEXT NOT NULL,
    "card_holder_name" TEXT NOT NULL,
    "expiry_month" INTEGER NOT NULL,
    "expiry_year" INTEGER NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "credit_cards_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "transactions" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "trans_num" TEXT NOT NULL,
    "credit_card_num" TEXT NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "description" TEXT NOT NULL,
    "merchant_name" TEXT NOT NULL,
    "merchant_category" TEXT NOT NULL,
    "transaction_date" TIMESTAMP(3) NOT NULL,
    "transaction_type" "TransactionType" NOT NULL DEFAULT 'PURCHASE',
    "merchant_latitude" DOUBLE PRECISION,
    "merchant_longitude" DOUBLE PRECISION,
    "merchant_city" TEXT,
    "merchant_state" TEXT,
    "merchant_country" TEXT,
    "merchant_zipcode" TEXT,
    "status" "TransactionStatus" NOT NULL DEFAULT 'APPROVED',
    "authorization_code" TEXT,
    "reference_number" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "transactions_pkey" PRIMARY KEY ("id")
);



-- CreateTable
CREATE TABLE "alert_rules" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "alert_type" "AlertType" NOT NULL,
    "amount_threshold" DECIMAL(10,2),
    "merchant_category" TEXT,
    "merchant_name" TEXT,
    "location" TEXT,
    "timeframe" TEXT,
    "natural_language_query" TEXT,
    "notification_methods" "NotificationMethod"[] DEFAULT ARRAY['EMAIL']::"NotificationMethod"[],
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "last_triggered" TIMESTAMP(3),
    "trigger_count" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "alert_rules_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "alert_notifications" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "alert_rule_id" TEXT NOT NULL,
    "transaction_id" TEXT,
    "title" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "notification_method" "NotificationMethod" NOT NULL,
    "status" "NotificationStatus" NOT NULL DEFAULT 'PENDING',
    "sent_at" TIMESTAMP(3),
    "delivered_at" TIMESTAMP(3),
    "read_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "alert_notifications_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_address_city_address_state_idx" ON "users"("address_city", "address_state");

-- CreateIndex
CREATE INDEX "users_location_consent_given_idx" ON "users"("location_consent_given");

-- CreateIndex
CREATE INDEX "transactions_user_id_transaction_date_idx" ON "transactions"("user_id", "transaction_date");

-- CreateIndex
CREATE INDEX "transactions_merchant_category_idx" ON "transactions"("merchant_category");

-- CreateIndex
CREATE INDEX "transactions_amount_idx" ON "transactions"("amount");

-- CreateIndex
CREATE INDEX "alert_rules_user_id_is_active_idx" ON "alert_rules"("user_id", "is_active");

-- CreateIndex
CREATE INDEX "alert_notifications_user_id_created_at_idx" ON "alert_notifications"("user_id", "created_at");

-- AddForeignKey
ALTER TABLE "credit_cards" ADD CONSTRAINT "credit_cards_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
--ALTER TABLE "transactions" ADD CONSTRAINT "transactions_credit_card_num_fkey" FOREIGN KEY ("credit_card_num") REFERENCES "credit_cards"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "alert_rules" ADD CONSTRAINT "alert_rules_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "alert_notifications" ADD CONSTRAINT "alert_notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "alert_notifications" ADD CONSTRAINT "alert_notifications_alert_rule_id_fkey" FOREIGN KEY ("alert_rule_id") REFERENCES "alert_rules"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "alert_notifications" ADD CONSTRAINT "alert_notifications_transaction_id_fkey" FOREIGN KEY ("transaction_id") REFERENCES "transactions"("id") ON DELETE SET NULL ON UPDATE CASCADE;
