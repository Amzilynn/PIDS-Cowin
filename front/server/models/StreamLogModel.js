import { pool } from '../db.js';

export const StreamLogModel = {
  getAll: async () => {
    const [rows] = await pool.query('SELECT * FROM stream_logs ORDER BY created_at ASC');
    return rows;
  }
};
