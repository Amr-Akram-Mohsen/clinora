import { useEffect, useState } from "react";
import { adminApi } from "@/api/admin";
import { Badge } from "@/components/Badge/Badge";
import { LoadingState, ErrorState, EmptyState } from "@/components/States/States";
import type { AuditLogItem } from "@/types/admin";
import "./AdminPages.css";

export function AuditLogViewerPage() {
    const [logs, setLogs] = useState<AuditLogItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionFilter, setActionFilter] = useState("");
    const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);

    useEffect(() => {
        loadLogs();
    }, [actionFilter]);

    async function loadLogs() {
        setIsLoading(true);
        setError(null);
        try {
            const res = await adminApi.getAuditLogs({
                action: actionFilter || undefined,
            });
            setLogs(res.data.items);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load audit logs.");
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="audit-log-viewer">
            <div className="staff-management__toolbar">
                <input
                    type="text"
                    className="staff-management__input"
                    placeholder="Filter by action (e.g. organization.update)…"
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                />
            </div>

            {isLoading ? (
                <LoadingState message="Loading immutable audit trail…" />
            ) : error ? (
                <ErrorState message={error} onRetry={loadLogs} />
            ) : logs.length === 0 ? (
                <EmptyState title="No audit events" message="No matching audit log entries found." />
            ) : (
                <div className="admin-table-container">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Action</th>
                                <th>Outcome</th>
                                <th>Actor Email</th>
                                <th>IP Address</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log) => (
                                <tr key={log.id} onClick={() => setSelectedLog(log)} style={{ cursor: "pointer" }}>
                                    <td>{new Date(log.created_at).toLocaleString()}</td>
                                    <td><code>{log.action}</code></td>
                                    <td>
                                        <Badge variant={log.outcome === "success" ? "success" : "error"}>
                                            {log.outcome}
                                        </Badge>
                                    </td>
                                    <td>{log.actor_email || "System"}</td>
                                    <td>{log.ip_address || "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {selectedLog && (
                <div className="admin-modal-overlay" onClick={() => setSelectedLog(null)}>
                    <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
                        <h2>Audit Event Details</h2>
                        <div className="audit-details">
                            <p><strong>Action:</strong> <code>{selectedLog.action}</code></p>
                            <p><strong>Outcome:</strong> {selectedLog.outcome}</p>
                            <p><strong>Actor:</strong> {selectedLog.actor_email}</p>
                            <p><strong>IP Address:</strong> {selectedLog.ip_address || "—"}</p>
                            <p><strong>User Agent:</strong> {selectedLog.user_agent || "—"}</p>
                            <p><strong>Request ID:</strong> {selectedLog.request_id || "—"}</p>
                            <p><strong>Timestamp:</strong> {new Date(selectedLog.created_at).toLocaleString()}</p>
                            {selectedLog.metadata && (
                                <div>
                                    <strong>Metadata:</strong>
                                    <pre className="audit-pre">{JSON.stringify(selectedLog.metadata, null, 2)}</pre>
                                </div>
                            )}
                        </div>
                        <div className="admin-modal__actions">
                            <button className="admin-btn-secondary" onClick={() => setSelectedLog(null)}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}