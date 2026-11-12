import Image from "next/image";

export default function Home() {
  return (
    <div className="bulwark min-h-screen bg-black text-white">
      <header className="nav">
        <div className="nav-inner">
          <div>
            <h1 className="wide text-2xl font-bold tracking-wider">
              Campus Digital Twin
            </h1>
          </div>
          <nav className="nav-links">
            <a href="#!" className="active">Home</a>
            <a href="#!">3D Viewer</a>
            <a href="#!">Upload</a>
            <a href="#!">About</a>
          </nav>
        </div>
      </header>

      <main className="flex min-h-screen flex-col items-center justify-center p-8">
        <div className="max-w-5xl w-full grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* CTA Buttons */}
          <div>
            <button className="btn btn-neon w-full mb-4">
              Open 3D Viewer
            </button>
            <button className="btn btn-ghost w-full mb-4">
              Cancel
            </button>
          </div>

          {/* Frosted Glass Panel */}
          <div className="glass p-6 rounded-lg">
            <h2 className="wide text-2xl font-bold mb-4">3D Campus Viewer</h2>
            <p className="text-zinc-400">
              Interactive 3D visualization of the KENYATSU campus with indoor navigation.
            </p>
          </div>

          {/* Feature Cards */}
          <div>
            <div className="card">
              <h3 className="wide text-xl font-semibold mb-3">3D BIM Visualisation</h3>
              <p className="text-zinc-400 mb-4">
                Explore the building in 3D with floor-by-floor navigation.
              </p>
              <button className="btn btn-blue">Start Exploration</button>
            </div>

            <div className="card">
              <h3 className="wide text-xl font-semibold mb-3">Indoor Routing</h3>
              <p className="text-zinc-400 mb-4">
                Find the shortest path between any two rooms on campus.
              </p>
              <button className="btn btn-blue">Plot Route</button>
            </div>

            <div className="card">
              <h3 className="wide text-xl font-semibold mb-3">IFC Upload</h3>
              <p className="text-zinc-400 mb-4">
                Upload IFC models to extend the campus digital twin.
              </p>
              <button className="btn btn-blue">Upload IFC</button>
            </div>
          </div>
        </div>

        {/* Statistics Ticker */}
        <div className="ticker mt-8">
          <div className="ticker-item active">
            <span className="n">105</span>
            <span className="l">rooms</span>
          </div>
          <div className="ticker-item">
            <span className="n">3</span>
            <span className="l">floors</span>
          </div>
          <div className="ticker-item">
            <span className="n">19</span>
            <span className="l">labels</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 mt-auto border-t border-zinc-800">
        <div className="footer-grid max-w-7xl grid-cols-1 md:grid-cols-2 gap-8 px-8">
          <div>
            <h4 className="wide text-lg font-bold mb-3">Campus Digital Twin</h4>
            <p className="text-zinc-400 text-sm">
              Indoor navigation, engineered in Kenya
            </p>
          </div>
          <div>
            <h4 className="wide text-lg font-bold mb-3">Links</h4>
            <ul className="space-y-2 text-zinc-400 text-sm">
              <li><a href="#!" className="hover:text-neon">Features</a></li>
              <li><a href="#!" className="hover:text-neon">Documentation</a></li>
              <li><a href="#!" className="hover:text-neon">Support</a></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}