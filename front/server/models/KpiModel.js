import { pool } from '../db.js';

export const KpiModel = {
  getAll: async () => {
    const [rows] = await pool.query('SELECT * FROM rep_kpis');
    return rows;
  }
};
