import { Link, useLocation } from 'react-router-dom';

export function CleanNav() {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="clean-nav">
      <Link to="/" className="clean-nav-title">
        Jenquist Home
      </Link>
      <div className="clean-nav-links">
        <Link
          to="/reference/getting-started"
          className={`clean-nav-link ${isActive('/reference') ? 'clean-nav-link--active' : ''}`}
        >
          Reference
        </Link>
        <Link to="/chat" className="clean-nav-link clean-nav-link--accent">
          AI Dashboard &rarr;
        </Link>
      </div>
    </nav>
  );
}
