import prisma from './database';

async function verifyUserData() {
  try {
    console.log('🔍 Verifying updated user data...\n');

    const user = await prisma.user.findFirst({
      where: { email: 'john.doe@example.com' },
      include: {
        creditCards: true,
        transactions: {
          take: 3,
          orderBy: { transaction_date: 'desc' }
        },
        alertRules: true
      }
    });

    if (!user) {
      console.log('❌ User not found');
      return;
    }

    console.log('👤 USER PROFILE:');
    console.log(`   Name: ${user.first_name} ${user.last_name}`);
    console.log(`   Email: ${user.email}`);
    console.log(`   Phone: ${user.phone_number}`);
    console.log(`   Active: ${user.is_active}\n`);

    console.log('📍 ADDRESS:');
    console.log(`   Street: ${user.address_street}`);
    console.log(`   City: ${user.address_city}, ${user.address_state} ${user.address_zipcode}`);
    console.log(`   Country: ${user.address_country}\n`);

    console.log('💰 FINANCIAL INFO:');
    console.log(`   Credit Limit: $${user.credit_limit?.toString()}`);
    console.log(`   Current Balance: $${user.credit_balance?.toString()}\n`);

    console.log('📱 MOBILE APP LOCATION (Privacy Consented):');
    console.log(`   Consent Given: ${user.location_consent_given}`);
    if (user.location_consent_given) {
      console.log(`   Last Location: ${user.last_app_location_latitude}, ${user.last_app_location_longitude}`);
      console.log(`   Timestamp: ${user.last_app_location_timestamp?.toISOString()}`);
      console.log(`   Accuracy: ${user.last_app_location_accuracy}m\n`);
    }

    console.log('🛒 LAST TRANSACTION LOCATION:');
    console.log(`   Coordinates: ${user.last_merchant_latitude}, ${user.last_merchant_longitude}`);
    console.log(`   Location: ${user.last_merchant_city}, ${user.last_merchant_state}, ${user.last_merchant_country}`);
    console.log(`   Timestamp: ${user.last_transaction_timestamp?.toISOString()}\n`);

    console.log('💳 RELATED DATA:');
    console.log(`   Credit Cards: ${user.creditCards.length}`);
    console.log(`   Recent Transactions: ${user.transactions.length}`);
    console.log(`   Alert Rules: ${user.alertRules.length}`);

    console.log('\n✅ User data verification complete!');

  } catch (error) {
    console.error('❌ Error verifying user data:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

verifyUserData(); 