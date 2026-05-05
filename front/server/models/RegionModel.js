import { pool } from '../db.js';

export const RegionModel = {
  getAll: async () => {
    const [rows] = await pool.query('SELECT * FROM regions');
    return rows;
  }
};
