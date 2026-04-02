import { KpiModel } from '../models/KpiModel.js';

export const getKpis = async (req, res) => {
  try {
    const data = await KpiModel.getAll();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
