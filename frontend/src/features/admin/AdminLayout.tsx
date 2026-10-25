import { NavLink, Outlet } from "react-router-dom";
import "./AdminPages.css";

export function AdminLayout() {
    return (
        <div className="admin-layout">
            <div className="admin-layout__header">
                <h1>Clinic Administration</h1>
                <p>Manage staff members, clinic profile settings, and system audit trails.</p>
            </div>

            <nav className="admin-layout__tabs">
                <NavLink
                    to="/admin/staff"
                    className={({ isActive }) =>
                        `admin-layout__tab ${isActive ? "admin-layout__tab--active" : ""}`
                    }
                >
                    Staff Directory
                </NavLink>
                <NavLink
                    to="/admin/settings"
                    className={({ isActive }) =>
                        `admin-layout__tab ${isActive ? "admin-layout__tab--active" : ""}`
                    }
                >
                    Clinic Settings
                </NavLink>
                <NavLink
                    to="/admin/audit"
                    className={({ isActive }) =>
                        `admin-layout__tab ${isActive ? "admin-layout__tab--active" : ""}`
                    }
                >
                    Audit Trail
                </NavLink>
            </nav>

            <div className="admin-layout__content">
                <Outlet />
            </div>
        </div>
    );
}