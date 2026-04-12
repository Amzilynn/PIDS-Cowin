import React from 'react';
import logoPng from '../assets/logo.png';

export default function Logo({ className = "h-10 w-auto", showText = true }) {
  // If showText is false, we might want to crop or hide the text portion.
  // However, given the PNG includes both icon and "Avalive" text, 
  // we'll display the PNG which represents the full brand identity.
  // We can adjust the container width based on showText if needed.
  
  return (
    <div className={`flex items-center gap-3 group cursor-pointer ${className} transition-opacity duration-300 hover:opacity-90`}>
      <img 
        src={logoPng} 
        alt="Avalive MedDelegate Pro" 
        className="h-full w-auto object-contain"
        style={{ maxHeight: '100%' }}
      />
      {!showText && (
         <div className="sr-only">Avalive MedDelegate Pro</div>
      )}
    </div>
  );
}
