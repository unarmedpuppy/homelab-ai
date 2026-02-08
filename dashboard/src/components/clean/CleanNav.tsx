import { Link, useLocation } from 'react-router-dom';

const referenceLinks = [
  { to: '/reference/getting-started', label: 'Getting Started' },
  { to: '/reference/emails', label: 'Emails' },
  { to: '/reference/troubleshooting', label: 'Troubleshooting' },
];

export function CleanNav() {
  const location = useLocation();
  const isReference = location.pathname.startsWith('/reference');

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      <nav className="clean-nav">
        <Link to="/" className="clean-nav-title">
          Jenquist Home
        </Link>
        <div className="clean-nav-links">
          <Link
            to="/reference/getting-started"
            className={`clean-nav-link ${isReference ? 'clean-nav-link--active' : ''}`}
          >
            Reference
          </Link>
          <Link to="/chat" className="clean-nav-link clean-nav-link--accent">
            AI Dashboard &rarr;
          </Link>
        </div>
      </nav>
      {isReference && (
        <div className="clean-subnav">
          {referenceLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`clean-subnav-link ${isActive(link.to) ? 'clean-subnav-link--active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
