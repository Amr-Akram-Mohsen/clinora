/**
 * test/RegisterPage.test.tsx — RegisterPage component tests.
 */

import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { RegisterPage } from "@/features/auth/RegisterPage";

vi.mock("@/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    register: vi.fn(),
    isAuthenticated: false,
    isLoading: false,
  }),
}));

describe("RegisterPage", () => {
  it("renders form fields for user registration", () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Clinic \/ Practice Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Clinical Role/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Create Account & Enter Workspace/i })
    ).toBeInTheDocument();
  });

  it("contains a link to the sign-in page", () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const loginLink = screen.getByRole("link", { name: /Sign in here/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute("href", "/login");
  });
});
