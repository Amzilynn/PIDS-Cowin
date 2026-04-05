import React from 'react';

export default function Logo({ className = "w-10 h-10", showText = true }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Icon portion: Silhouette with Heartbeat Pulse */}
      <div className="relative flex items-center justify-center">
        <svg
          viewBox="0 0 200 200"
          className="w-full h-full"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Head Silhouette - Simplified representation of the logo profile */}
          <path
            d="M60 140 C 60 180 140 180 140 140 C 140 100 120 40 100 40 C 80 40 60 100 60 140"
            fill="currentColor"
            className="text-brand-navy"
          />
          <path
            d="M100 45 C 115 45 130 60 135 80 C 140 100 145 110 155 120 L 155 130 C 150 145 135 155 120 160 C 100 165 80 165 60 155 C 50 145 45 130 45 120 C 45 100 50 80 65 60 C 75 50 85 45 100 45 Z"
            fill="currentColor"
            className="text-brand-navy"
          />
          
          {/* Pulse/Heartbeat - Scaled to fit roughly center/top of head area */}
          <path
            d="M70 100 L 90 100 L 95 85 L 105 115 L 110 100 L 130 100"
            stroke="currentColor"
            strokeWidth="4"
            strokeLinejoin="round"
            strokeLinecap="round"
            className="text-brand-teal"
          />
        </svg>
      </div>

      {/* Text portion if enabled */}
      {showText && (
        <div className="flex flex-col -gap-1">
          <h1 className="text-2xl font-extrabold tracking-tight text-brand-navy leading-none">
            Ava<span className="text-brand-teal">live</span>
          </h1>
          <span className="text-[10px] font-bold text-brand-teal tracking-[0.2em] uppercase">
            MedDelegate Pro
          </span>
        </div>
      )}
    </div>
  );
}
