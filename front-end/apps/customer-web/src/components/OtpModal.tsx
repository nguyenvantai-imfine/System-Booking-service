"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldCheck,
  X,
  Mail,
  Clock,
  RefreshCw,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

interface OtpModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  txnCode: string;
  bookingCode: string;
  onVerify: (otpCode: string) => Promise<void>;
  onResend: () => Promise<void>;
  isVerifying: boolean;
  isResending: boolean;
  errorMessage?: string;
  clearError?: () => void;
}

export function maskEmail(email: string): string {
  if (!email || !email.includes("@")) return email;
  const [localPart, domain] = email.split("@");
  if (localPart.length <= 2) {
    return `${localPart[0]}***@${domain}`;
  }
  const prefix = localPart.slice(0, 2);
  return `${prefix}***@${domain}`;
}

export function OtpModal({
  isOpen,
  onClose,
  email,
  txnCode,
  bookingCode,
  onVerify,
  onResend,
  isVerifying,
  isResending,
  errorMessage,
  clearError,
}: OtpModalProps) {
  const [otp, setOtp] = useState<string[]>(["", "", "", "", "", ""]);
  const [countdown, setCountdown] = useState<number>(180);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Reset inputs and timer whenever modal is opened
  useEffect(() => {
    if (isOpen) {
      setOtp(["", "", "", "", "", ""]);
      setCountdown(180);
      if (clearError) clearError();
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    }
  }, [isOpen]);

  // Countdown timer: 180 seconds
  useEffect(() => {
    if (!isOpen) return;
    if (countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen, countdown]);

  // Keyboard accessibility: ESC closes modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isVerifying) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isVerifying, onClose]);

  if (!isOpen) return null;

  const formatCountdown = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handleChange = (index: number, value: string) => {
    if (isVerifying || countdown === 0) return;
    if (clearError) clearError();

    const digits = value.replace(/\D/g, "");
    if (!digits) {
      const nextOtp = [...otp];
      nextOtp[index] = "";
      setOtp(nextOtp);
      return;
    }

    const lastDigit = digits.slice(-1);
    const nextOtp = [...otp];
    nextOtp[index] = lastDigit;
    setOtp(nextOtp);

    // Auto-focus next input
    if (index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-verify when 6 digits are complete
    const fullCode = nextOtp.join("");
    if (fullCode.length === 6 && !nextOtp.includes("")) {
      onVerify(fullCode);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (otp[index] === "" && index > 0) {
        e.preventDefault();
        const nextOtp = [...otp];
        nextOtp[index - 1] = "";
        setOtp(nextOtp);
        inputRefs.current[index - 1]?.focus();
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      e.preventDefault();
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < 5) {
      e.preventDefault();
      inputRefs.current[index + 1]?.focus();
    } else if (e.key === "Enter") {
      const fullCode = otp.join("");
      if (fullCode.length === 6 && !isVerifying && countdown > 0) {
        e.preventDefault();
        onVerify(fullCode);
      }
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (isVerifying || countdown === 0) return;
    if (clearError) clearError();

    const pastedData = e.clipboardData.getData("text");
    const digits = pastedData.replace(/\D/g, "").slice(0, 6);
    if (!digits) return;

    const nextOtp = [...otp];
    for (let i = 0; i < 6; i++) {
      nextOtp[i] = digits[i] || "";
    }
    setOtp(nextOtp);

    const focusIndex = Math.min(digits.length, 5);
    inputRefs.current[focusIndex]?.focus();

    if (digits.length === 6) {
      onVerify(digits);
    }
  };

  const handleResendClick = async () => {
    if (isResending) return;
    try {
      await onResend();
      setOtp(["", "", "", "", "", ""]);
      setCountdown(180);
      if (clearError) clearError();
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    } catch {
      // Error handled by parent via errorMessage prop
    }
  };

  const isComplete = otp.every((d) => d !== "");

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-200"
      onClick={() => {
        if (!isVerifying) onClose();
      }}
    >
      <div
        className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden p-6 sm:p-8 transform transition-all animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          disabled={isVerifying}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-700 rounded-full hover:bg-slate-100 transition-colors disabled:opacity-40"
          aria-label="Đóng"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Icon & Title */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto shadow-xs">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Xác thực thanh toán OTP
          </h3>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Để bảo mật giao dịch đặt phòng, mã xác thực 6 chữ số đã được gửi đến:
          </p>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50/70 border border-indigo-100 text-indigo-700 font-semibold text-xs mt-1">
            <Mail className="w-3.5 h-3.5 shrink-0" />
            <span className="font-mono">{maskEmail(email)}</span>
          </div>
        </div>

        {/* 6-Digit OTP Inputs */}
        <div className="my-6">
          <div className="grid grid-cols-6 gap-2 sm:gap-2.5" onPaste={handlePaste}>
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => {
                  inputRefs.current[index] = el;
                }}
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={1}
                value={digit}
                disabled={isVerifying || countdown === 0}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onFocus={(e) => e.target.select()}
                className={`w-full h-13 sm:h-15 text-center text-xl sm:text-2xl font-black font-mono rounded-2xl border-2 transition-all outline-none ${
                  errorMessage
                    ? "border-rose-300 bg-rose-50/30 text-rose-900 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/15"
                    : "border-slate-200 bg-slate-50/60 text-slate-900 focus:border-indigo-600 focus:bg-white focus:ring-4 focus:ring-indigo-500/15"
                } ${
                  isVerifying || countdown === 0
                    ? "opacity-50 cursor-not-allowed bg-slate-100"
                    : ""
                }`}
                autoComplete="one-time-code"
              />
            ))}
          </div>
        </div>

        {/* Error Alert inside Modal */}
        {errorMessage && (
          <div className="mb-4 flex items-start gap-2.5 p-3 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold animate-in fade-in duration-150">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="flex-1 leading-relaxed">{errorMessage}</span>
          </div>
        )}

        {/* Countdown & Resend Section */}
        <div className="space-y-3 pt-1">
          {countdown > 0 ? (
            <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Mã có hiệu lực trong:</span>
              <span className="font-mono font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-md">
                {formatCountdown(countdown)}
              </span>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-center text-xs text-rose-600 font-semibold">
                Mã xác thực OTP đã hết hạn (180 giây).
              </p>
              <button
                type="button"
                onClick={handleResendClick}
                disabled={isResending}
                className="w-full py-2.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition-all flex items-center justify-center gap-2 border border-indigo-200/80 disabled:opacity-60"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${isResending ? "animate-spin" : ""}`}
                />
                <span>
                  {isResending ? "Đang gửi lại mã mới..." : "Gửi lại mã OTP"}
                </span>
              </button>
            </div>
          )}

          {/* Confirm Button */}
          <button
            type="button"
            disabled={!isComplete || isVerifying || countdown === 0}
            onClick={() => onVerify(otp.join(""))}
            className="w-full py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-sm shadow-lg shadow-indigo-600/30 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
          >
            {isVerifying ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Đang xác thực OTP & xuất vé...</span>
              </>
            ) : (
              <>
                <span>Xác nhận giao dịch</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          {/* Transaction Metadata Footer */}
          <div className="pt-2 text-center">
            <p className="text-[11px] text-slate-400 font-mono">
              Mã giao dịch: {txnCode ? txnCode.slice(-12) : "..."} • Đơn: {bookingCode}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
