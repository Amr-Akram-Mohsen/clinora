export interface StaffUser {
    id: string;
    email: string;
    full_name: string;
    roles: string[];
    is_active: boolean;
    created_at: string;
}

export interface OrganizationProfile {
    id: string;
    name: string;
    contact_phone?: string;
    contact_email?: string;
    address?: string;
    operating_schedule?: Record<string, any>;
}

export interface AuditLogItem {
    id: string;
    action: string;
    outcome: string;
    actor_email?: string;
    ip_address?: string;
    user_agent?: string;
    request_id?: string;
    metadata?: Record<string, any>;
    created_at: string;
}