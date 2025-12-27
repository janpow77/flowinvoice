import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users as UsersIcon,
  UserPlus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Key,
  UserCheck,
  UserX,
  X,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '../lib/api'
import type { UserListItem, UserRole } from '../lib/types'

interface UserFormData {
  username: string
  email: string
  password: string
  full_name: string
  organization: string
  role: UserRole
  assigned_project_id: string
}

interface Project {
  id: string
  title: string
}

export default function Users() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  // State
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null)
  const [deletingUser, setDeletingUser] = useState<UserListItem | null>(null)
  const [resetPasswordUser, setResetPasswordUser] = useState<UserListItem | null>(null)
  const [newPassword, setNewPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    organization: '',
    role: 'schueler',
    assigned_project_id: '',
  })

  // Queries
  const { data: usersData, isLoading, error } = useQuery({
    queryKey: ['users', search, roleFilter, statusFilter],
    queryFn: () => api.getUsers({
      search: search || undefined,
      role: roleFilter || undefined,
      is_active: statusFilter === '' ? undefined : statusFilter === 'active',
      limit: 100,
    }),
  })

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: api.getProjects,
  })

  // Mutations
  const createUserMutation = useMutation({
    mutationFn: api.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowCreateDialog(false)
      resetForm()
    },
  })

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: Parameters<typeof api.updateUser>[1] }) =>
      api.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setEditingUser(null)
      resetForm()
    },
  })

  const deleteUserMutation = useMutation({
    mutationFn: api.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setDeletingUser(null)
    },
  })

  const toggleActiveMutation = useMutation({
    mutationFn: api.toggleUserActive,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: ({ userId, password }: { userId: string; password: string }) =>
      api.resetUserPassword(userId, password),
    onSuccess: () => {
      setResetPasswordUser(null)
      setNewPassword('')
    },
  })

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setActiveDropdown(null)
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      full_name: '',
      organization: '',
      role: 'schueler',
      assigned_project_id: '',
    })
  }

  const handleCreateUser = () => {
    createUserMutation.mutate({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name || undefined,
      organization: formData.organization || undefined,
      role: formData.role,
      assigned_project_id: formData.assigned_project_id || undefined,
    })
  }

  const handleUpdateUser = () => {
    if (!editingUser) return
    updateUserMutation.mutate({
      userId: editingUser.id,
      data: {
        email: formData.email || undefined,
        full_name: formData.full_name || undefined,
        organization: formData.organization || undefined,
        role: formData.role,
        assigned_project_id: formData.assigned_project_id || null,
      },
    })
  }

  const handleEditClick = (user: UserListItem) => {
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      full_name: user.full_name || '',
      organization: '',
      role: user.role,
      assigned_project_id: user.assigned_project_id || '',
    })
    setEditingUser(user)
    setActiveDropdown(null)
  }

  const getRoleBadgeClass = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300'
      case 'schueler':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      case 'extern':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getRoleLabel = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return t('users.roles.admin')
      case 'schueler':
        return t('users.roles.schueler')
      case 'extern':
        return t('users.roles.extern')
      default:
        return role
    }
  }

  const users = usersData?.users || []

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
              {t('users.title')}
            </h1>
            <p className="text-theme-text-muted">
              {t('users.subtitle')}
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            resetForm()
            setShowCreateDialog(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary/90 transition-colors"
        >
          <UserPlus className="w-5 h-5" />
          {t('users.createUser')}
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-theme-text-muted" />
          <input
            type="text"
            placeholder={t('users.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary placeholder-theme-text-muted focus:outline-none focus:ring-2 focus:ring-theme-primary"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
        >
          <option value="">{t('users.allRoles')}</option>
          <option value="admin">{t('users.roles.admin')}</option>
          <option value="schueler">{t('users.roles.schueler')}</option>
          <option value="extern">{t('users.roles.extern')}</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
        >
          <option value="">{t('users.allStatus')}</option>
          <option value="active">{t('users.statusActive')}</option>
          <option value="inactive">{t('users.statusInactive')}</option>
        </select>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-300">{t('users.loadError')}</span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-theme-primary"></div>
        </div>
      )}

      {/* Users Table */}
      {!isLoading && !error && (
        <div className="bg-theme-card rounded-xl border border-theme-border overflow-hidden">
          <table className="w-full">
            <thead className="bg-theme-hover">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                  {t('users.table.user')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                  {t('users.table.role')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                  {t('users.table.status')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                  {t('users.table.lastActive')}
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                  {t('users.table.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-theme-border">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-theme-text-muted">
                    {t('users.noUsers')}
                  </td>
                </tr>
              ) : (
                users.map((user: UserListItem) => (
                  <tr key={user.id} className="hover:bg-theme-hover transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-theme-primary/20 flex items-center justify-center">
                          <span className="text-theme-primary font-medium">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-theme-text-primary">{user.username}</div>
                          <div className="text-sm text-theme-text-muted">{user.email}</div>
                          {user.full_name && (
                            <div className="text-sm text-theme-text-muted">{user.full_name}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={clsx(
                        'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                        getRoleBadgeClass(user.role)
                      )}>
                        {getRoleLabel(user.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={clsx(
                        'inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full',
                        user.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      )}>
                        {user.is_active ? (
                          <CheckCircle className="w-3 h-3" />
                        ) : (
                          <X className="w-3 h-3" />
                        )}
                        {user.is_active ? t('users.active') : t('users.inactive')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-theme-text-muted">
                      {user.last_active_at
                        ? new Date(user.last_active_at).toLocaleDateString()
                        : t('users.never')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setActiveDropdown(activeDropdown === user.id ? null : user.id)
                          }}
                          className="p-2 hover:bg-theme-hover rounded-lg transition-colors"
                        >
                          <MoreVertical className="w-5 h-5 text-theme-text-muted" />
                        </button>
                        {activeDropdown === user.id && (
                          <div className="absolute right-0 mt-2 w-48 bg-theme-card border border-theme-border rounded-lg shadow-lg z-10">
                            <button
                              onClick={() => handleEditClick(user)}
                              className="flex items-center gap-2 w-full px-4 py-2 text-left text-theme-text-primary hover:bg-theme-hover"
                            >
                              <Edit className="w-4 h-4" />
                              {t('users.actions.edit')}
                            </button>
                            <button
                              onClick={() => {
                                setResetPasswordUser(user)
                                setActiveDropdown(null)
                              }}
                              className="flex items-center gap-2 w-full px-4 py-2 text-left text-theme-text-primary hover:bg-theme-hover"
                            >
                              <Key className="w-4 h-4" />
                              {t('users.actions.resetPassword')}
                            </button>
                            <button
                              onClick={() => {
                                toggleActiveMutation.mutate(user.id)
                                setActiveDropdown(null)
                              }}
                              className="flex items-center gap-2 w-full px-4 py-2 text-left text-theme-text-primary hover:bg-theme-hover"
                            >
                              {user.is_active ? (
                                <>
                                  <UserX className="w-4 h-4" />
                                  {t('users.actions.deactivate')}
                                </>
                              ) : (
                                <>
                                  <UserCheck className="w-4 h-4" />
                                  {t('users.actions.activate')}
                                </>
                              )}
                            </button>
                            <hr className="my-1 border-theme-border" />
                            <button
                              onClick={() => {
                                setDeletingUser(user)
                                setActiveDropdown(null)
                              }}
                              className="flex items-center gap-2 w-full px-4 py-2 text-left text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                            >
                              <Trash2 className="w-4 h-4" />
                              {t('users.actions.delete')}
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Dialog */}
      {showCreateDialog && (
        <Dialog
          title={t('users.createUser')}
          onClose={() => {
            setShowCreateDialog(false)
            resetForm()
          }}
          onConfirm={handleCreateUser}
          confirmText={t('users.create')}
          isLoading={createUserMutation.isPending}
          error={createUserMutation.error?.message}
        >
          <UserForm
            formData={formData}
            setFormData={setFormData}
            projects={projects as Project[] || []}
            showPasswordField
            t={t}
          />
        </Dialog>
      )}

      {/* Edit User Dialog */}
      {editingUser && (
        <Dialog
          title={t('users.editUser')}
          onClose={() => {
            setEditingUser(null)
            resetForm()
          }}
          onConfirm={handleUpdateUser}
          confirmText={t('users.save')}
          isLoading={updateUserMutation.isPending}
          error={updateUserMutation.error?.message}
        >
          <UserForm
            formData={formData}
            setFormData={setFormData}
            projects={projects as Project[] || []}
            showPasswordField={false}
            isEdit
            t={t}
          />
        </Dialog>
      )}

      {/* Delete Confirmation Dialog */}
      {deletingUser && (
        <Dialog
          title={t('users.deleteUser')}
          onClose={() => setDeletingUser(null)}
          onConfirm={() => deleteUserMutation.mutate(deletingUser.id)}
          confirmText={t('users.delete')}
          confirmVariant="danger"
          isLoading={deleteUserMutation.isPending}
          error={deleteUserMutation.error?.message}
        >
          <p className="text-theme-text-secondary">
            {t('users.deleteConfirmation', { username: deletingUser.username })}
          </p>
        </Dialog>
      )}

      {/* Reset Password Dialog */}
      {resetPasswordUser && (
        <Dialog
          title={t('users.resetPassword')}
          onClose={() => {
            setResetPasswordUser(null)
            setNewPassword('')
          }}
          onConfirm={() => resetPasswordMutation.mutate({
            userId: resetPasswordUser.id,
            password: newPassword,
          })}
          confirmText={t('users.resetPasswordConfirm')}
          isLoading={resetPasswordMutation.isPending}
          error={resetPasswordMutation.error?.message}
          disabled={newPassword.length < 6}
        >
          <div className="space-y-4">
            <p className="text-theme-text-secondary">
              {t('users.resetPasswordDescription', { username: resetPasswordUser.username })}
            </p>
            <div>
              <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                {t('users.newPassword')}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2 pr-10 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
                  placeholder={t('users.newPasswordPlaceholder')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-theme-text-muted hover:text-theme-text-primary"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {newPassword.length > 0 && newPassword.length < 6 && (
                <p className="mt-1 text-sm text-red-500">{t('users.passwordTooShort')}</p>
              )}
            </div>
          </div>
        </Dialog>
      )}
    </div>
  )
}

// Dialog Component
function Dialog({
  title,
  children,
  onClose,
  onConfirm,
  confirmText,
  confirmVariant = 'primary',
  isLoading,
  error,
  disabled,
}: {
  title: string
  children: React.ReactNode
  onClose: () => void
  onConfirm: () => void
  confirmText: string
  confirmVariant?: 'primary' | 'danger'
  isLoading?: boolean
  error?: string
  disabled?: boolean
}) {
  const { t } = useTranslation()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-theme-card rounded-xl shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-theme-border">
          <h2 className="text-lg font-semibold text-theme-text-primary">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-theme-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-theme-text-muted" />
          </button>
        </div>
        <div className="p-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
            </div>
          )}
          {children}
        </div>
        <div className="flex justify-end gap-3 p-4 border-t border-theme-border">
          <button
            onClick={onClose}
            className="px-4 py-2 text-theme-text-secondary hover:bg-theme-hover rounded-lg transition-colors"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading || disabled}
            className={clsx(
              'px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
              confirmVariant === 'danger'
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-theme-primary text-white hover:bg-theme-primary/90'
            )}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                {t('common.loading')}
              </span>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// User Form Component
function UserForm({
  formData,
  setFormData,
  projects,
  showPasswordField,
  isEdit,
  t,
}: {
  formData: UserFormData
  setFormData: (data: UserFormData) => void
  projects: Project[]
  showPasswordField: boolean
  isEdit?: boolean
  t: (key: string) => string
}) {
  const [passwordVisible, setPasswordVisible] = useState(false)

  return (
    <div className="space-y-4">
      {!isEdit && (
        <div>
          <label className="block text-sm font-medium text-theme-text-secondary mb-1">
            {t('users.form.username')} *
          </label>
          <input
            type="text"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            className="w-full px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
            placeholder={t('users.form.usernamePlaceholder')}
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-theme-text-secondary mb-1">
          {t('users.form.email')} *
        </label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="w-full px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
          placeholder={t('users.form.emailPlaceholder')}
        />
      </div>

      {showPasswordField && (
        <div>
          <label className="block text-sm font-medium text-theme-text-secondary mb-1">
            {t('users.form.password')} *
          </label>
          <div className="relative">
            <input
              type={passwordVisible ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 pr-10 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
              placeholder={t('users.form.passwordPlaceholder')}
            />
            <button
              type="button"
              onClick={() => setPasswordVisible(!passwordVisible)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-theme-text-muted hover:text-theme-text-primary"
            >
              {passwordVisible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-theme-text-secondary mb-1">
          {t('users.form.fullName')}
        </label>
        <input
          type="text"
          value={formData.full_name}
          onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
          className="w-full px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
          placeholder={t('users.form.fullNamePlaceholder')}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-theme-text-secondary mb-1">
          {t('users.form.organization')}
        </label>
        <input
          type="text"
          value={formData.organization}
          onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
          className="w-full px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
          placeholder={t('users.form.organizationPlaceholder')}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-theme-text-secondary mb-1">
          {t('users.form.role')} *
        </label>
        <select
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
          className="w-full px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
        >
          <option value="schueler">{t('users.roles.schueler')}</option>
          <option value="admin">{t('users.roles.admin')}</option>
          <option value="extern">{t('users.roles.extern')}</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-theme-text-secondary mb-1">
          {t('users.form.assignedProject')}
        </label>
        <select
          value={formData.assigned_project_id}
          onChange={(e) => setFormData({ ...formData, assigned_project_id: e.target.value })}
          className="w-full px-4 py-2 bg-theme-card border border-theme-border rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
        >
          <option value="">{t('users.form.noProject')}</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.title}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
