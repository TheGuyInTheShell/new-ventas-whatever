export interface ViewPermissionDefinition {
  name: string
  action: string
  description: string
  type: string
  meta?: Record<string, any>
}

export const viewPermissions: ViewPermissionDefinition[] = [
  {
    name: 'CREATE_USER',
    action: 'POST',
    description: 'Create new users',
    type: 'UI',
    meta: { label: 'Create User' }
  },
  {
    name: 'EDIT_USER',
    action: 'PUT',
    description: 'Edit existing users',
    type: 'UI',
    meta: { label: 'Edit User' }
  },
  {
    name: 'DELETE_USER',
    action: 'DELETE',
    description: 'Delete users',
    type: 'UI',
    meta: { label: 'Delete User' }
  }
]

export const useViewAuth = () => {
  return {
    viewPermissions
  }
}
