import React, { useEffect, useState } from 'react';
import styles from './Toast.module.css';

interface ToastProps {
  message: string;
  type?: 'error' | 'info' | 'success';
  duration?: number;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'info',
  duration = 5000,
  onClose,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    setIsVisible(true);

    // Auto-dismiss after duration
    const timer = setTimeout(() => {
      handleLeave();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration]);

  const handleLeave = () => {
    setIsLeaving(true);
    setTimeout(() => {
      onClose();
    }, 300); // Match transition duration
  };

  const getIcon = () => {
    switch (type) {
      case 'error':
        return '⚠️';
      case 'success':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  const toastClass = [
    styles.toast,
    styles[type],
    isVisible ? styles.visible : '',
    isLeaving ? styles.leaving : ''
  ].filter(Boolean).join(' ');

  return (
    <div className={toastClass}>
      <div className={styles.toastContent}>
        <span className={styles.toastIcon}>{getIcon()}</span>
        <span className={styles.toastMessage}>{message}</span>
        <button
          className={styles.toastClose}
          onClick={handleLeave}
          aria-label="Close notification"
        >
          ×
        </button>
      </div>
    </div>
  );
};