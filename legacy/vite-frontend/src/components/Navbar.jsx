import { Link } from "react-router-dom";

function Navbar() {
    return (
        <nav className="nav">
            <h2>CRLK</h2>

            <div className="nav-links">
                <Link to ="/missions">Missions</Link>
                <Link to ="/launches">Launches</Link>
                <Link to ="/spacecraft">SpaceCrafts</Link>
                <Link to ="/">About Us</Link>
            </div>
            
        </nav>
    );
}

export default Navbar; 