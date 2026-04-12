import express from 'express';
import { getRegions } from '../controllers/RegionController.js';
import { getStats } from '../controllers/StatController.js';
import { getStreamLogs } from '../controllers/StreamLogController.js';
import { getSimulationHistory, sendSimulationMessage, getLearnedContext, addLearnedTopic, handleAIVision, handleAISTT, handleAIMultimodal } from '../controllers/SimulationController.js';
import { getVisits } from '../controllers/VisitController.js';
import { getKpis } from '../controllers/KpiController.js';
import { getProducts } from '../controllers/ProductController.js';
import { login } from '../controllers/UserController.js';
import { getUserReports, saveReport } from '../controllers/EvaluationController.js';

const router = express.Router();

router.get('/regions', getRegions);
router.get('/stats', getStats);
router.get('/stream', getStreamLogs);

router.get('/visits', getVisits);
router.get('/kpis', getKpis);

router.get('/simulate/history', getSimulationHistory);
router.post('/simulate/message', sendSimulationMessage);
router.get('/simulate/context', getLearnedContext);
router.post('/simulate/context', addLearnedTopic);
router.post('/ai/vision', handleAIVision);
router.post('/ai/stt', handleAISTT);
router.post('/ai/multimodal', handleAIMultimodal);

router.get('/products', getProducts);

// Authentication
router.post('/auth/login', login);

// Evaluations
router.get('/evaluations/:userId', getUserReports);
router.post('/evaluations', saveReport);

export default router;
