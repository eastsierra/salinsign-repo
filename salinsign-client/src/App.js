import { BrowserRouter as Router, Routes, Route, useNavigate, Link } from 'react-router-dom';
import './App.css';
import LibraryModule from './LibraryModule';

const Translate = () => <h2>Translate Module</h2>;
const SignLibrary = () => <h2>Sign Library Module</h2>;
const Help = () => <h2>Help Module</h2>;

function MainMenu() {
  const navigate = useNavigate();

  return (
    <div className="App">
      <header className="App-header">
        <div className="Background-image">
          <img src="Salin.png" alt="Logo" className="App-logo" />
          <div className="Button-container">
            <button onClick={() => navigate('/translate')} className="Menu-button">
              <img src="TRANSLATE.png" alt="Translate Icon" className="Button-icon" />
            </button>

            <button onClick={() => navigate('/library-module')} className="Menu-button">
              <img src="LIBRARY.png" alt="Library Icon" className="Button-icon" />
            </button>

            <button onClick={() => navigate('/help')} className="Menu-button">
              <img src="HELP.png" alt="Help Icon" className="Button-icon" />
            </button>
          </div>
        </div>
      </header>
    </div>
  );
}

function AppWrapper() {
  return (
    <Router>
      <Routes>
        {/* Home Page */}
        <Route path="/" element={<MainMenu />} />
        
        {/* Routes for other modules */}
        <Route path="/translate" element={<Translate />} />
        <Route path="/sign-library" element={<SignLibrary />} />
        <Route path="/help" element={<Help />} />
        <Route path="/library-module" element={<LibraryModule />} />
      </Routes>
    </Router>
  );
}

export default AppWrapper;