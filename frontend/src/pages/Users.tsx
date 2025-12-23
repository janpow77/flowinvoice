import { useTranslation } from 'react-i18next'
import {
  Users as UsersIcon,
  UserPlus,
  Settings,
  Shield,
  Clock,
  Construction,
} from 'lucide-react'

export default function Users() {
  const { i18n } = useTranslation()
  const lang = i18n.language

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-theme-primary/10 rounded-lg">
            <UsersIcon className="w-8 h-8 text-theme-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-theme-text-primary">
              {lang === 'de' ? 'Benutzerverwaltung' : 'User Management'}
            </h1>
            <p className="text-theme-text-muted">
              {lang === 'de'
                ? 'Verwalten Sie Benutzer, Rollen und Berechtigungen'
                : 'Manage users, roles and permissions'}
            </p>
          </div>
        </div>
      </div>

      {/* Coming Soon Card */}
      <div className="bg-theme-card rounded-xl border border-theme-border p-12 text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-status-warning-bg mb-6">
          <Construction className="w-10 h-10 text-status-warning" />
        </div>

        <h2 className="text-xl font-semibold text-theme-text-primary mb-2">
          {lang === 'de' ? 'Bald verfügbar' : 'Coming Soon'}
        </h2>

        <p className="text-theme-text-muted max-w-md mx-auto mb-8">
          {lang === 'de'
            ? 'Die Benutzerverwaltung wird derzeit entwickelt. Bald können Sie hier Benutzer anlegen, Rollen zuweisen und Berechtigungen verwalten.'
            : 'User management is currently under development. Soon you will be able to create users, assign roles and manage permissions here.'}
        </p>

        {/* Planned Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="p-4 bg-theme-hover rounded-lg">
            <UserPlus className="w-6 h-6 text-blue-500 mx-auto mb-2" />
            <h3 className="font-medium text-theme-text-primary text-sm">
              {lang === 'de' ? 'Benutzer anlegen' : 'Create Users'}
            </h3>
            <p className="text-xs text-theme-text-muted mt-1">
              {lang === 'de' ? 'Neue Benutzer hinzufügen' : 'Add new users'}
            </p>
          </div>

          <div className="p-4 bg-theme-hover rounded-lg">
            <Shield className="w-6 h-6 text-green-500 mx-auto mb-2" />
            <h3 className="font-medium text-theme-text-primary text-sm">
              {lang === 'de' ? 'Rollen & Rechte' : 'Roles & Permissions'}
            </h3>
            <p className="text-xs text-theme-text-muted mt-1">
              {lang === 'de' ? 'Zugriffsrechte verwalten' : 'Manage access rights'}
            </p>
          </div>

          <div className="p-4 bg-theme-hover rounded-lg">
            <Clock className="w-6 h-6 text-purple-500 mx-auto mb-2" />
            <h3 className="font-medium text-theme-text-primary text-sm">
              {lang === 'de' ? 'Aktivitätslog' : 'Activity Log'}
            </h3>
            <p className="text-xs text-theme-text-muted mt-1">
              {lang === 'de' ? 'Benutzeraktivitäten nachverfolgen' : 'Track user activities'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
