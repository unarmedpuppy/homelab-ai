import { useState } from 'react';

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "Can't access a service?",
    answer: "Make sure you're on home WiFi or connected to the VPN. Try refreshing the page. Try a different browser. If the problem persists, the service might be down — check Uptime Kuma or ask Joshua.",
  },
  {
    question: 'Forgot your password?',
    answer: "All passwords are stored in Vaultwarden. Open it from the home page and search for the service. If you can't get into Vaultwarden itself, ask Joshua to reset it.",
  },
  {
    question: 'Service is slow or not loading?',
    answer: "The server might be under heavy load or restarting after an update. Wait a few minutes and try again. If it's still slow, let Joshua know.",
  },
  {
    question: 'Requested movie or show not appearing?',
    answer: "Overseerr requests are automatic but can take anywhere from a few minutes to a few hours depending on availability. Check the request status in Overseerr.",
  },
  {
    question: 'Photos not syncing?',
    answer: "Check the Immich app on your phone. Make sure background sync is enabled in the app settings. Also verify you're connected to WiFi — the app may be configured to only sync on WiFi.",
  },
  {
    question: 'How to get help',
    answer: "Text Joshua. For non-urgent things, you can also create a card on the Planka project board.",
  },
];

function AccordionItem({ item }: { item: FAQItem }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="clean-accordion-item">
      <button
        className="clean-accordion-trigger"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span>{item.question}</span>
        <span className={`clean-accordion-chevron ${open ? 'clean-accordion-chevron--open' : ''}`}>
          &#9660;
        </span>
      </button>
      {open && (
        <div className="clean-accordion-content">
          {item.answer}
        </div>
      )}
    </div>
  );
}

export default function TroubleshootingPage() {
  return (
    <>
      <div className="clean-page-header">
        <h1 className="clean-page-title">Troubleshooting</h1>
        <p className="clean-page-subtitle">Common issues and how to fix them</p>
      </div>

      {faqs.map((faq) => (
        <AccordionItem key={faq.question} item={faq} />
      ))}
    </>
  );
}
