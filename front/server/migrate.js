import { pool } from './db.js';

async function migrate() {
  try {
    console.log('Starting migration...');
    await pool.query(`
      CREATE TABLE IF NOT EXISTS user_context (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        topic VARCHAR(100) NOT NULL,
        frequency INT DEFAULT 1,
        last_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY user_topic (user_id, topic)
      )
    `);
    console.log('Migration successful: user_context table created.');
    process.exit(0);
  } catch (err) {
    console.error('Migration failed:', err.message);
    process.exit(1);
  }
}

migrate();
