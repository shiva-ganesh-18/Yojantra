import React, { Component } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[Yojantra ErrorBoundary] Uncaught rendering exception:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200 p-8 text-center space-y-6">
            <div className="w-16 h-16 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
              <AlertTriangle size={32} />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-gov-navy-950">Something went wrong</h2>
              <p className="text-sm text-slate-500">
                An unexpected interface error occurred. The application state has been safely preserved.
              </p>
            </div>
            {this.state.error && (
              <div className="p-3 bg-slate-100 rounded-xl text-left text-xs font-mono text-slate-700 overflow-auto max-h-32 border border-slate-200">
                {this.state.error.toString()}
              </div>
            )}
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="px-5 py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white font-semibold text-sm shadow flex items-center gap-2"
              >
                <RefreshCw size={16} />
                <span>Reload Page</span>
              </button>
              <button
                type="button"
                onClick={this.handleReset}
                className="px-5 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-sm flex items-center gap-2"
              >
                <Home size={16} />
                <span>Go Home</span>
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
