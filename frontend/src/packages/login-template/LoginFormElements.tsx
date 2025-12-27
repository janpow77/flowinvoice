/**
 * Login Form Elements
 *
 * Vorgefertigte Form-Elemente für das Login-Template.
 * Diese können direkt verwendet oder als Vorlage dienen.
 */

import { forwardRef, InputHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react';

// =============================================================================
// Login Input
// =============================================================================

interface LoginInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const LoginInput = forwardRef<HTMLInputElement, LoginInputProps>(
  ({ label, className = '', ...props }, ref) => {
    return (
      <div>
        {label && (
          <label
            htmlFor={props.id}
            className="block text-sm font-semibold text-blue-100 mb-2"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`w-full bg-white/10 border border-white/30 text-white placeholder-blue-200/60
            focus:border-blue-300 focus:ring-2 focus:ring-blue-300/50 h-12 rounded-lg px-4
            transition-all duration-200 ${className}`}
          {...props}
        />
      </div>
    );
  }
);

LoginInput.displayName = 'LoginInput';

// =============================================================================
// Login Button
// =============================================================================

interface LoginButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  children: ReactNode;
}

export const LoginButton = forwardRef<HTMLButtonElement, LoginButtonProps>(
  ({ loading = false, children, className = '', disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 h-12
          shadow-lg shadow-blue-900/50 border-none text-base rounded-lg
          transition-all duration-200 hover:shadow-xl hover:shadow-blue-800/50
          disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        {...props}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span>Laden...</span>
          </span>
        ) : (
          children
        )}
      </button>
    );
  }
);

LoginButton.displayName = 'LoginButton';

// =============================================================================
// Login Error Message
// =============================================================================

interface LoginErrorProps {
  message: string;
}

export function LoginError({ message }: LoginErrorProps) {
  if (!message) return null;

  return (
    <div className="text-sm text-center text-red-100 bg-red-500/30 py-3 px-4 rounded-lg border border-red-400/30">
      {message}
    </div>
  );
}

// =============================================================================
// Login Divider
// =============================================================================

interface LoginDividerProps {
  text?: string;
}

export function LoginDivider({ text = 'oder' }: LoginDividerProps) {
  return (
    <div className="relative my-6">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-white/20" />
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="px-4 bg-transparent text-blue-200/60">{text}</span>
      </div>
    </div>
  );
}

// =============================================================================
// OAuth Button (Google, etc.)
// =============================================================================

interface OAuthButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: ReactNode;
  loading?: boolean;
  children: ReactNode;
}

export const OAuthButton = forwardRef<HTMLButtonElement, OAuthButtonProps>(
  ({ icon, loading = false, children, className = '', disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled || loading}
        className={`w-full flex items-center justify-center gap-3 px-4 py-3 h-12
          bg-white/95 hover:bg-white text-gray-700 font-semibold rounded-lg
          shadow-lg transition-all duration-200 hover:shadow-xl
          disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        {...props}
      >
        {loading ? (
          <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
        ) : (
          icon
        )}
        <span>{children}</span>
      </button>
    );
  }
);

OAuthButton.displayName = 'OAuthButton';

// =============================================================================
// Google Icon
// =============================================================================

export function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path
        fill="currentColor"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="currentColor"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="currentColor"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="currentColor"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

// =============================================================================
// Demo Hint
// =============================================================================

interface DemoHintProps {
  text: string;
}

export function DemoHint({ text }: DemoHintProps) {
  return (
    <p className="text-xs text-blue-200/60 text-center">
      {text}
    </p>
  );
}

export default {
  LoginInput,
  LoginButton,
  LoginError,
  LoginDivider,
  OAuthButton,
  GoogleIcon,
  DemoHint,
};
