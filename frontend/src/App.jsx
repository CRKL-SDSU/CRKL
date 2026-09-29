import {BrowserRouter, Routes, Route} from 'react-router-dom';

import Navbar from './components/Navbar';
import Home from './pages/Home';
import Missions from './pages/Missions';
import Launches from './pages/Launches';
import Spacecraft from './pages/Spacecraft';

function App() {
    return (
        <BrowserRouter>
            <Navbar />

            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/missions" element={<Missions />} />
                <Route path="/spacecraft" element={<Spacecraft />} />
                <Route path="/launches" element={<Launches />} />
            </Routes>
        </BrowserRouter>
    );
}
export default App
