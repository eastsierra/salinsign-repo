import React from 'react';
import './TranslationModule.css';
import backButtonImage from '../../images/backbutton.png'; // Back Button Image
import headerImage from '../../images/translation.png'; // Header image for Translation Module
 // Import the VideoStream component

function TranslationModule() {
  return (
    <div className="translation-module">
      <img
        src={backButtonImage}
        alt="Back Button"
        className="back-button"
        onClick={() => window.history.back()} 
      />
      <img src={headerImage} alt="Header" className="header-image" />
      <div className="content-placeholder">

            <img
                src="http://localhost:5000/video_feed"
                alt="Video Stream"
                style={{ width: '100%' }}
            />
      </div>
    </div>

    
  );
}

export default TranslationModule;
