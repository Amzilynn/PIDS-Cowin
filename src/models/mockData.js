import { LayoutGrid, Map as MapIcon, Brain, Microscope, BarChart3 } from 'lucide-react';

export const menuItems = [
  { id: 'Dashboard', icon: LayoutGrid },
  { id: 'Territory', icon: MapIcon },
  { id: 'Training', icon: Brain },
  { id: 'Medical AI', icon: Microscope },
  { id: 'Analytics', icon: BarChart3 },
];

export const initialRegionData = { 
  name: 'Tunis', 
  perf: 92, 
  reps: 42, 
  strategy: 'Optimize cardio-unit distribution.' 
};

export const initialSimData = { 
  eye: 0, 
  know: 0, 
  feedback: 'Ready to simulate...' 
};
