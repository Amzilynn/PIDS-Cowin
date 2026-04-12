import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("=== App Crash ===", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          display: 'flex', flexDirection: 'column', alignItems: 'center', 
          justifyContent: 'center', height: '100vh', fontFamily: 'monospace',
          background: '#0F172A', color: '#f1f5f9', padding: '40px'
        }}>
          <h1 style={{ color: '#f87171', fontSize: '24px', marginBottom: '12px' }}>
            ⚠ Application Error
          </h1>
          <pre style={{ 
            color: '#94a3b8', background: '#1e293b', padding: '24px',
            borderRadius: '12px', maxWidth: '800px', overflowX: 'auto', fontSize: '13px'
          }}>
            {this.state.error && this.state.error.toString()}
          </pre>
          <p style={{ color: '#64748b', marginTop: '16px', fontSize: '14px' }}>
            Check the browser console (F12) for more details.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
