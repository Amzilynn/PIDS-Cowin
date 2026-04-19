import { StatModel } from '../models/StatModel.js';

export const getStats = async (req, res) => {
  try {
    const data = await StatModel.getAll();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
