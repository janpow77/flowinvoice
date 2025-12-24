/**
 * Button Component
 *
 * Einheitlicher Button mit verschiedenen Varianten und Größen.
 */

import { forwardRef, ButtonHTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import { InlineSpinner } from './LogoSpinner';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'success' | 'warning' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button-Variante */
  variant?: ButtonVariant;
  /** Button-Größe */
  size?: ButtonSize;
  /** Volle Breite */
  fullWidth?: boolean;
  /** Lädt gerade */
  loading?: boolean;
  /** Icon links vom Text */
  leftIcon?: ReactNode;
  /** Icon rechts vom Text */
  rightIcon?: ReactNode;
  /** Nur Icon (quadratisch) */
  iconOnly?: boolean;
  /** Kinder-Elemente */
  children?: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  outline: 'btn-outline',
  ghost: 'btn-ghost',
  success: 'btn-success',
  warning: 'btn-warning',
  danger: 'btn-danger',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'btn-sm',
  md: '',
  lg: 'btn-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      leftIcon,
      rightIcon,
      iconOnly = false,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={clsx(
          'btn',
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && 'w-full',
          iconOnly && 'btn-icon',
          className
        )}
        {...props}
      >
        {loading ? (
          <>
            <InlineSpinner size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />
            {!iconOnly && children && <span className="ml-2">{children}</span>}
          </>
        ) : (
          <>
            {leftIcon && <span className="mr-2">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="ml-2">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

/**
 * IconButton - Quadratischer Button nur mit Icon
 */
interface IconButtonProps extends Omit<ButtonProps, 'children' | 'leftIcon' | 'rightIcon' | 'iconOnly'> {
  icon: ReactNode;
  'aria-label': string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, className, ...props }, ref) => {
    return (
      <Button ref={ref} iconOnly className={className} {...props}>
        {icon}
      </Button>
    );
  }
);

IconButton.displayName = 'IconButton';

/**
 * ButtonGroup - Gruppiert mehrere Buttons
 */
interface ButtonGroupProps {
  children: ReactNode;
  className?: string;
}

export function ButtonGroup({ children, className }: ButtonGroupProps) {
  return (
    <div className={clsx('flex items-center gap-2', className)}>
      {children}
    </div>
  );
}

export default Button;
