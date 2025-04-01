import { useState, useEffect, useCallback } from "react";
import './progress_popup.css';

export const ProgressPopup = ({ noteName, progress, onClose }) => (
    <div className="popup-overlay">
      <div className="popup-content">
        {/* <img 
          src={`/hands/${noteName}.png`} 
          alt={noteName}
          className="hand-image"
        /> */}
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );