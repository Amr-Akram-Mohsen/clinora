/**
 * features/patients/PatientListPage.tsx
 *
 * Patient Directory view: search, paginated table, and registration modal trigger.
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchPatients } from "@/api/clinical";
import { Button } from "@/components/Button/Button";
import { Badge } from "@/components/Badge/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States/States";
import { RegisterPatientModal } from "./RegisterPatientModal";
import type { PatientListItem } from "@/types/clinical";
import "./PatientListPage.css";

export function PatientListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const queryParam = searchParams.get("q") || "";
  const pageParam = parseInt(searchParams.get("page") || "1", 10);

  const [searchQuery, setSearchQuery] = useState(queryParam);
  const [patients, setPatients] = useState<PatientListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(pageParam);
  const pageSize = 20;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    loadPatients();
  }, [queryParam, page]);

  async function loadPatients() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchPatients({
        q: queryParam || undefined,
        page,
        pageSize,
      });
      setPatients(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err?.message || "Failed to load patients.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearchParams(searchQuery ? { q: searchQuery, page: "1" } : {});
  }

  return (
    <div className="patient-list">
      <div className="patient-list__header">
        <div className="patient-list__title-group">
          <h1>Patients Directory</h1>
          <p>Search, manage records, and register new patients.</p>
        </div>
        <Button variant="primary" onClick={() => setIsModalOpen(true)}>
          + Register Patient
        </Button>
      </div>

      <div className="patient-list__controls">
        <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "var(--spacing-2)", flex: 1 }}>
          <input
            type="search"
            className="patient-list__search-input"
            placeholder="Search by name, phone, or national ID…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Button variant="secondary" type="submit">
            Search
          </Button>
        </form>
        <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)" }}>
          Total: {total} patients
        </span>
      </div>

      {isLoading ? (
        <LoadingState message="Loading patient records…" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadPatients} />
      ) : patients.length === 0 ? (
        <EmptyState
          title="No patients found"
          message={
            queryParam
              ? `No matching records for "${queryParam}".`
              : "No patients registered in the clinic yet."
          }
          action={
            <Button variant="primary" onClick={() => setIsModalOpen(true)}>
              Register First Patient
            </Button>
          }
        />
      ) : (
        <div className="patient-list__table-container">
          <table className="patient-list__table">
            <thead>
              <tr>
                <th>Patient Name</th>
                <th>Biological Sex</th>
                <th>Date of Birth</th>
                <th>Phone</th>
                <th>National ID</th>
                <th>Blood Type</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr
                  key={p.id}
                  className="patient-list__row"
                  onClick={() => navigate(`/patients/${p.id}`)}
                >
                  <td className="patient-list__patient-name">{p.full_name}</td>
                  <td>{p.gender}</td>
                  <td>{p.date_of_birth}</td>
                  <td>{p.phone}</td>
                  <td>{p.national_id || "—"}</td>
                  <td>
                    {p.blood_type ? (
                      <Badge variant="info">{p.blood_type}</Badge>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {total > pageSize && (
            <div className="patient-list__pagination">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              >
                Previous
              </Button>
              <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)" }}>
                Page {page} of {Math.ceil(total / pageSize)}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page * pageSize >= total}
                onClick={() => setPage((prev) => prev + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </div>
      )}

      <RegisterPatientModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadPatients}
      />
    </div>
  );
}
