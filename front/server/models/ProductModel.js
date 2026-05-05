import { pool } from '../db.js';

export const ProductModel = {
  getAll: async () => {
    const [rows] = await pool.query('SELECT * FROM medical_products');
    return rows;
  }
};
