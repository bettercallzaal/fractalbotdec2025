const { neon } = require('@neondatabase/serverless');

// Use the DATABASE_URL directly
const DATABASE_URL = 'postgresql://neondb_owner:npg_eyICRwz1S0or@ep-raspy-glitter-aeiaae3n-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require';

console.log('🔍 Using DATABASE_URL for migration...');
const sql = neon(DATABASE_URL);

async function migrate() {
  console.log('🔄 Starting database migration...');
  
  try {
    // Create users table
    await sql`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        discord_id VARCHAR(255) UNIQUE NOT NULL,
        username VARCHAR(255) NOT NULL,
        display_name VARCHAR(255),
        avatar_url TEXT,
        wallet_address VARCHAR(255),
        total_fractals INTEGER DEFAULT 0,
        total_wins INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `;
    console.log('✅ Users table created');

    // Create fractals table
    await sql`
      CREATE TABLE IF NOT EXISTS fractals (
        id SERIAL PRIMARY KEY,
        thread_id VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        guild_id VARCHAR(255) NOT NULL,
        facilitator_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        status VARCHAR(50) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
      )
    `;
    console.log('✅ Fractals table created');

    // Create participants table
    await sql`
      CREATE TABLE IF NOT EXISTS participants (
        id SERIAL PRIMARY KEY,
        fractal_id INTEGER REFERENCES fractals(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        level INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(fractal_id, user_id, level)
      )
    `;
    console.log('✅ Participants table created');

    // Create voting_rounds table
    await sql`
      CREATE TABLE IF NOT EXISTS voting_rounds (
        id SERIAL PRIMARY KEY,
        fractal_id INTEGER REFERENCES fractals(id) ON DELETE CASCADE,
        level INTEGER NOT NULL,
        winner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        total_votes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        UNIQUE(fractal_id, level)
      )
    `;
    console.log('✅ Voting rounds table created');

    // Create votes table
    await sql`
      CREATE TABLE IF NOT EXISTS votes (
        id SERIAL PRIMARY KEY,
        voting_round_id INTEGER REFERENCES voting_rounds(id) ON DELETE CASCADE,
        voter_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        candidate_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(voting_round_id, voter_id)
      )
    `;
    console.log('✅ Votes table created');

    console.log('🎉 Database migration completed successfully!');
    
    // Test the connection
    const userCount = await sql`SELECT COUNT(*) as count FROM users`;
    console.log(`📊 Current users in database: ${userCount[0].count}`);
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  }
}

migrate();
