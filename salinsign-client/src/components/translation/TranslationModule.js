import React from 'react';
import './TranslationModule.css';
import backButtonImage from '../../images/backbutton.png'; // Back Button Image
import headerImage from '../../images/signlibrary.png'; // Header image for Translation Module

function TranslationModule() {
  return (
    <div className="translation-module">
      <img
        src={backButtonImage}
        alt="Back Button"
        className="back-button"
        onClick={() => window.history.back()} // Navigates back to the previous page
      />
      <img src={headerImage} alt="Header" className="header-image" />
      <div className="content-placeholder">
        <p>Translation module content goes here...</p>
      </div>
    </div>
  );
}

export default TranslationModule;
