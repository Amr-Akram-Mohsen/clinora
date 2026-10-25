import { apiClient } from './client'; // Adjust to your project's axios client
import { StaffUser, OrganizationProfile, AuditLogItem } from '../types/admin';

export const adminApi = {
    getStaff: (params?: { skip?: number; limit?: number; search?: string; role?: string }) =>
        apiClient.get<{ total: number; items: StaffUser[] }>('/api/v1/admin/staff', { params }),

    inviteStaff: (data: { email: string; full_name: string; role: string }) =>
        apiClient.post('/api/v1/admin/staff/invite', data),

    updateStaffRole: (userId: string, role: string) =>
        apiClient.patch(`/api/v1/admin/staff/${userId}/role`, { role }),

    toggleStaffStatus: (userId: string, is_active: boolean) =>
        apiClient.patch(`/api/v1/admin/staff/${userId}/status`, { is_active }),

    getOrganization: () =>
        apiClient.get<OrganizationProfile>('/api/v1/admin/organization'),

    updateOrganization: (data: Partial<OrganizationProfile>) =>
        apiClient.put<OrganizationProfile>('/api/v1/admin/organization', data),

    getAuditLogs: (params?: Record<string, any>) =>
        apiClient.get<{ total: number; items: AuditLogItem[] }>('/api/v1/admin/audit-logs', { params }),
};