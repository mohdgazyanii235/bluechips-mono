import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="text-center space-y-4 max-w-lg">
            <p className="font-serif text-2xl text-gold-400">Something went wrong</p>
            <p className="text-stone-400 text-sm font-mono bg-surface border border-surface-border rounded-lg p-4 text-left break-all">
              {this.state.error.message}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="text-sm text-stone-500 hover:text-gold-400 underline"
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
