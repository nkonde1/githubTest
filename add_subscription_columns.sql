-- Add subscription-related columns to users table
-- Run this script against your PostgreSQL database

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS billing_due_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_payment_amount FLOAT;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(50);
