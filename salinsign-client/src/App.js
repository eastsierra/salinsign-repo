import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import LibraryModule from './LibraryModule';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Home Page Route */}
          <Route
            path="/"
            element={
              <header className="App-header">
                <p>Welcome to the Home Page!</p>
                <Link to="/library-module">
                  <button className="App-button">Go to Sign Library</button>
                </Link>
              </header>
            }
          />
          
          {/* Sign Library Route */}
          <Route path="/library-module" element={<LibraryModule />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
