/**
 * FlowAudit Login Template Package
 *
 * Wiederverwendbares Login-Template mit Animationen.
 * Das Logo ist im Package enthalten (assets/auditlogo.png).
 *
 * Verwendung:
 * ```tsx
 * import { LoginTemplate, LoginInput, LoginButton, logoPath } from '@/packages/login-template';
 *
 * <LoginTemplate
 *   logoPath={logoPath}  // Logo aus dem Package
 *   title="flowaudit"
 *   subtitle="Automated Audit Systems"
 * >
 *   <form onSubmit={handleSubmit}>
 *     <LoginInput label="Benutzername" />
 *     <LoginInput label="Passwort" type="password" />
 *     <LoginButton>Login</LoginButton>
 *   </form>
 * </LoginTemplate>
 * ```
 */

// Logo Assets - im Package enthalten
import logoPng from './assets/auditlogo.png';
import logoSvg from './assets/auditlogo.svg';

export const logoPath = logoPng;
export const logoPathSvg = logoSvg;
export { logoPng, logoSvg };

// Main Template
export {
  LoginTemplate,
  loginAnimations,
  JumpingFish,
  BinaryDataWater,
  DecorativeBubbles,
} from './LoginTemplate';

export type { LoginTemplateProps } from './LoginTemplate';

// Form Elements
export {
  LoginInput,
  LoginButton,
  LoginError,
  LoginDivider,
  OAuthButton,
  GoogleIcon,
  DemoHint,
} from './LoginFormElements';
