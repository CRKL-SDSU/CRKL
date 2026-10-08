import { Link } from "react-router-dom";

function Home() {
    return (
       <div className="home-container">

            <section className="hero">
            <h1>CRLK Space</h1>

            <p>
                Your mission control for all things space. Learn more about our mission below.
            </p>
    
            </section> 

            <h2>Our Mission</h2>
            <section className="mission-statment">
                
                <p>
                    CRKL Space bring the complexities of space down into your hands. [Place holder]
                </p>
            </section>

            <h2>Meet the team</h2>
            <section className="about-us">
                
                <div className="about-us-card">
                    <h2>Chris</h2>
                    <p>[Role]</p>
                    <p>
                        Chris' blog paragraph here
                    </p>
                </div>

                <div className="about-us-card">
                    <h2>Ryan</h2>
                     <p>[Role]</p>
                    <p>
                        Ryan's blog paragraph here
                    </p>
                </div>

                <div className="about-us-card">
                    <h2>Kaz</h2>
                     <p>[Role]</p>
                    <p>
                        Kaz's blog paragraph here
                    </p>
                </div>

                <div className="about-us-card">
                    <h2>Lia</h2>
                     <p>[Role]</p>
                    <p>
                        Lia's blog paragraph here
                    </p>
                </div>

            </section>

            <h3>Project Links</h3>
            <section className="links">
                
                <div className="links-card">
                    <h4>Phase 1 Draft Presentation</h4>
                    <a
                        href="https://docs.google.com/presentation/d/1e8twPY4Sz94O2nLHfVMKYxdCF_QQqdBgUattRhs2cik/edit?usp=sharing"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Link to our 10 min presentation slides
                    </a>
                </div>

                <div className="links-card">
                    <h4>Draft Database Product Overview & Instructions</h4>
                    <a
                        href=""
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Overview of our product and user instructions.
                    </a>
                </div>

                <div className="links-card">
                    <h4>Draft Blog</h4>
                    <a
                        href=""
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Each team member describes the project and why it is unique.
                    </a>
                </div>

                <div className="links-card">
                    <h4>Draft Source Code & Executable</h4>
                    <a
                        href=""
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        GitHub repository, executable, and summary of original code beyond AI assistance
                    </a>
                </div>

                <div className="links-card">
                    <h4>Draft Database Product Document</h4>
                    <a
                        href=""
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Technical PDF describing design, implementation, course concepts applied, screenshots, and user guide.
                    </a>
                </div>

                <div className="links-card">
                    <h4>Draft about webpage</h4>
                    <a
                        href=""
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Introduce your team and your hypothetical software company.

                    </a>
                </div>

            </section>

       </div>
    );
}

export default Home;