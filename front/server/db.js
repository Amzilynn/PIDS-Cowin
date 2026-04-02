import mysql from 'mysql2/promise';

// Create a connection pool to the MySQL database
export const pool = mysql.createPool({
  host: 'localhost',
  user: 'root',
  password: '', // Assuming no password for local dev
  database: 'avalife_db',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

console.log('MySQL Database pool established.');
