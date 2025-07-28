import prisma from './database';

async function seed() {
  try {
    console.log('🌱 Starting database seed...');

    // Create sample user
    const user = await prisma.user.create({
      data: {
        email: 'john.doe@example.com',
        first_name: 'John',
        last_name: 'Doe',
        phone_number: '+1-555-0123',
        
        // Address information
        address_street: '123 Main Street, Apt 4B',
        address_city: 'San Francisco',
        address_state: 'CA',
        address_zipcode: '94102',
        address_country: 'US',
        
        // Financial information
        credit_limit: 15000.00,
        credit_balance: 2347.85,
        
        // Location consent and last app location
        location_consent_given: true,
        last_app_location_latitude: 37.7749,
        last_app_location_longitude: -122.4194,
        last_app_location_timestamp: new Date('2024-01-17T18:30:00Z'),
        last_app_location_accuracy: 5.0,
        
        // Last transaction location (from most recent transaction)
        last_merchant_latitude: 37.7849,
        last_merchant_longitude: -122.4094,
        last_transaction_timestamp: new Date('2024-01-17T19:20:00Z'),
        last_merchant_city: 'San Francisco',
        last_merchant_state: 'CA',
        last_merchant_country: 'US',
      },
    });

    console.log('👤 Created user:', user.email);

    // Create sample credit card
    const creditCard = await prisma.creditCard.create({
      data: {
        user_id: user.id,
        card_number: '1234', // Last 4 digits only
        card_type: 'Visa',
        bank_name: 'Example Bank',
        card_holder_name: 'John Doe',
        expiry_month: 12,
        expiry_year: 2027,
      },
    });

    console.log('💳 Created credit card for user');


    // Create sample transactions
    const transactions = await Promise.all([
      prisma.transaction.create({
        data: {
          user_id: user.id,
          first_name: user.first_name,
          last_name: user.last_name,
          trans_num: "123456",
          credit_card_num: creditCard.id,
          amount: 89.99,
          description: 'Grocery shopping',
          merchant_name: 'Whole Foods Market',
          merchant_category: 'Grocery',
          transaction_date: new Date('2024-01-15T10:30:00Z'),
          merchant_city: 'San Francisco',
          merchant_state: 'CA',
          merchant_country: 'US',
          status: 'APPROVED',
        },
      }),
      prisma.transaction.create({
        data: {
          user_id: user.id,
          credit_card_num: creditCard.id,
          amount: 1299.99,
          first_name: user.first_name,
          last_name: user.last_name,
          trans_num: "786543",
          description: 'Laptop purchase',
          merchant_name: 'Apple Store',
          merchant_category: 'Electronics',
          transaction_date: new Date('2024-01-16T14:45:00Z'),
          merchant_city: 'San Francisco',
          merchant_state: 'CA',
          merchant_country: 'US',
          status: 'APPROVED',
        },
      }),
      prisma.transaction.create({
        data: {
          user_id: user.id,
          credit_card_num: creditCard.id,
          amount: 45.50,
          first_name: user.first_name,
          last_name: user.last_name,
          trans_num: "897654",
          description: 'Dinner',
          merchant_name: 'Restaurant ABC',
          merchant_category: 'Dining',
          transaction_date: new Date('2024-01-17T19:20:00Z'),
          merchant_city: 'San Francisco',
          merchant_state: 'CA',
          merchant_country: 'US',
          status: 'APPROVED',
        },
      }),
    ]);

    console.log(`💰 Created ${transactions.length} sample transactions`);

    // Create sample alert rules
    const alertRules = await Promise.all([
      prisma.alertRule.create({
        data: {
          user_id: user.id,
          name: 'High Amount Alert',
          description: 'Alert for transactions over $1000',
          alert_type: 'AMOUNT_THRESHOLD',
          amount_threshold: 1000.00,
          notification_methods: ['EMAIL', 'SMS'],
        },
      }),
      prisma.alertRule.create({
        data: {
          user_id: user.id,
          name: 'Electronics Purchase Alert',
          description: 'Alert for all electronics purchases',
          alert_type: 'MERCHANT_CATEGORY',
          merchant_category: 'Electronics',
          notification_methods: ['EMAIL'],
        },
      }),
      prisma.alertRule.create({
        data: {
          user_id: user.id,
          name: 'AI Smart Alert',
          description: 'Smart pattern-based alerts using AI',
          alert_type: 'PATTERN_BASED',
          natural_language_query: 'Alert me when I spend more than usual on dining in a week',
          notification_methods: ['PUSH'],
        },
      }),
    ]);

    console.log(`🚨 Created ${alertRules.length} sample alert rules`);

    console.log('✅ Database seeded successfully!');
  } catch (error) {
    console.error('❌ Error seeding database:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

seed(); 