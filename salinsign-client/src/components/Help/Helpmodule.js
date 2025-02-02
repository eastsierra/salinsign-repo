import React from "react";
import { useNavigate } from "react-router-dom";
import backButtonImage from "../../images/backbutton.png"; // Back Button Image
import "./Helpmodule.css"; // Import CSS for styling

function HelpModule() {
  const navigate = useNavigate();

  return (
    <div className="help-module">
      {/* Back Button */}
      <img
        src={backButtonImage}
        alt="Back"
        className="back-button"
        onClick={() => navigate(-1)}
      />

      {/* Help Title */}
      <h2 className="help-title">HELP</h2>

      {/* Help Content */}
      <div className="help-content">
        {/* Video Section */}
        <div className="video-container">
          <video controls className="video-player">
            <source src="your-video-file.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Help Text Section */}
        <div className="text-box">
          <p>
            <strong>Lorem ipsum dolor sit amet,</strong> consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
            dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
            proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
          </p>
        </div>
      </div>
    </div>
  );
}

export default HelpModule;
