import { useEffect, useState } from "react";
import { adminApi } from "@/api/admin";
import { Button } from "@/components/Button/Button";
import { Badge } from "@/components/Badge/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States/States";
import type { StaffUser } from "@/types/admin";
import "./AdminPages.css";

export function StaffManagementPage() {
    const [staffList, setStaffList] = useState<StaffUser[]>([]);
    const [total, setTotal] = useState(0);
    const [search, setSearch] = useState("");
    const [roleFilter, setRoleFilter] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Invite modal state
    const [isInviteOpen, setIsInviteOpen] = useState(false);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteName, setInviteName] = useState("");
    const [inviteRole, setInviteRole] = useState("DOCTOR");
    const [inviteSubmitting, setInviteSubmitting] = useState(false);

    useEffect(() => {
        loadStaff();
    }, [search, roleFilter]);

    async function loadStaff() {
        setIsLoading(true);
        setError(null);
        try {
            const res = await adminApi.getStaff({
                search: search || undefined,
                role: roleFilter || undefined,
            });
            setStaffList(res.data.items);
            setTotal(res.data.total);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load staff list.");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleInvite(e: React.FormEvent) {
        e.preventDefault();
        setInviteSubmitting(true);
        try {
            await adminApi.inviteStaff({
                email: inviteEmail,
                full_name: inviteName,
                role: inviteRole,
            });
            setIsInviteOpen(false);
            setInviteEmail("");
            setInviteName("");
            loadStaff();
        } catch (err: any) {
            alert(err?.response?.data?.detail || "Failed to invite staff member.");
        } finally {
            setInviteSubmitting(false);
        }
    }

    async function handleStatusToggle(userId: string, currentStatus: boolean) {
        try {
            await adminApi.toggleStaffStatus(userId, !currentStatus);
            loadStaff();
        } catch (err: any) {
            alert(err?.response?.data?.detail || "Failed to update status.");
        }
    }

    async function handleRoleChange(userId: string, newRole: string) {
        try {
            await adminApi.updateStaffRole(userId, newRole);
            loadStaff();
        } catch (err: any) {
            alert(err?.response?.data?.detail || "Failed to update role.");
        }
    }

    return (
        <div className="staff-management">
            <div className="staff-management__toolbar">
                <form onSubmit={(e) => { e.preventDefault(); loadStaff(); }} className="staff-management__search-form">
                    <input
                        type="search"
                        className="staff-management__input"
                        placeholder="Search by name or email…"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    <select
                        className="staff-management__select"
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                    >
                        <option value="">All Roles</option>
                        <option value="ADMIN">Admin</option>
                        <option value="DOCTOR">Doctor</option>
                        <option value="NURSE">Nurse</option>
                        <option value="RECEPTIONIST">Receptionist</option>
                    </select>
                </form>
                <Button variant="primary" onClick={() => setIsInviteOpen(true)}>
                    + Invite Staff Member
                </Button>
            </div>

            {isLoading ? (
                <LoadingState message="Loading staff directory…" />
            ) : error ? (
                <ErrorState message={error} onRetry={loadStaff} />
            ) : staffList.length === 0 ? (
                <EmptyState title="No staff found" message="No practitioners or staff members match your criteria." />
            ) : (
                <div className="admin-table-container">
                    <table className="admin-table">
                        <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)" }}>
                            Total: {total} staff members
                        </span>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {staffList.map((user) => (
                                <tr key={user.id}>
                                    <td className="admin-table__name">{user.full_name}</td>
                                    <td>{user.email}</td>
                                    <td>
                                        <select
                                            value={user.roles[0] || "STAFF"}
                                            onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                            className="admin-table__role-select"
                                        >
                                            <option value="ADMIN">ADMIN</option>
                                            <option value="DOCTOR">DOCTOR</option>
                                            <option value="NURSE">NURSE</option>
                                            <option value="RECEPTIONIST">RECEPTIONIST</option>
                                        </select>
                                    </td>
                                    <td>
                                        <Badge variant={user.is_active ? "success" : "warning"}>
                                            {user.is_active ? "Active" : "Inactive"}
                                        </Badge>
                                    </td>
                                    <td>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => handleStatusToggle(user.id, user.is_active)}
                                        >
                                            {user.is_active ? "Deactivate" : "Reactivate"}
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Invite Modal */}
            {isInviteOpen && (
                <div className="admin-modal-overlay">
                    <div className="admin-modal">
                        <h2>Invite Staff Member</h2>
                        <form onSubmit={handleInvite} className="admin-modal__form">
                            <div className="admin-form-group">
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    required
                                    value={inviteName}
                                    onChange={(e) => setInviteName(e.target.value)}
                                    placeholder="Dr. Jane Doe"
                                />
                            </div>
                            <div className="admin-form-group">
                                <label>Email Address</label>
                                <input
                                    type="email"
                                    required
                                    value={inviteEmail}
                                    onChange={(e) => setInviteEmail(e.target.value)}
                                    placeholder="jane.doe@clinora.com"
                                />
                            </div>
                            <div className="admin-form-group">
                                <label>Role</label>
                                <select
                                    value={inviteRole}
                                    onChange={(e) => setInviteRole(e.target.value)}
                                >
                                    <option value="ADMIN">ADMIN</option>
                                    <option value="DOCTOR">DOCTOR</option>
                                    <option value="NURSE">NURSE</option>
                                    <option value="RECEPTIONIST">RECEPTIONIST</option>
                                </select>
                            </div>
                            <div className="admin-modal__actions">
                                <Button variant="secondary" type="button" onClick={() => setIsInviteOpen(false)}>
                                    Cancel
                                </Button>
                                <Button variant="primary" type="submit" disabled={inviteSubmitting}>
                                    {inviteSubmitting ? "Sending..." : "Send Invitation"}
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}