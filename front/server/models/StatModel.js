import { pool } from '../db.js';

export const StatModel = {
  getAll: async () => {
    const [rows] = await pool.query('SELECT * FROM stats');
    return rows;
  }
};
