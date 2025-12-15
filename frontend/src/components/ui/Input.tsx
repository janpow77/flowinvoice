/**
 * Input Components
 *
 * Formular-Eingabefelder mit einheitlichem Styling.
 */

import { forwardRef, InputHTMLAttributes, TextareaHTMLAttributes, SelectHTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';

/* =============================================================================
   Input (Text, Email, Password, Number, etc.)
   ============================================================================= */

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Label über dem Input */
  label?: string;
  /** Hilfetext unter dem Input */
  helperText?: string;
  /** Fehlermeldung */
  error?: string;
  /** Icon links im Input */
  leftIcon?: ReactNode;
  /** Icon rechts im Input */
  rightIcon?: ReactNode;
  /** Volle Breite */
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      fullWidth = true,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = !!error;

    return (
      <div className={clsx('form-group', fullWidth && 'w-full')}>
        {label && (
          <label htmlFor={inputId} className="label">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'input',
              hasError && 'border-error-500 focus:border-error-500 focus:ring-error-500/20',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            aria-invalid={hasError}
            aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
            {...props}
          />
          {rightIcon && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {rightIcon}
            </span>
          )}
        </div>
        {error && (
          <p id={`${inputId}-error`} className="error-text">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="helper-text">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

/* =============================================================================
   Textarea
   ============================================================================= */

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      helperText,
      error,
      fullWidth = true,
      className,
      id,
      rows = 4,
      ...props
    },
    ref
  ) => {
    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = !!error;

    return (
      <div className={clsx('form-group', fullWidth && 'w-full')}>
        {label && (
          <label htmlFor={textareaId} className="label">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          rows={rows}
          className={clsx(
            'textarea',
            hasError && 'border-error-500 focus:border-error-500 focus:ring-error-500/20',
            className
          )}
          aria-invalid={hasError}
          aria-describedby={error ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : undefined}
          {...props}
        />
        {error && (
          <p id={`${textareaId}-error`} className="error-text">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${textareaId}-helper`} className="helper-text">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

/* =============================================================================
   Select
   ============================================================================= */

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  label?: string;
  helperText?: string;
  error?: string;
  options: SelectOption[];
  placeholder?: string;
  fullWidth?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      helperText,
      error,
      options,
      placeholder,
      fullWidth = true,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = !!error;

    return (
      <div className={clsx('form-group', fullWidth && 'w-full')}>
        {label && (
          <label htmlFor={selectId} className="label">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={clsx(
            'select',
            hasError && 'border-error-500 focus:border-error-500 focus:ring-error-500/20',
            className
          )}
          aria-invalid={hasError}
          aria-describedby={error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p id={`${selectId}-error`} className="error-text">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${selectId}-helper`} className="helper-text">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

/* =============================================================================
   Checkbox
   ============================================================================= */

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  helperText?: string;
  error?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, helperText, error, className, id, ...props }, ref) => {
    const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

    return (
      <div className="form-group">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            ref={ref}
            type="checkbox"
            id={checkboxId}
            className={clsx('checkbox mt-0.5', className)}
            {...props}
          />
          <div>
            <span className="text-sm font-medium text-gray-700">{label}</span>
            {helperText && <p className="helper-text mt-0.5">{helperText}</p>}
            {error && <p className="error-text mt-0.5">{error}</p>}
          </div>
        </label>
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';

/* =============================================================================
   Radio
   ============================================================================= */

interface RadioOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface RadioGroupProps {
  name: string;
  label?: string;
  options: RadioOption[];
  value?: string;
  onChange?: (value: string) => void;
  helperText?: string;
  error?: string;
  orientation?: 'horizontal' | 'vertical';
}

export function RadioGroup({
  name,
  label,
  options,
  value,
  onChange,
  helperText,
  error,
  orientation = 'vertical',
}: RadioGroupProps) {
  return (
    <div className="form-group" role="radiogroup" aria-label={label}>
      {label && <span className="label">{label}</span>}
      <div
        className={clsx(
          'flex gap-4',
          orientation === 'vertical' ? 'flex-col' : 'flex-row flex-wrap'
        )}
      >
        {options.map((option) => (
          <label
            key={option.value}
            className={clsx(
              'flex items-center gap-2 cursor-pointer',
              option.disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange?.(e.target.value)}
              disabled={option.disabled}
              className="radio"
            />
            <span className="text-sm text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>
      {error && <p className="error-text">{error}</p>}
      {helperText && !error && <p className="helper-text">{helperText}</p>}
    </div>
  );
}

/* =============================================================================
   FormGroup - Container für Formularfelder
   ============================================================================= */

interface FormGroupProps {
  children: ReactNode;
  className?: string;
}

export function FormGroup({ children, className }: FormGroupProps) {
  return <div className={clsx('space-y-4', className)}>{children}</div>;
}

export default Input;
