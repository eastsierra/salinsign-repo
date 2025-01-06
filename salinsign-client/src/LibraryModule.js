import React, { useState } from 'react';
import './LibraryModule.css';
import backButtonImage from './images/backbutton.png'; // Back Button Image
import headerImage from './images/signlibrary.png'; // Title image


function LibraryModule() {
  const [activeTab, setActiveTab] = useState("alphabet");

  const categories = {
    alphabet: [
      { title: "Letter A", image: require ("./images/alphabet/A.png") },
      { title: "Letter B", image: require ("./images/alphabet/A.png") },
      { title: "Letter C", image: require ("./images/alphabet/A.png") },
      { title: "Letter D", image: require ("./images/alphabet/A.png") },
      { title: "Letter E", image: require ("./images/alphabet/A.png") },
      { title: "Letter F", image: require ("./images/alphabet/A.png") },
      { title: "Letter G", image: require ("./images/alphabet/A.png") },
      { title: "Letter H", image: require ("./images/alphabet/A.png") },
      { title: "Letter I", image: require ("./images/alphabet/A.png") },
      { title: "Letter J", image: require ("./images/alphabet/A.png") },
      { title: "Letter K", image: require ("./images/alphabet/A.png") },
      { title: "Letter L", image: require ("./images/alphabet/A.png") },
      { title: "Letter M", image: require ("./images/alphabet/A.png") },
      { title: "Letter N", image: require ("./images/alphabet/A.png") },
      { title: "Letter O", image: require ("./images/alphabet/A.png") },
      { title: "Letter P", image: require ("./images/alphabet/A.png") },
      { title: "Letter Q", image: require ("./images/alphabet/A.png") },
      { title: "Letter R", image: require ("./images/alphabet/A.png") },
      { title: "Letter S", image: require ("./images/alphabet/A.png") },
      { title: "Letter T", image: require ("./images/alphabet/A.png") },
      { title: "Letter U", image: require ("./images/alphabet/A.png") },
      { title: "Letter V", image: require ("./images/alphabet/A.png") },
      { title: "Letter W", image: require ("./images/alphabet/A.png") },
      { title: "Letter X", image: require ("./images/alphabet/A.png") },
      { title: "Letter Y", image: require ("./images/alphabet/A.png") },
      { title: "Letter Z", image: require ("./images/alphabet/A.png") },
    ],
    numbers: [
      { title: "Number 0", image: require ("./images/numbers/B.png") },
      { title: "Number 1", image: require ("./images/numbers/B.png") },
      { title: "Number 2", image: require ("./images/numbers/B.png") },
      { title: "Number 3", image: require ("./images/numbers/B.png") },
      { title: "Number 4", image: require ("./images/numbers/B.png") },
      { title: "Number 5", image: require ("./images/numbers/B.png") },
      { title: "Number 6", image: require ("./images/numbers/B.png") },
      { title: "Number 7", image: require ("./images/numbers/B.png") },
      { title: "Number 8", image: require ("./images/numbers/B.png") },
      { title: "Number 9", image: require ("./images/numbers/B.png") },
      { title: "Number 10", image: require ("./images/numbers/B.png") },
    ],
    greetings: [
      { title: "Hello", image: require ("./images/greetings/C.png") },
      { title: "Good Morning", image: require ("./images/greetings/C.png") },
      { title: "Good Afternoon", image: require ("./images/greetings/C.png") },
      { title: "Good Evening", image: require ("./images/greetings/C.png") },
      { title: "Goodbye", image: require ("./images/greetings/C.png") },
      { title: "Thank you", image: require ("./images/greetings/C.png") },
    ],
    medical: [
      { title: "Allergy", image: require ("./images/medical/D.png") },
      { title: "Back pain", image: require ("./images/medical/D.png") },
      { title: "Blood pressure", image: require ("./images/medical/D.png") },
      { title: "Breathing difficulty", image: require ("./images/medical/D.png") },
      { title: "Cold", image: require ("./images/medical/D.png") },
      { title: "Conditions", image: require ("./images/medical/D.png") },
      { title: "Cough", image: require ("./images/medical/D.png") },
      { title: "Dibetes", image: require ("./images/medical/D.png") },
      { title: "Diarrhea", image: require ("./images/medical/D.png") },
      { title: "Dizzy", image: require ("./images/medical/D.png") },
      { title: "Fatigue", image: require ("./images/medical/D.png") },
      { title: "Fever", image: require ("./images/medical/D.png") },
      { title: "Food poisoning", image: require ("./images/medical/D.png") },
      { title: "Headache", image: require ("./images/medical/D.png") },
      { title: "Injury", image: require ("./images/medical/D.png") },
      { title: "Pain", image: require ("./images/medical/D.png") },
      { title: "Sick", image: require ("./images/medical/D.png") },
      { title: "Sore throat", image: require ("./images/medical/D.png") },
      { title: "Stomachache", image: require ("./images/medical/D.png") },
      { title: "Stress", image: require ("./images/medical/D.png") },
      { title: "Stroke", image: require ("./images/medical/D.png") },
      { title: "Strong", image: require ("./images/medical/D.png") },
      { title: "Vomit", image: require ("./images/medical/D.png") },
      { title: "Weak", image: require ("./images/medical/D.png") },
      { title: "Wound", image: require ("./images/medical/D.png") },

    ],
  };

  return (
    <div className="library-module">
      <img
        src={backButtonImage}
        alt="Back Button"
        className="back-button"
        onClick={() => window.history.back()} // Navigates back to the previous page
      />
      <img src={headerImage} alt="Header" className="header-image" />

      <div className="tab-bar">
        {Object.keys(categories).map((category) => (
          <div
            key={category}
            className={`tab ${activeTab === category ? "active-tab" : ""}`}
            onClick={() => setActiveTab(category)}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </div>
        ))}
      </div>

      <div className="tab-content">
        {categories[activeTab].map((item, index) => (
          <div key={index} className="grid-item">
            <img src={item.image} alt={item.title} className="grid-image" />
            <p className="grid-title">{item.title}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LibraryModule;
