import { RegionModel } from '../models/RegionModel.js';

export const getRegions = async (req, res) => {
  try {
    const data = await RegionModel.getAll();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
