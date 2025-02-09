import React, { useState } from 'react';   
import './TranslationModule.css';
import backButtonImage from '../../images/backbutton.png'; // Back Button Image
import headerImage from '../../images/translation.png'; // Header image for Translation Module
import Chat from '../../images/Chatbox.png';

function TranslationModule() {
    const [messages, setMessages] = useState([]);
    const [inputUser1, setInputUser1] = useState("");
    const [inputUser2, setInputUser2] = useState("");

    const sendMessage = (user, message) => {
        if (message.trim() === "") return;
        setMessages([...messages, { user, text: message }]);
        user === "Patient" ? setInputUser1("") : setInputUser2("");
    };

    return (
        <div className="translation-module">
            <img
                src={backButtonImage}
                alt="Back Button"
                className="back-button"
                onClick={() => window.history.back()} 
            />
            <img src={headerImage} alt="Header" className="header-image" />

            <div className="container">
                {/* Column 1 - Video Stream */}
                <div className="box-1">
                    <div className="content-placeholder">
                        <img
                            src="http://localhost:5000/video_feed"
                            alt="Video Stream"
                            style={{ width: '100%' }}
                        />
                    </div>
                    {/* Input for User 1 */}
                    <div className="input-container">
                        <input
                            type="text"
                            placeholder="Patient Type here..."
                            value={inputUser1}
                            onChange={(e) => setInputUser1(e.target.value)}
                        />
                        <button onClick={() => sendMessage("Patient", inputUser1)}>Send</button>
                    </div>
                </div>

                {/* Column 2 - Chat Box */}
                <div className="box-2">
                <img src={Chat} alt="Header" className="chatbox-header" />
                    <div className="chat-box">
                        {messages.map((msg, index) => (
                            <div
                                key={index}
                                className={`message ${msg.user === "Patient" ? "user1" : "user2"}`}
                            >
                                <strong>{msg.user}:</strong> {msg.text}
                            </div>
                        ))}
                    </div>

                    

                    {/* Input for Doctor */}
                    <div className="input-container">
                        <input
                            type="text"
                            placeholder="Doctor Type here..."
                            value={inputUser2}
                            onChange={(e) => setInputUser2(e.target.value)}
                        />
                        <button onClick={() => sendMessage("Doctor", inputUser2)}>Send</button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default TranslationModule;
