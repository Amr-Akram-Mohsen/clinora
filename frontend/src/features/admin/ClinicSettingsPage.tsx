import { useEffect, useState } from "react";
import { adminApi } from "@/api/admin";
import { Button } from "@/components/Button/Button";
import { LoadingState, ErrorState } from "@/components/States/States";
import type { OrganizationProfile } from "@/types/admin";
import "./AdminPages.css";

export function ClinicSettingsPage() {
    const [profile, setProfile] = useState<OrganizationProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    useEffect(() => {
        loadSettings();
    }, []);

    async function loadSettings() {
        setIsLoading(true);
        setError(null);
        try {
            const res = await adminApi.getOrganization();
            setProfile(res.data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load clinic settings.");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        if (!profile) return;
        setIsSaving(true);
        setSuccessMessage(null);
        setError(null);
        try {
            const res = await adminApi.updateOrganization({
                name: profile.name,
                contact_phone: profile.contact_phone,
                contact_email: profile.contact_email,
                address: profile.address,
            });
            setProfile(res.data);
            setSuccessMessage("Clinic settings updated successfully.");
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to save settings.");
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <LoadingState message="Loading clinic profile…" />;
    if (error && !profile) return <ErrorState message={error} onRetry={loadSettings} />;

    return (
        <div className="clinic-settings">
            <form onSubmit={handleSave} className="clinic-settings__form">
                <h2>Organization Profile</h2>
                <p>Update your clinic contact info and physical location.</p>

                {successMessage && <div className="admin-alert admin-alert--success">{successMessage}</div>}
                {error && <div className="admin-alert admin-alert--error">{error}</div>}

                <div className="admin-form-group">
                    <label>Clinic Name</label>
                    <input
                        type="text"
                        required
                        value={profile?.name || ""}
                        onChange={(e) => setProfile({ ...profile!, name: e.target.value })}
                    />
                </div>

                <div className="admin-form-group">
                    <label>Contact Phone</label>
                    <input
                        type="text"
                        value={profile?.contact_phone || ""}
                        onChange={(e) => setProfile({ ...profile!, contact_phone: e.target.value })}
                    />
                </div>

                <div className="admin-form-group">
                    <label>Contact Email</label>
                    <input
                        type="email"
                        value={profile?.contact_email || ""}
                        onChange={(e) => setProfile({ ...profile!, contact_email: e.target.value })}
                    />
                </div>

                <div className="admin-form-group">
                    <label>Physical Address</label>
                    <textarea
                        rows={3}
                        value={profile?.address || ""}
                        onChange={(e) => setProfile({ ...profile!, address: e.target.value })}
                    />
                </div>

                <Button variant="primary" type="submit" disabled={isSaving}>
                    {isSaving ? "Saving Changes…" : "Save Changes"}
                </Button>
            </form>
        </div>
    );
}