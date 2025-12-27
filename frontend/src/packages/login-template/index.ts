/**
 * FlowAudit Login Template Package
 *
 * Wiederverwendbares Login-Template mit Animationen.
 *
 * WICHTIG: Das Logo (auditlogo.png) muss im public-Verzeichnis liegen!
 * Das Template verwendet das Original-Logo ohne Änderungen.
 *
 * Verwendung:
 * ```tsx
 * import { LoginTemplate, LoginInput, LoginButton } from '@/packages/login-template';
 *
 * <LoginTemplate
 *   logoPath="/auditlogo.png"  // Pfad zum Original-Logo
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
