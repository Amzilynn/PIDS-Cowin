import { pool } from '../db.js';

export const VisitModel = {
  getAll: async () => {
    const [rows] = await pool.query('SELECT * FROM physician_visits ORDER BY scheduled_time ASC');
    return rows;
  }
};
