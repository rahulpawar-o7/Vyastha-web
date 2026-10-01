import { useEffect, useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import "./VerifyEmailPage.css";

const API_URL =
  process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState(
    "Your email is being verified..."
  );

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setMessage("Verification token is missing.");
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/auth/verify-email?token=${encodeURIComponent(
            token
          )}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Email verification failed."
          );
        }

        setStatus("success");
        setMessage(
          "Your email has been verified successfully."
        );

        toast.success("Email verified successfully.");

        setTimeout(() => {
          navigate("/login");
        }, 2000);
      } catch (error) {
        console.error("Email verification error:", error);

        setStatus("error");
        setMessage(
          error.message || "Unable to verify your email."
        );
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  return (
    <div className="verify-email-page">
      <div className="verify-email-card">
        {status === "loading" && (
          <>
            <Loader2
              className="verify-email-icon loading-icon"
              size={52}
            />

            <h1>Verifying your email</h1>

            <p>{message}</p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle2
              className="verify-email-icon success-icon"
              size={52}
            />

            <h1>Email verified!</h1>

            <p>{message}</p>

            <p className="redirect-message">
              Redirecting you to login...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <AlertCircle
              className="verify-email-icon error-icon"
              size={52}
            />

            <h1>Verification failed</h1>

            <p>{message}</p>

            <Link
              to="/login"
              className="verify-email-login-button"
            >
              Go to Login
            </Link>
          </>
        )}
      </div>
    </div>
  );
}