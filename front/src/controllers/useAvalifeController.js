import { useState, useCallback, useEffect, useRef } from 'react';
import { initialRegionData, initialSimData } from '../models/mockData';

export function useAvalifeController() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [selectedRegion, setSelectedRegion] = useState(initialRegionData);
  const [simData, setSimData] = useState(initialSimData);
  const [medQuery, setMedQuery] = useState('');
  const [roleType, setRoleType] = useState('Medical');
  
  // Dynamic API Data states
  const [stats, setStats] = useState([]);
  const [regionsData, setRegionsData] = useState([]);
  const [streamLogs, setStreamLogs] = useState([]);
  const [visits, setVisits] = useState([]);
  const [kpis, setKpis] = useState([]);
  const [products, setProducts] = useState([]);

  // Simulation Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const SERVER_URL = 'http://localhost:5000';

  const safeFetch = (url, setter) => {
    fetch(url)
      .then(res => res.json())
      .then(data => setter(Array.isArray(data) ? data : []))
      .catch(err => console.error(`Error fetching ${url}:`, err));
  };

  useEffect(() => {
    safeFetch(`${SERVER_URL}/api/stats`, setStats);
    safeFetch(`${SERVER_URL}/api/regions`, setRegionsData);
    safeFetch(`${SERVER_URL}/api/stream`, setStreamLogs);
    safeFetch(`${SERVER_URL}/api/visits`, setVisits);
    safeFetch(`${SERVER_URL}/api/kpis`, setKpis);
    safeFetch(`${SERVER_URL}/api/products`, setProducts);
    safeFetch(`${SERVER_URL}/api/simulate/history`, setChatMessages);
  }, []);

  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
  }, []);

  const handleRegionSelect = useCallback((region) => {
    setSelectedRegion(region);
  }, []);

  const handleSendChat = useCallback(async (message) => {
    if (!message.trim()) return;
    // Optimistically add delegate message to chat
    const delegateMsg = { role: 'delegate', message };
    setChatMessages(prev => [...prev, delegateMsg]);
    setChatInput('');
    setChatLoading(true);
    try {
      const res = await fetch(`${SERVER_URL}/api/simulate/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: 'doctor', message: data.aiMessage }]);
      setSimData({ eye: data.eye, know: data.know, feedback: data.feedback });
    } catch (err) {
      console.error("Chat error:", err);
      setChatMessages(prev => [...prev, { role: 'doctor', message: 'Ava Train: Connection error. Please check the server.' }]);
    } finally {
      setChatLoading(false);
    }
  }, []);

  const handleSimulationRun = handleSendChat;

  const handleMedQueryChange = useCallback((query) => {
    setMedQuery(query);
  }, []);

  return {
    state: {
      activeTab,
      selectedRegion,
      simData,
      medQuery,
      stats,
      regionsData,
      streamLogs,
      visits,
      kpis,
      products,
      chatMessages,
      chatInput,
      chatLoading,
      roleType
    },
    actions: {
      handleTabChange,
      handleRegionSelect,
      handleSimulationRun,
      handleSendChat,
      handleMedQueryChange,
      setChatInput,
      setRoleType
    }
  };
}
